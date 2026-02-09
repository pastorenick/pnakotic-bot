"""
Simple JSON file-based caching with TTL (Time To Live)
Supports lazy loading - cache is populated on first request, not on startup
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_cache(cache_file: str) -> Optional[Dict[str, Any]]:
    """
    Load cache from JSON file
    
    Args:
        cache_file: Path to cache file
        
    Returns:
        Cache dict with 'timestamp' and 'data' keys, or None if not found/invalid
    """
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading cache from {cache_file}: {e}")
        return None


def save_cache(cache_file: str, data: Any) -> None:
    """
    Save data to cache with timestamp
    
    Args:
        cache_file: Path to cache file
        data: Data to cache (dict or list)
    """
    # Ensure directory exists
    Path(cache_file).parent.mkdir(parents=True, exist_ok=True)
    
    cache_obj = {
        'timestamp': datetime.utcnow().isoformat(),
        'data': data
    }
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_obj, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving cache to {cache_file}: {e}")


def is_cache_valid(cache_file: str, ttl_hours: int = 24) -> bool:
    """
    Check if cache file exists and is fresh
    
    Args:
        cache_file: Path to cache file
        ttl_hours: Time to live in hours (default: 24)
        
    Returns:
        True if cache is valid and fresh, False otherwise
    """
    if not os.path.exists(cache_file):
        return False
    
    cache = load_cache(cache_file)
    if not cache or 'timestamp' not in cache:
        return False
    
    try:
        # Check TTL
        cached_time = datetime.fromisoformat(cache['timestamp'])
        expiry_time = cached_time + timedelta(hours=ttl_hours)
        
        return datetime.utcnow() < expiry_time
    except (ValueError, TypeError) as e:
        print(f"Error checking cache validity: {e}")
        return False
