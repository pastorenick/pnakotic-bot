# Deployment Guide: Vector Similarity Search

## What Changed

This update adds semantic vector-based similarity search to the bot using pre-computed embeddings.

### New Features
- **Vector similarity search** using pre-generated embeddings
- **Pre-generated embeddings** (9.3 MB) included in repository
- **Automatic fallback** to keyword search if embeddings unavailable
- **Better card recommendations** based on semantic understanding
- **Production optimized** - no ML model loading in production

### Files Modified
- `bot/replacement_finder.py` - Added vector similarity scoring
- `requirements.txt` - Removed sentence-transformers (dev-only now)
- `fly.toml` - Increased memory to 512MB
- `.gitignore` - Allow embeddings.json to be committed
- `main.py` - Added startup initialization

### New Files
- `bot/generate_embeddings.py` - Script to regenerate embeddings (local only)
- `bot/startup.py` - Startup checks for embeddings
- `data/cache/embeddings.json` - Pre-generated embeddings (9.3 MB)
- `requirements-dev.txt` - Development dependencies (sentence-transformers)
- `update_embeddings.sh` - Helper script for updating embeddings
- `EMBEDDINGS.md` - Documentation

## Key Architecture Decisions

### Why Pre-generated Embeddings?

1. **Memory efficiency**: sentence-transformers model = ~200MB, embeddings only = ~10MB
2. **Fast startup**: No model loading time
3. **Works on 512MB RAM**: Fly.io free tier compatible
4. **Deterministic**: Same embeddings every deployment

### Production vs Development

**Production (Fly.io):**
- Only installs `requirements.txt` (no sentence-transformers)
- Loads pre-generated embeddings from `data/cache/embeddings.json`
- Uses numpy for cosine similarity calculations
- Low memory footprint

**Development (Local):**
- Installs `requirements-dev.txt` (includes sentence-transformers)
- Can generate new embeddings when cards are added
- Commits updated embeddings to git

## Deployment Steps

### Step 1: Verify Changes
```bash
git status
git diff fly.toml requirements.txt
```

You should see:
- `fly.toml`: Memory increased to 512MB
- `requirements.txt`: sentence-transformers removed
- New file: `requirements-dev.txt`

### Step 2: Commit and Push
```bash
git add .
git commit -m "Add vector similarity search with pre-generated embeddings"
git push origin main
```

### Step 3: Deploy to Fly.io
```bash
fly deploy
```

### Step 4: Verify Deployment
Check logs to ensure embeddings are loaded:
```bash
fly logs
```

You should see:
```
✅ Embeddings cache found (9.3 MB)
PnakoticBot initialized successfully!
```

If you see errors like `PR04 could not find a good candidate`, check memory usage:
```bash
fly scale memory 512
```

## Memory Considerations

### Before (with sentence-transformers):
- Base Python + libs: ~100MB
- sentence-transformers model: ~200MB
- **Total: ~300MB** ❌ Too much for 256MB

### After (pre-generated embeddings):
- Base Python + libs: ~100MB
- numpy + embeddings: ~20MB
- Flask + Telegram bot: ~50MB
- **Total: ~170MB** ✅ Fits in 512MB comfortably

## Updating Embeddings

When new cards are released:

### Method 1: Using the script (recommended)
```bash
./update_embeddings.sh
```

### Method 2: Manual
```bash
# Make sure dev dependencies are installed
pip install -r requirements-dev.txt

# Generate new embeddings
python -m bot.generate_embeddings

# Commit
git add data/cache/embeddings.json
git commit -m "Update embeddings for new card set"
git push
```

## Troubleshooting

### "PR04 could not find a good candidate" error

This means the app is crashing on startup, usually due to memory issues.

**Solutions:**
1. Check if sentence-transformers is in requirements.txt (should NOT be there)
2. Verify memory is set to 512MB in fly.toml
3. Check logs: `fly logs`
4. Increase memory if needed: `fly scale memory 512`

### "Embeddings cache not found" warning

The bot will work fine with keyword search, but to enable vector search:
1. Make sure `data/cache/embeddings.json` is committed to git
2. Check .gitignore doesn't exclude it
3. Verify file size: `ls -lh data/cache/embeddings.json` should show ~9MB

### High memory usage

If memory usage is still high:
1. Check `fly logs` for memory stats
2. Consider reducing gunicorn workers in Dockerfile (currently 2)
3. Monitor with: `fly status`

## Fallback Behavior

If embeddings are missing or fail to load:
- Bot automatically falls back to keyword-based similarity search
- No degradation in functionality, just less semantic understanding
- Logs will show: "Bot will use keyword-based similarity search"

## Testing

Test the deployment with these commands in Telegram:

```
/replace Apprentice Wizard
```
Should find: Sisters of Avalon (95% match - also draws spells)

```
/replace Unland Angler  
```
Should find: Giant Shark, Sea Serpent (water creatures with movement abilities)

```
/replace Nelly Longarms
```
Should find: Cards with control/drag mechanics

Compare results with the old keyword-based search - should see more semantically similar cards!

## Performance Metrics

- **Embedding generation**: ~2 seconds for 1,104 cards (local only)
- **Search time**: ~0.1-0.5s (same as before)
- **Startup time**: ~2-3s (no model loading)
- **Memory usage**: ~150-200MB (down from ~300MB+)
- **Storage**: 9.3 MB for embeddings
