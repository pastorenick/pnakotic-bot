"""
FAQ scraper for curiosa.io
Parses FAQ page and extracts Q&A pairs per card
Shows all FAQs (no truncation as per user preference)
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from bot.cache import load_cache, save_cache, is_cache_valid


# FAQ Configuration
FAQ_URL = "https://curiosa.io/faqs"
CACHE_FILE = "data/cache/faqs.json"
CACHE_TTL_HOURS = 24


def scrape_all_faqs() -> Dict[str, List[Dict[str, str]]]:
    """
    Scrape all FAQs from curiosa.io/faqs
    
    Returns:
        Dictionary mapping card names to list of FAQ entries
        Format: {
            "Blink": [
                {"question": "...", "answer": "..."},
                ...
            ],
            ...
        }
    """
    try:
        print(f"Scraping FAQs from {FAQ_URL}...")
        response = requests.get(FAQ_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        faqs = {}
        current_card = None
        
        # Parse FAQ structure
        # Expected format:
        # <h3>Card Name</h3>
        # <p><strong>Question?</strong></p>
        # <p>Answer.</p>
        
        for element in soup.find_all(['h3', 'h4', 'p']):
            # Card section headers
            if element.name in ['h3', 'h4']:
                current_card = element.get_text().strip()
                if current_card and current_card not in faqs:
                    faqs[current_card] = []
            
            # FAQ entries
            elif element.name == 'p' and current_card:
                # Check if it's a question (has bold text)
                strong = element.find('strong')
                if strong:
                    question = strong.get_text().strip()
                    
                    # Next <p> sibling should be the answer
                    answer_elem = element.find_next_sibling('p')
                    if answer_elem:
                        # Make sure the answer isn't another question
                        if not answer_elem.find('strong'):
                            answer = answer_elem.get_text().strip()
                            faqs[current_card].append({
                                'question': question,
                                'answer': answer
                            })
        
        print(f"Successfully scraped FAQs for {len(faqs)} cards")
        return faqs
    
    except requests.RequestException as e:
        print(f"Error scraping FAQs: {e}")
        return {}
    except Exception as e:
        print(f"Error parsing FAQ HTML: {e}")
        return {}


def load_faqs() -> Dict[str, List[Dict[str, str]]]:
    """
    Load FAQs from cache or scrape if stale (lazy load)
    Cache is populated on first request, not on startup
    
    Returns:
        Dictionary mapping card names to FAQ entries
    """
    if is_cache_valid(CACHE_FILE, CACHE_TTL_HOURS):
        cached = load_cache(CACHE_FILE)
        if cached:
            print("Loading FAQs from cache")
            return cached['data']
    
    # Scrape fresh data (only when needed)
    print("Cache miss or expired - scraping fresh FAQ data...")
    faqs = scrape_all_faqs()
    
    if faqs:
        save_cache(CACHE_FILE, faqs)
        print(f"Cached FAQs for {len(faqs)} cards")
    
    return faqs


def get_card_faq(card_name: str, faqs: Dict[str, List[Dict[str, str]]]) -> Optional[List[Dict[str, str]]]:
    """
    Get FAQ entries for a specific card
    
    Args:
        card_name: Name of the card
        faqs: Dictionary of all FAQs
        
    Returns:
        List of FAQ entries, or None if card has no FAQs
    """
    return faqs.get(card_name)
