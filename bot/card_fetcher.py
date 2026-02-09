"""
Sorcery API client for fetching card data
Includes fuzzy search with typo tolerance and image URL generation
"""

import requests
from fuzzywuzzy import process
from typing import Dict, List, Optional, Union
from bot.cache import load_cache, save_cache, is_cache_valid


# API Configuration
API_URL = "https://api.sorcerytcg.com/api/cards"
IMAGE_CDN = "https://d27a44hjr9gen3.cloudfront.net/cards/"
CACHE_FILE = "data/cache/cards.json"
CACHE_TTL_HOURS = 24


def fetch_all_cards() -> List[Dict]:
    """
    Fetch all cards from Sorcery API
    
    Returns:
        List of card dictionaries
    """
    try:
        print(f"Fetching cards from {API_URL}...")
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        cards = response.json()
        print(f"Successfully fetched {len(cards)} cards")
        return cards
    except requests.RequestException as e:
        print(f"Error fetching cards from API: {e}")
        return []


def load_cards() -> List[Dict]:
    """
    Load cards from cache or fetch if stale (lazy load)
    Cache is populated on first request, not on startup
    
    Returns:
        List of card dictionaries
    """
    if is_cache_valid(CACHE_FILE, CACHE_TTL_HOURS):
        cached = load_cache(CACHE_FILE)
        if cached:
            print("Loading cards from cache")
            return cached['data']
    
    # Fetch fresh data (only when needed)
    print("Cache miss or expired - fetching fresh card data...")
    cards = fetch_all_cards()
    
    if cards:
        save_cache(CACHE_FILE, cards)
        print(f"Cached {len(cards)} cards")
    
    return cards


def normalize_name(name: str) -> str:
    """
    Normalize card name for comparison
    
    Args:
        name: Card name
        
    Returns:
        Normalized lowercase name
    """
    return name.lower().strip()


def search_card(query: str, cards: List[Dict]) -> Optional[Union[Dict, List[Dict]]]:
    """
    Search for card by name with fuzzy matching
    
    Args:
        query: Search query
        cards: List of all cards
        
    Returns:
        - Single dict if exact match found
        - List of dicts if multiple matches found
        - None if no match found
    """
    if not cards:
        return None
    
    query_norm = normalize_name(query)
    
    # 1. Exact match (case-insensitive)
    exact = [c for c in cards if normalize_name(c['name']) == query_norm]
    if exact:
        return exact[0]
    
    # 2. Partial match (substring)
    partial = [c for c in cards if query_norm in normalize_name(c['name'])]
    if len(partial) == 1:
        return partial[0]
    elif len(partial) > 1:
        return partial  # Multiple matches
    
    # 3. Fuzzy match (typo tolerance)
    card_names = [c['name'] for c in cards]
    best_match_result = process.extractOne(query, card_names)
    
    if best_match_result:
        best_match, score = best_match_result
        
        if score >= 80:  # 80% confidence threshold
            return next(c for c in cards if c['name'] == best_match)
    
    return None  # No match found


def get_card_image_url(card: Dict, prefer_standard: bool = True) -> Optional[str]:
    """
    Get CloudFront CDN URL for card image
    Prefers standard finish from most recent set
    
    Args:
        card: Card dictionary
        prefer_standard: Prefer standard finish over foil/rainbow
        
    Returns:
        Image URL string, or None if not available
    """
    # Get most recent set (last in list)
    sets = card.get('sets', [])
    if not sets:
        return None
    
    recent_set = sets[-1]  # Most recent
    variants = recent_set.get('variants', [])
    
    if not variants:
        return None
    
    # Prefer standard finish
    if prefer_standard:
        standard = [v for v in variants if v.get('finish') == 'Standard']
        if standard:
            slug = standard[0]['slug']
            return f"{IMAGE_CDN}{slug}.png"
    
    # Fallback to first variant
    slug = variants[0]['slug']
    return f"{IMAGE_CDN}{slug}.png"
