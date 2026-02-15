"""
JustTCG API integration for fetching card prices.
Provides price lookup functionality for Sorcery: Contested Realm cards.
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

# JustTCG API configuration
JUSTTCG_BASE_URL = "https://api.justtcg.com/v1"
JUSTTCG_API_KEY = os.getenv("JUSTTCG_API_KEY")

# Cache for game catalog check (to avoid repeated API calls)
_game_cache = {
    "sorcery_game_id": None,
    "last_checked": None,
    "cache_duration": timedelta(hours=24)  # Recheck once per day
}


def _get_headers() -> Dict[str, str]:
    """Get request headers with API key."""
    if not JUSTTCG_API_KEY:
        raise ValueError("JUSTTCG_API_KEY environment variable not set")
    
    return {
        "x-api-key": JUSTTCG_API_KEY,
        "Accept": "application/json"
    }


def get_sorcery_game_id() -> Optional[str]:
    """
    Check if Sorcery: Contested Realm is available in JustTCG catalog.
    Returns the game ID if found, None otherwise.
    Results are cached for 24 hours to minimize API calls.
    """
    # Check cache first
    now = datetime.now()
    if (_game_cache["last_checked"] and 
        now - _game_cache["last_checked"] < _game_cache["cache_duration"]):
        return _game_cache["sorcery_game_id"]
    
    try:
        response = requests.get(
            f"{JUSTTCG_BASE_URL}/games",
            headers=_get_headers(),
            timeout=10
        )
        response.raise_for_status()
        
        games = response.json()
        
        # Look for Sorcery in the games list
        # Try common variations of the game name
        sorcery_variations = [
            "sorcery-contested-realm",
            "sorcery",
            "Sorcery: Contested Realm",
            "Sorcery",
            "SORCERY"
        ]
        
        for game in games:
            game_id = game.get("id", "")
            game_name = game.get("name", "")
            
            for variation in sorcery_variations:
                if variation.lower() in game_id.lower() or variation.lower() in game_name.lower():
                    # Found it! Cache and return
                    _game_cache["sorcery_game_id"] = game_id
                    _game_cache["last_checked"] = now
                    logger.info(f"Found Sorcery game in JustTCG catalog: {game_id}")
                    return game_id
        
        # Not found - cache this result too
        _game_cache["sorcery_game_id"] = None
        _game_cache["last_checked"] = now
        logger.info("Sorcery not found in JustTCG catalog")
        return None
        
    except requests.RequestException as e:
        logger.error(f"Error fetching JustTCG games list: {e}")
        # Don't update cache on error - might be temporary
        return _game_cache.get("sorcery_game_id")


def search_card_prices(card_name: str) -> Optional[Dict[str, Any]]:
    """
    Search for a card by name and return pricing information.
    Returns None if Sorcery isn't in the catalog or card not found.
    """
    # First check if Sorcery is available
    game_id = get_sorcery_game_id()
    if not game_id:
        logger.info("Sorcery not available in JustTCG catalog yet")
        return None
    
    try:
        # Search for the card
        response = requests.get(
            f"{JUSTTCG_BASE_URL}/cards",
            headers=_get_headers(),
            params={
                "game": game_id,
                "q": card_name
            },
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        cards = data.get("data", [])
        
        if not cards:
            logger.info(f"No cards found for '{card_name}' in JustTCG")
            return None
        
        # Return the first match (most relevant)
        # Include metadata for API usage tracking
        return {
            "card": cards[0],
            "metadata": data.get("_metadata", {}),
            "total_results": len(cards)
        }
        
    except requests.RequestException as e:
        logger.error(f"Error searching JustTCG for '{card_name}': {e}")
        return None


def _format_price_change(change: Optional[float]) -> str:
    """Format price change percentage with appropriate emoji."""
    if change is None or change == 0:
        return "—"
    
    emoji = "📈" if change > 0 else "📉"
    sign = "+" if change > 0 else ""
    return f"{emoji} {sign}{change:.1f}%"


def _format_variant_prices(variants: List[Dict[str, Any]]) -> str:
    """Format pricing information from card variants."""
    if not variants:
        return "No pricing data available"
    
    lines = []
    
    # Find Near Mint Normal variant (most common reference point)
    nm_normal = None
    other_variants = []
    
    for variant in variants:
        condition = variant.get("condition", "")
        printing = variant.get("printing", "")
        
        if condition == "Near Mint" and printing == "Normal":
            nm_normal = variant
        else:
            other_variants.append(variant)
    
    # Show Near Mint Normal first if available
    if nm_normal:
        price = nm_normal.get("price")
        changes = nm_normal.get("priceChanges", {})
        
        if price:
            lines.append(f"📊 *Near Mint*: ${price:.2f}")
            
            # Add price changes if available
            change_parts = []
            if "7d" in changes:
                change_parts.append(f"7d: {_format_price_change(changes['7d'])}")
            if "30d" in changes:
                change_parts.append(f"30d: {_format_price_change(changes['30d'])}")
            
            if change_parts:
                lines.append(f"   {' | '.join(change_parts)}")
    
    # Show other conditions
    if other_variants:
        lines.append("\n*Other Conditions:*")
        for variant in other_variants[:5]:  # Limit to 5 to avoid spam
            condition = variant.get("condition", "Unknown")
            printing = variant.get("printing", "Normal")
            price = variant.get("price")
            
            if price:
                variant_label = condition
                if printing != "Normal":
                    variant_label += f" ({printing})"
                lines.append(f"• {variant_label}: ${price:.2f}")
    
    return "\n".join(lines) if lines else "No pricing data available"


def format_justtcg_prices(search_result: Optional[Dict[str, Any]]) -> str:
    """
    Format JustTCG pricing data for Telegram display.
    Handles both when data is available and when Sorcery isn't in catalog.
    """
    if not search_result:
        # Sorcery not in catalog yet
        return (
            "💎 *JustTCG prices not available yet*\n\n"
            "ℹ️ Sorcery: Contested Realm hasn't been added to the "
            "JustTCG catalog yet. Check back soon!"
        )
    
    card = search_result.get("card", {})
    card_name = card.get("name", "Unknown Card")
    variants = card.get("variants", [])
    
    # Build the message
    message_parts = [
        f"💎 *JustTCG Prices for {card_name}*\n",
        _format_variant_prices(variants),
        "\n🔗 Data from JustTCG"
    ]
    
    # Add metadata about API usage if available
    metadata = search_result.get("metadata", {})
    rate_limit = metadata.get("rateLimit", {})
    if rate_limit:
        remaining = rate_limit.get("remaining")
        if remaining is not None and remaining < 50:
            # Warn when getting low on API calls
            message_parts.append(f"\n⚠️ API calls remaining today: {remaining}")
    
    return "\n".join(message_parts)


def get_card_prices(card_name: str) -> str:
    """
    Main entry point for getting JustTCG prices.
    Returns formatted message ready for Telegram.
    """
    search_result = search_card_prices(card_name)
    return format_justtcg_prices(search_result)
