"""
eBay API integration for fetching Sorcery card market prices
Uses eBay Browse API to search for active listings
"""

import os
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bot.cache import load_cache, save_cache

logger = logging.getLogger(__name__)

# eBay API endpoints - detect sandbox vs production
# Sandbox credentials start with "SBX-" for Cert ID
def _get_ebay_api_base():
    """Determine if using Sandbox or Production based on credentials"""
    cert_id = os.getenv('EBAY_CERT_ID', '')
    if cert_id.startswith('SBX-'):
        logger.info("Using eBay Sandbox API")
        return "https://api.sandbox.ebay.com"
    else:
        logger.info("Using eBay Production API")
        return "https://api.ebay.com"

EBAY_API_BASE = _get_ebay_api_base()
EBAY_AUTH_URL = f"{EBAY_API_BASE}/identity/v1/oauth2/token"
EBAY_BROWSE_URL = f"{EBAY_API_BASE}/buy/browse/v1/item_summary/search"

# Cache settings
EBAY_CACHE_FILE = "ebay_prices.json"
EBAY_TOKEN_CACHE_FILE = "ebay_token.json"


def get_ebay_credentials() -> tuple:
    """
    Get eBay API credentials from environment variables
    
    Returns:
        Tuple of (client_id, client_secret)
    """
    client_id = os.getenv('EBAY_APP_ID')
    client_secret = os.getenv('EBAY_CERT_ID')
    
    if not client_id or not client_secret:
        logger.warning("eBay API credentials not configured. Set EBAY_APP_ID and EBAY_CERT_ID environment variables.")
        return None, None
    
    return client_id, client_secret


def get_access_token(force_refresh: bool = False) -> Optional[str]:
    """
    Get OAuth access token for eBay API
    Tokens are cached and reused until they expire
    
    Args:
        force_refresh: Force token refresh even if cached token is valid
        
    Returns:
        Access token string or None if authentication fails
    """
    # Check for cached token first
    if not force_refresh:
        token_cache = load_cache(EBAY_TOKEN_CACHE_FILE)
        if token_cache:
            token_data = token_cache.get('token_data')
            if token_data:
                # Check if token is still valid (with 5 minute buffer)
                expires_at = datetime.fromisoformat(token_data['expires_at'])
                if datetime.now() < expires_at - timedelta(minutes=5):
                    logger.info("Using cached eBay access token")
                    return token_data['access_token']
    
    # Get credentials
    client_id, client_secret = get_ebay_credentials()
    if not client_id or not client_secret:
        return None
    
    # Request new token
    logger.info("Requesting new eBay access token...")
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    data = {
        'grant_type': 'client_credentials',
        'scope': 'https://api.ebay.com/oauth/api_scope'
    }
    
    try:
        response = requests.post(
            EBAY_AUTH_URL,
            headers=headers,
            data=data,
            auth=(client_id, client_secret),
            timeout=10
        )
        response.raise_for_status()
        
        token_response = response.json()
        access_token = token_response['access_token']
        expires_in = token_response['expires_in']  # seconds
        
        # Cache the token
        token_data = {
            'access_token': access_token,
            'expires_at': (datetime.now() + timedelta(seconds=expires_in)).isoformat()
        }
        
        save_cache(EBAY_TOKEN_CACHE_FILE, {'token_data': token_data})
        logger.info(f"eBay access token obtained, expires in {expires_in} seconds")
        
        return access_token
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get eBay access token: {e}")
        return None


