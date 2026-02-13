"""
Interactive test script for the vector similarity search
Simulates the /replace command without needing Telegram
"""

import sys
from bot.card_fetcher import load_cards, search_card
from bot.replacement_finder import find_replacements, format_replacement_explanation

def main():
    # Load cards
    print("Loading cards...")
    cards = load_cards()
    print(f"Loaded {len(cards)} cards")
    print()
    
    # Interactive loop
    while True:
        print("=" * 70)
        card_name = input("Enter a card name to find replacements (or 'quit' to exit): ")
        print()
        
        if card_name.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not card_name.strip():
            continue
        
        # Search for the card
        result = search_card(card_name, cards)
        
        if result is None:
            print(f"❌ Card '{card_name}' not found")
            print()
            continue
        
        if isinstance(result, list):
            print(f"❌ Multiple cards match '{card_name}':")
            for card in result[:5]:
                print(f"  - {card['name']}")
            print()
            continue
        
        # Found the card
        target_card = result
        card_name = target_card['name']
        
        print(f"🔍 Finding replacements for: {card_name}")
        print()
        
        # Show the target card's details
        guardian = target_card.get('guardian', {})
        print(f"Type: {guardian.get('type', 'N/A')}")
        print(f"Cost: {guardian.get('cost', 'N/A')}")
        print(f"Elements: {target_card.get('elements', 'N/A')}")
        
        attack = guardian.get('attack')
        defence = guardian.get('defence')
        if attack is not None and defence is not None:
            print(f"Stats: {attack}/{defence}")
        
        rules = guardian.get('rulesText', '')
        if rules:
            print(f"Rules: {rules}")
        
        print()
        print("-" * 70)
        print()
        
        # Find replacements
        replacements = find_replacements(card_name, cards, max_results=5, min_score=30.0)
        
        if not replacements:
            print("❌ No similar cards found (try lowering the minimum similarity threshold)")
            print()
            continue
        
        print(f"✅ Found {len(replacements)} similar cards:")
        print()
        
        for i, replacement in enumerate(replacements, 1):
            explanation = format_replacement_explanation(target_card, replacement)
            print(f"{i}. {explanation}")
            print()
        
        print()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
