# Deployment Guide: Vector Similarity Search

## What Changed

This update adds semantic vector-based similarity search to the bot using pre-computed embeddings.

### New Features
- **Vector similarity search** using sentence-transformers
- **Pre-generated embeddings** (9.3 MB) included in repository
- **Automatic fallback** to keyword search if embeddings unavailable
- **Better card recommendations** based on semantic understanding

### Files Modified
- `bot/replacement_finder.py` - Added vector similarity scoring
- `requirements.txt` - Added sentence-transformers and numpy
- `.gitignore` - Allow embeddings.json to be committed
- `main.py` - Added startup initialization

### New Files
- `bot/generate_embeddings.py` - Script to regenerate embeddings
- `bot/startup.py` - Startup checks for embeddings
- `data/cache/embeddings.json` - Pre-generated embeddings (9.3 MB)
- `EMBEDDINGS.md` - Documentation

## Deployment Steps

### Step 1: Review Changes
```bash
git status
git diff requirements.txt
```

### Step 2: Commit and Push
```bash
git add .
git commit -m "Add vector-based similarity search with pre-generated embeddings"
git push origin main
```

### Step 3: Deploy to Fly.io
Fly.io will automatically deploy when you push to main (if auto-deploy is enabled).

Or manually deploy:
```bash
fly deploy
```

### Step 4: Verify
Check logs to ensure embeddings are loaded:
```bash
fly logs
```

You should see: `✅ Embeddings cache found (9.3 MB)`

## Memory Considerations

The sentence-transformers model requires ~200MB to load, but we're using **pre-generated embeddings** which only need ~10MB in memory. This works fine with Fly.io's 256MB RAM limit.

## Updating Embeddings

When new cards are released:

1. **Locally generate new embeddings:**
   ```bash
   python -m bot.generate_embeddings
   ```

2. **Commit and deploy:**
   ```bash
   git add data/cache/embeddings.json
   git commit -m "Update embeddings for new card set"
   git push
   ```

## Fallback Behavior

If embeddings are missing or fail to load:
- Bot automatically falls back to keyword-based similarity search
- No degradation in functionality, just less semantic understanding
- Logs will show warning: "Bot will use keyword-based similarity search"

## Testing

Test the deployment with these commands in Telegram:
```
/replace Apprentice Wizard
/replace Unland Angler
/replace Nelly Longarms
```

Compare results with old keyword-based search - should see more semantically similar cards!
