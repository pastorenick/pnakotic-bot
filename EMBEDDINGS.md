# Vector Embeddings for Card Similarity

This document explains how to use the vector-based similarity search system.

## Overview

The bot now uses semantic vector embeddings to find similar cards instead of just keyword matching. This provides much better results by understanding the actual meaning and function of card abilities.

## How It Works

1. **Embeddings Generation**: Card abilities are converted to 384-dimensional vectors using the `all-MiniLM-L6-v2` model
2. **Similarity Search**: When finding replacements, the bot compares vectors using cosine similarity
3. **Fallback**: If embeddings aren't available, the system falls back to the old keyword-based matching

## Setup Instructions

### 1. Install Dependencies

First, install the required packages:

```bash
pip install -r requirements.txt
```

### 2. Generate Embeddings (One-time setup)

Run the embedding generation script to process all existing cards:

```bash
cd /home/nico/Projects/Sorcery/PnakoticBot
python -m bot.generate_embeddings
```

This will:
- Load all cards from the cache
- Generate vector embeddings for each card's abilities
- Save embeddings to `data/cache/embeddings.json`

**Note**: This needs to run AFTER the bot has been started at least once to populate the cards cache.

### 3. Use the Bot

The bot will automatically use embeddings when available. No configuration needed!

## Updating Embeddings

You should regenerate embeddings when:
- New card sets are released
- The cards cache is updated
- You want to use a different embedding model

Simply run the generation script again:

```bash
python -m bot.generate_embeddings
```

## Scoring System

### With Vector Embeddings (Primary)
- **Vector similarity**: 70% - Semantic understanding of abilities
- **Element/thresholds**: 20% - Color identity match
- **Mana cost**: 10% - Cost similarity

### Keyword Fallback (When embeddings unavailable)
- **Keywords/abilities**: 50% - Keyword overlap
- **Element/thresholds**: 25% - Color identity match
- **Mana cost**: 15% - Cost similarity
- **Card type**: 10% - Type bonus

## Performance

- **Embedding Generation**: ~1-2 minutes for ~1000 cards (one-time)
- **Search Performance**: Similar to before (~0.1-0.5s)
- **Storage**: ~2-3 MB for embeddings cache
- **Model Download**: ~80 MB (downloaded once, cached locally)

## Technical Details

### Model
- **Name**: `all-MiniLM-L6-v2`
- **Dimension**: 384
- **Type**: Sentence Transformer
- **Speed**: Fast (CPU-friendly)

### What Gets Embedded
For each card, we create a description including:
- Card type and subtypes
- Elements
- Stats (attack/defense)
- Full rules text

Example:
```
"Minion. Mortal. Element: Air. Stats: 1/1. Spellcaster. Genesis → Draw a spell."
```

## Troubleshooting

### Embeddings not loading
- Make sure `data/cache/embeddings.json` exists
- Run `python -m bot.generate_embeddings` to create it

### "Cards cache not found" error
- Start the bot first to populate the cards cache
- Or manually fetch cards using the bot's `/replace` command once

### Slow performance
- Vector search should be similar speed to keyword search
- If slow, check if numpy is using optimized BLAS libraries

### Want to use a different model?
Edit `MODEL_NAME` in `bot/generate_embeddings.py` and regenerate embeddings.

## Example Usage

The bot command remains the same:

```
/replace Apprentice Wizard
```

The bot will now find semantically similar cards rather than just keyword matches!