def search_ebay_listings(card_name: str, limit: int = 10, foil_only: bool = False) -> Optional[List[Dict]]:
    """
    Search eBay for Sorcery card listings
    
    Args:
        card_name: Name of the card to search for
        limit: Maximum number of listings to return (default 10)
        foil_only: If True, search only for foil versions. If False, search for non-foil (default False)
        
    Returns:
        List of listing dictionaries or None if search fails
    """
    # Get access token
    access_token = get_access_token()
    if not access_token:
        logger.error("Cannot search eBay: no access token")
        return None
    
    # Build search query
    # Add "Sorcery Contested Realm" to ensure we get the right game
    # Add foil/non-foil filtering to the query
    if foil_only:
        # Search specifically for foil versions
        search_query = f"{card_name} Sorcery Contested Realm foil"
    else:
        # Search for non-foil versions (exclude foil listings)
        # We'll filter foil listings in the parsing stage
        search_query = f"{card_name} Sorcery Contested Realm"
    
    # eBay API parameters
    params = {
        'q': search_query,
        'limit': min(limit, 50),  # eBay allows max 200, we use 50 as reasonable limit
        'filter': 'buyingOptions:{FIXED_PRICE}',  # Only Buy It Now (not auctions)
        'sort': 'price',  # Sort by price ascending
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US',  # US marketplace
        'X-EBAY-C-ENDUSERCTX': 'affiliateCampaignId=<ePNCampaignId>,affiliateReferenceId=<referenceId>'
    }
    
    try:
        logger.info(f"Searching eBay for: {search_query}")
        response = requests.get(
            EBAY_BROWSE_URL,
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Extract item summaries
        items = data.get('itemSummaries', [])
        
        if not items:
            logger.info(f"No eBay listings found for '{card_name}'")
            return []
        
        # Parse and format listings
        listings = []
        for item in items[:limit]:
            listing = parse_ebay_listing(item)
            if listing:
                # Filter by foil status if specified
                if foil_only and not listing.get('is_foil', False):
                    # Skip non-foil listings when searching for foil
                    continue
                elif not foil_only and listing.get('is_foil', False):
                    # Skip foil listings when searching for non-foil
                    continue
                listings.append(listing)
        
        logger.info(f"Found {len(listings)} eBay listings for '{card_name}'")
        return listings
        
    except requests.exceptions.RequestException as e:
        logger.error(f"eBay search failed: {e}")
        return None


def parse_ebay_listing(item: Dict) -> Optional[Dict]:
    """
    Parse eBay item summary into simplified listing dictionary
    
    Args:
        item: eBay item summary dictionary
        
    Returns:
        Simplified listing dictionary or None if parsing fails
    """
    try:
        # Extract price
        price_obj = item.get('price', {})
        price = price_obj.get('value', 'N/A')
        currency = price_obj.get('currency', 'USD')
        
        # Extract location
        location = item.get('itemLocation', {})
        city = location.get('city', '')
        state = location.get('stateOrProvince', '')
        country = location.get('country', '')
        
        # Format location string
        location_parts = [p for p in [city, state, country] if p]
        location_str = ', '.join(location_parts) if location_parts else 'Unknown'
        
        # Extract condition
        condition = item.get('condition', 'N/A')
        
        # Extract URL
        item_url = item.get('itemWebUrl', '')
        
        # Extract title
        title = item.get('title', 'Unknown Item')
        
        # Detect foil status from title
        # Look for common foil indicators in title
        title_lower = title.lower()
        
        # Check for non-foil indicators first (these take precedence)
        non_foil_keywords = ['non-foil', 'nonfoil', 'non foil', ' nf ', ' nf,', ' nf)', 'regular']
        is_non_foil_explicit = any(keyword in title_lower for keyword in non_foil_keywords)
        
        # Check for foil indicators
        foil_keywords = ['foil', 'holo', 'holographic', 'shiny', 'etched']
        has_foil_keyword = any(keyword in title_lower for keyword in foil_keywords)
        
        # Determine final foil status
        # If explicitly marked as non-foil, it's not foil even if "foil" appears in title
        if is_non_foil_explicit:
            is_foil = False
        else:
            is_foil = has_foil_keyword
        
        # Extract shipping info
        shipping = item.get('shippingOptions', [])
        shipping_cost = 'N/A'
        if shipping and len(shipping) > 0:
            shipping_price = shipping[0].get('shippingCost', {})
            if shipping_price:
                ship_value = shipping_price.get('value', '0')
                ship_currency = shipping_price.get('currency', 'USD')
                if float(ship_value) == 0:
                    shipping_cost = 'Free'
                else:
                    shipping_cost = f"{ship_value} {ship_currency}"
        
        return {
            'title': title,
            'price': price,
            'currency': currency,
            'condition': condition,
            'location': location_str,
            'shipping': shipping_cost,
            'url': item_url,
            'is_foil': is_foil,
        }
        
    except Exception as e:
        logger.error(f"Failed to parse eBay listing: {e}")
        return None


def get_price_statistics(listings: List[Dict]) -> Dict:
    """
    Calculate price statistics from listings
    
    Args:
        listings: List of listing dictionaries
        
    Returns:
        Dictionary with min, max, avg prices
    """
    if not listings:
        return {
            'min': None,
            'max': None,
            'avg': None,
            'count': 0
        }
    
    # Extract numeric prices
    prices = []
    for listing in listings:
        try:
            price = float(listing['price'])
            prices.append(price)
        except (ValueError, TypeError):
            continue
    
    if not prices:
        return {
            'min': None,
            'max': None,
            'avg': None,
            'count': 0
        }
    
    return {
        'min': min(prices),
        'max': max(prices),
        'avg': sum(prices) / len(prices),
        'count': len(prices),
        'currency': listings[0].get('currency', 'USD')
    }


def format_price_message(card_name: str, listings: List[Dict], stats: Dict, foil_only: bool = False) -> str:
    """
    Format eBay price data into Telegram message
    
    Args:
        card_name: Name of the card
        listings: List of listing dictionaries
        stats: Price statistics dictionary
        foil_only: Whether this is a foil-only search
        
    Returns:
        Formatted message string
    """
    if not listings:
        foil_text = " (Foil)" if foil_only else " (Non-Foil)"
        return f"💰 *Market Prices for {card_name}{foil_text}*\n\n❌ No active listings found on eBay.\n\n💡 Tip: Try checking TCGPlayer or the Sorcery Marketplace Discord."
    
    # Build message
    foil_indicator = " ✨ Foil" if foil_only else " 📄 Non-Foil"
    lines = [f"💰 *Market Prices for {card_name}{foil_indicator}*\n"]
    
    # Add statistics if available
    if stats['count'] > 0:
        currency = stats.get('currency', 'USD')
        lines.append(f"📊 *Price Range (from {stats['count']} listings):*")
        lines.append(f"• Low: ${stats['min']:.2f} {currency}")
        lines.append(f"• High: ${stats['max']:.2f} {currency}")
        lines.append(f"• Average: ${stats['avg']:.2f} {currency}\n")
    
    # Add top listings
    lines.append(f"🛒 *Current Listings (eBay):*")
    
    for i, listing in enumerate(listings[:5], 1):  # Show top 5
        try:
            price = float(listing['price'])
            price_str = f"${price:.2f}"
        except (ValueError, TypeError):
            price_str = str(listing['price'])
        
        # Format listing line with foil/non-foil indicator
        condition = listing.get('condition', 'N/A')
        location = listing.get('location', 'Unknown')
        shipping = listing.get('shipping', 'N/A')
        is_foil = listing.get('is_foil', False)
        item_url = listing.get('url', '')
        
        # Add foil indicator
        foil_indicator = "✨ Foil" if is_foil else "📄 Non-Foil"
        
        # Create clickable link if URL is available
        if item_url:
            lines.append(f"{i}. [{price_str} - {condition}]({item_url}) - {foil_indicator}")
        else:
            lines.append(f"{i}. {price_str} - {condition} - {foil_indicator}")
        
        lines.append(f"   📍 {location}")
        if shipping != 'N/A':
            lines.append(f"   📦 Shipping: {shipping}")
        lines.append("")  # Blank line
    
    # Add footer
    if len(listings) > 5:
        lines.append(f"_...and {len(listings) - 5} more listings_\n")
    
    lines.append("🔗 Data from eBay")
    
    return '\n'.join(lines)


# ============================================================================
# eBay Finding API - For Sold/Completed Listings
# ============================================================================

# Finding API endpoint (uses App ID, not OAuth)
def _get_finding_api_base():
    """Get Finding API base URL"""
    cert_id = os.getenv('EBAY_CERT_ID', '')
    if cert_id.startswith('SBX-'):
        return "https://svcs.sandbox.ebay.com/services/search/FindingService/v1"
    else:
        return "https://svcs.ebay.com/services/search/FindingService/v1"

EBAY_FINDING_URL = _get_finding_api_base()


def search_ebay_sold_listings(card_name: str, limit: int = 10, foil_only: bool = False) -> Optional[List[Dict]]:
    """
    Search eBay for completed/sold Sorcery card listings using Finding API
    
    Args:
        card_name: Name of the card to search for
        limit: Maximum number of listings to return (default 10)
        foil_only: If True, search only for foil versions. If False, search for non-foil (default False)
        
    Returns:
        List of listing dictionaries or None if search fails
    """
    # Get App ID (Finding API uses App ID, not OAuth)
    app_id = os.getenv('EBAY_APP_ID')
    if not app_id:
        logger.error("Cannot search eBay Finding API: no EBAY_APP_ID")
        return None
    
    # Build search query with foil filtering
    if foil_only:
        search_query = f"{card_name} Sorcery Contested Realm foil"
    else:
        search_query = f"{card_name} Sorcery Contested Realm"
    
    # Finding API parameters (uses GET request with query params)
    params = {
        'OPERATION-NAME': 'findCompletedItems',
        'SERVICE-VERSION': '1.0.0',
        'SECURITY-APPNAME': app_id,
        'RESPONSE-DATA-FORMAT': 'JSON',
        'REST-PAYLOAD': '',
        'keywords': search_query,
        'paginationInput.entriesPerPage': min(limit, 100),  # Max 100 per page
        'sortOrder': 'EndTimeSoonest',  # Most recent sales first
    }
    
    try:
        logger.info(f"Searching eBay sold items for: {search_query}")
        response = requests.get(
            EBAY_FINDING_URL,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Extract items from Finding API response structure
        search_result = data.get('findCompletedItemsResponse', [{}])[0]
        items_array = search_result.get('searchResult', [{}])[0].get('item', [])
        
        if not items_array:
            logger.info(f"No sold listings found for '{card_name}'")
            return []
        
        # Parse and format listings
        listings = []
        for item in items_array[:limit]:
            listing = parse_finding_api_listing(item)
            if listing:
                # Filter by foil status if specified
                if foil_only and not listing.get('is_foil', False):
                    continue
                elif not foil_only and listing.get('is_foil', False):
                    continue
                listings.append(listing)
        
        logger.info(f"Found {len(listings)} sold listings for '{card_name}'")
        return listings
        
    except requests.exceptions.RequestException as e:
        logger.error(f"eBay Finding API search failed: {e}")
        return None


def parse_finding_api_listing(item: Dict) -> Optional[Dict]:
    """
    Parse eBay Finding API item into simplified listing dictionary
    
    Args:
        item: eBay Finding API item dictionary
        
    Returns:
        Simplified listing dictionary or None if parsing fails
    """
    try:
        # Extract title
        title = item.get('title', ['Unknown Item'])[0]
        
        # Extract price (sold price)
        selling_status = item.get('sellingStatus', [{}])[0]
        price_obj = selling_status.get('currentPrice', [{}])[0]
        price = price_obj.get('__value__', 'N/A')
        currency = price_obj.get('@currencyId', 'USD')
        
        # Extract location
        location = item.get('location', ['Unknown'])[0]
        country = item.get('country', ['US'])[0]
        location_str = f"{location}, {country}" if location != 'Unknown' else country
        
        # Extract condition
        condition_obj = item.get('condition', [{}])[0]
        condition = condition_obj.get('conditionDisplayName', ['N/A'])[0]
        
        # Extract URL
        item_url = item.get('viewItemURL', [''])[0]
        
        # Extract shipping info
        shipping_info = item.get('shippingInfo', [{}])[0]
        shipping_cost_obj = shipping_info.get('shippingServiceCost', [{}])[0]
        shipping_value = shipping_cost_obj.get('__value__', '0')
        shipping_currency = shipping_cost_obj.get('@currencyId', 'USD')
        
        if float(shipping_value) == 0:
            shipping_cost = 'Free'
        else:
            shipping_cost = f"{shipping_value} {shipping_currency}"
        
        # Extract end date (when item sold)
        listing_info = item.get('listingInfo', [{}])[0]
        end_time = listing_info.get('endTime', [''])[0]
        
        # Parse end time to readable format
        sold_date = 'Unknown'
        if end_time:
            try:
                dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                sold_date = dt.strftime('%Y-%m-%d')
            except Exception:
                sold_date = end_time[:10]  # Just take date part
        
        # Detect foil status from title (same logic as Browse API)
        title_lower = title.lower()
        non_foil_keywords = ['non-foil', 'nonfoil', 'non foil', ' nf ', ' nf,', ' nf)', 'regular']
        is_non_foil_explicit = any(keyword in title_lower for keyword in non_foil_keywords)
        foil_keywords = ['foil', 'holo', 'holographic', 'shiny', 'etched']
        has_foil_keyword = any(keyword in title_lower for keyword in foil_keywords)
        
        if is_non_foil_explicit:
            is_foil = False
        else:
            is_foil = has_foil_keyword
        
        return {
            'title': title,
            'price': price,
            'currency': currency,
            'condition': condition,
            'location': location_str,
            'shipping': shipping_cost,
            'url': item_url,
            'is_foil': is_foil,
            'sold_date': sold_date,
        }
        
    except Exception as e:
        logger.error(f"Failed to parse Finding API listing: {e}")
        return None


def format_sold_price_message(card_name: str, listings: List[Dict], stats: Dict, foil_only: bool = False) -> str:
    """
    Format eBay sold listing price data into Telegram message
    
    Args:
        card_name: Name of the card
        listings: List of sold listing dictionaries
        stats: Price statistics dictionary
        foil_only: Whether this is a foil-only search
        
    Returns:
        Formatted message string
    """
    if not listings:
        foil_text = " (Foil)" if foil_only else " (Non-Foil)"
        return f"📊 *Sold Prices for {card_name}{foil_text}*\n\n❌ No completed sales found on eBay.\n\n💡 Tip: This card may not have sold recently, or try checking active listings with `/price`."
    
    # Build message
    foil_indicator = " ✨ Foil" if foil_only else " 📄 Non-Foil"
    lines = [f"📊 *Sold Prices for {card_name}{foil_indicator}*\n"]
    
    # Add statistics if available
    if stats['count'] > 0:
        currency = stats.get('currency', 'USD')
        lines.append(f"💰 *Price Range (from {stats['count']} recent sales):*")
        lines.append(f"• Low: ${stats['min']:.2f} {currency}")
        lines.append(f"• High: ${stats['max']:.2f} {currency}")
        lines.append(f"• Average: ${stats['avg']:.2f} {currency}\n")
    
    # Add top sold listings
    lines.append(f"🏷️ *Recent Sales (eBay):*")
    
    for i, listing in enumerate(listings[:5], 1):  # Show top 5
        try:
            price = float(listing['price'])
            price_str = f"${price:.2f}"
        except (ValueError, TypeError):
            price_str = str(listing['price'])
        
        # Format listing line
        condition = listing.get('condition', 'N/A')
        location = listing.get('location', 'Unknown')
        shipping = listing.get('shipping', 'N/A')
        is_foil = listing.get('is_foil', False)
        sold_date = listing.get('sold_date', 'Unknown')
        item_url = listing.get('url', '')
        
        # Add foil indicator
        foil_indicator = "✨ Foil" if is_foil else "📄 Non-Foil"
        
        # Create clickable link if URL is available
        if item_url:
            lines.append(f"{i}. [{price_str} - {condition}]({item_url}) - {foil_indicator}")
        else:
            lines.append(f"{i}. {price_str} - {condition} - {foil_indicator}")
        
        lines.append(f"   📅 Sold: {sold_date}")
        lines.append(f"   📍 {location}")
        if shipping != 'N/A':
            lines.append(f"   📦 Shipping: {shipping}")
        lines.append("")  # Blank line
    
    # Add footer
    if len(listings) > 5:
        lines.append(f"_...and {len(listings) - 5} more sales_\n")
    
    lines.append("🔗 Historical data from eBay")
    
    return '\n'.join(lines)
