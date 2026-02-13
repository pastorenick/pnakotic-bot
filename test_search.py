"""
Test script to search for cards with specific abilities
"""

from bot.card_fetcher import load_cards
from bot.replacement_finder import find_replacements, format_replacement_explanation

# Load all cards
print("Loading cards...")
cards = load_cards()
print(f"Loaded {len(cards)} cards\n")

# Find a card that can pull and submerge/bury creatures
print("=" * 70)
print("SEARCHING FOR: Cards that can pull and submerge/bury creatures")
print("=" * 70)
print()

# First, let's find cards with "submerge" or "bury" in their text
print("Cards with 'submerge' or 'bury' abilities:")
print("-" * 70)
submerge_bury_cards = []
for card in cards:
    rules_text = card.get('guardian', {}).get('rulesText', '').lower()
    if 'submerge' in rules_text or 'bury' in rules_text:
        name = card.get('name', '')
        card_type = card.get('guardian', {}).get('type', '')
        cost = card.get('guardian', {}).get('cost', 'N/A')
        print(f"  {name} ({card_type}, Cost: {cost})")
        print(f"    Rules: {card.get('guardian', {}).get('rulesText', '')}")
        print()
        submerge_bury_cards.append(card)

print(f"\nFound {len(submerge_bury_cards)} cards with submerge/bury abilities")
print()

# Now test the similarity search with one of these cards
if submerge_bury_cards:
    test_card = submerge_bury_cards[0]
    test_card_name = test_card['name']
    
    print("=" * 70)
    print(f"TESTING VECTOR SIMILARITY SEARCH")
    print(f"Finding cards similar to: {test_card_name}")
    print("=" * 70)
    print()
    
    # Find replacements
    replacements = find_replacements(test_card_name, cards, max_results=5, min_score=20.0)
    
    if replacements:
        print(f"Found {len(replacements)} similar cards:\n")
        for i, replacement in enumerate(replacements, 1):
            explanation = format_replacement_explanation(test_card, replacement)
            print(f"{i}. {explanation}")
            
            # Show the actual rules text
            rules = replacement['card'].get('guardian', {}).get('rulesText', '')
            if rules:
                print(f"   Rules: {rules}")
            print()
    else:
        print("No similar cards found")
