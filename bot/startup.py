"""
Startup initialization script
Ensures embeddings are generated before the bot starts
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

EMBEDDINGS_FILE = "data/cache/embeddings.json"
CARDS_FILE = "data/cache/cards.json"


def ensure_embeddings_exist():
    """
    Check if embeddings exist, generate if missing
    This runs on startup to ensure the bot has embeddings available
    
    NOTE: On Fly.io with limited RAM, we expect embeddings to be pre-generated
    and committed to the repository. This function only generates if truly missing.
    """
    if os.path.exists(EMBEDDINGS_FILE):
        file_size = os.path.getsize(EMBEDDINGS_FILE) / (1024 * 1024)  # MB
        logger.info(f"✅ Embeddings cache found ({file_size:.1f} MB)")
        return True
    
    logger.warning("⚠️ Embeddings cache not found!")
    logger.warning("The bot will use keyword-based similarity search as fallback.")
    logger.warning("To enable vector search, run: python -m bot.generate_embeddings")
    
    # Don't try to generate on startup in production - it requires too much RAM
    # and takes too long. Embeddings should be pre-generated and committed.
    return False


def init_cache_directory():
    """Ensure cache directory exists"""
    cache_dir = Path("data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Cache directory: {cache_dir.absolute()}")
