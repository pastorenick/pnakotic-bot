"""
Utility functions for rate limiting, message formatting, etc.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# Rate limiting storage
user_requests = defaultdict(list)
group_requests = defaultdict(list)


def is_rate_limited(identifier: int, is_group: bool = False) -> bool:
    """
    Check if user/group exceeded rate limit
    
    Args:
        identifier: user_id or chat_id
        is_group: True if checking group limit, False for user
    
    Returns:
        True if rate limited, False otherwise
    """
    max_requests = 5 if is_group else 10
    window_minutes = 1
    
    storage = group_requests if is_group else user_requests
    
    now = datetime.now()
    cutoff = now - timedelta(minutes=window_minutes)
    
    # Remove old requests
    storage[identifier] = [
        req_time for req_time in storage[identifier]
        if req_time > cutoff
    ]
    
    # Check limit
    if len(storage[identifier]) >= max_requests:
        return True
    
    # Add new request
    storage[identifier].append(now)
    return False


def format_card_message(card: Dict, faqs: Optional[List[Dict[str, str]]]) -> str:
    """
    Format card information into Telegram message
    Shows all FAQs (no truncation as per user preference)
    
    Args:
        card: Card data dict from API
        faqs: List of FAQ dicts or None
    
    Returns:
        Formatted message string (Markdown)
    """
    guardian = card.get('guardian', {})
    
    # Header
    msg = f"🃏 *{card['name']}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # Type & Rarity
    card_type = guardian.get('type', 'Unknown')
    rarity = guardian.get('rarity', 'Unknown')
    if rarity and rarity != 'Unknown':
        msg += f"📊 *Type:* {rarity} {card_type}\n"
    else:
        msg += f"📊 *Type:* {card_type}\n"
    
    # Element
    elements = card.get('elements', 'None')
    msg += f"🌀 *Element:* {elements}\n"
    
    # Cost & Thresholds
    cost = guardian.get('cost')
    thresholds = guardian.get('thresholds', {})
    threshold_str = ', '.join([
        f"{k.capitalize()}: {v}"
        for k, v in thresholds.items()
        if v > 0
    ])
    
    if cost is not None:
        msg += f"💎 *Cost:* {cost}"
        if threshold_str:
            msg += f" | {threshold_str}"
        msg += "\n"
    
    # Power/Defense (for minions)
    attack = guardian.get('attack')
    defence = guardian.get('defence')
    if attack is not None and defence is not None:
        msg += f"⚔️ *ATK/DEF:* {attack}/{defence}\n"
    
    # Life (for avatars)
    life = guardian.get('life')
    if life is not None:
        msg += f"❤️ *Life:* {life}\n"
    
    # Rules text
    rules = guardian.get('rulesText', '')
    if rules:
        msg += f"\n📖 *Effect:*\n{rules}\n"
    
    # Subtypes
    subtypes = card.get('subTypes', '')
    if subtypes:
        msg += f"\n🏷️ *Subtypes:* {subtypes}\n"
    
    # FAQs - Show ALL entries (no truncation)
    if faqs and len(faqs) > 0:
        msg += f"\n❓ *FAQ* ({len(faqs)} entries):\n\n"
        
        for i, faq in enumerate(faqs, 1):
            q = faq.get('question', '')
            a = faq.get('answer', '')
            msg += f"*Q{i}:* {q}\n"
            msg += f"*A:* {a}\n\n"
    
    # Link to curiosa.io
    card_slug = card['name'].lower().replace(' ', '-').replace("'", "").replace('"', '')
    msg += f"\n🔗 [View on Curiosa](https://curiosa.io/cards/{card_slug})"
    
    return msg
