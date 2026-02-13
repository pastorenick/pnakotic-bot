"""
Generate vector embeddings for all Sorcery TCG cards
This script should be run once to pre-compute embeddings, and re-run when new cards are added
"""

import json
import os
from typing import Dict, List
from sentence_transformers import SentenceTransformer
import numpy as np


EMBEDDINGS_CACHE_FILE = "data/cache/embeddings.json"
CARDS_CACHE_FILE = "data/cache/cards.json"
MODEL_NAME = "all-MiniLM-L6-v2"  # Fast, lightweight, good for short texts


def create_card_description(card: Dict) -> str:
    """
    Create a text description of a card for embedding
    Focuses on abilities, type, and mechanics
    
    Args:
        card: Card dictionary
        
    Returns:
        Text description suitable for embedding
    """
    guardian = card.get('guardian', {})
    
    # Core info
    parts = []
    
    # Card type and subtypes
    card_type = guardian.get('type', '')
    if card_type:
        parts.append(f"{card_type}")
    
    sub_types = card.get('subTypes', '')
    if sub_types:
        parts.append(f"{sub_types}")
    
    # Elements
    elements = card.get('elements', '')
    if elements:
        parts.append(f"Element: {elements}")
    
    # Stats (for minions)
    attack = guardian.get('attack')
    defence = guardian.get('defence')
    if attack is not None and defence is not None:
        parts.append(f"Stats: {attack}/{defence}")
    
    # Rules text (most important for ability matching)
    rules_text = guardian.get('rulesText', '')
    if rules_text:
        # Clean up rules text (remove newlines, normalize)
        clean_text = ' '.join(rules_text.split())
        parts.append(clean_text)
    
    # Join all parts
    description = '. '.join(parts)
    
    return description


def load_cards() -> List[Dict]:
    """
    Load all cards from cache
    
    Returns:
        List of card dictionaries
    """
    if not os.path.exists(CARDS_CACHE_FILE):
        raise FileNotFoundError(
            f"Cards cache not found at {CARDS_CACHE_FILE}. "
            "Please run the bot once to populate the cache first."
        )
    
    with open(CARDS_CACHE_FILE, 'r', encoding='utf-8') as f:
        cache_data = json.load(f)
    
    return cache_data.get('data', [])


def generate_embeddings(cards: List[Dict], model: SentenceTransformer) -> Dict:
    """
    Generate embeddings for all cards
    
    Args:
        cards: List of card dictionaries
        model: Sentence transformer model
        
    Returns:
        Dict mapping card names to embeddings
    """
    print(f"Generating embeddings for {len(cards)} cards...")
    
    embeddings_data = {
        'model': MODEL_NAME,
        'embeddings': {}
    }
    
    # Create descriptions for all cards
    card_names = []
    descriptions = []
    
    for card in cards:
        name = card.get('name', '')
        if not name:
            continue
            
        description = create_card_description(card)
        card_names.append(name)
        descriptions.append(description)
    
    # Generate embeddings in batch (much faster than one-by-one)
    print("Encoding descriptions...")
    embeddings = model.encode(descriptions, show_progress_bar=True)
    
    # Store embeddings
    for name, embedding in zip(card_names, embeddings):
        # Convert numpy array to list for JSON serialization
        embeddings_data['embeddings'][name] = embedding.tolist()
    
    print(f"Generated {len(embeddings_data['embeddings'])} embeddings")
    
    return embeddings_data


def save_embeddings(embeddings_data: Dict):
    """
    Save embeddings to cache file
    
    Args:
        embeddings_data: Dict with model name and embeddings
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(EMBEDDINGS_CACHE_FILE), exist_ok=True)
    
    print(f"Saving embeddings to {EMBEDDINGS_CACHE_FILE}...")
    
    with open(EMBEDDINGS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(embeddings_data, f)
    
    print("Embeddings saved successfully!")


def main():
    """
    Main function to generate and save embeddings
    """
    print("=" * 60)
    print("Sorcery TCG Card Embeddings Generator")
    print("=" * 60)
    print()
    
    # Load model
    print(f"Loading model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded!")
    print()
    
    # Load cards
    cards = load_cards()
    print(f"Loaded {len(cards)} cards from cache")
    print()
    
    # Generate embeddings
    embeddings_data = generate_embeddings(cards, model)
    print()
    
    # Save to cache
    save_embeddings(embeddings_data)
    print()
    
    # Stats
    embedding_dim = len(next(iter(embeddings_data['embeddings'].values())))
    print("=" * 60)
    print("Summary:")
    print(f"  Cards processed: {len(embeddings_data['embeddings'])}")
    print(f"  Embedding dimension: {embedding_dim}")
    print(f"  Model: {MODEL_NAME}")
    print("=" * 60)


if __name__ == '__main__':
    main()
