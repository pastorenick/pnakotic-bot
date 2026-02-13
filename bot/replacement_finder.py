"""
Card replacement recommendation engine for Sorcery TCG
Finds similar cards based on abilities, elements, and mana cost
Uses vector embeddings for semantic similarity when available
"""

import re
import os
import json
from typing import Dict, List, Tuple, Optional
from fuzzywuzzy import fuzz
import numpy as np


# Common Sorcery keywords and abilities (for extraction)
KEYWORDS = [
    # Combat abilities
    'airborne', 'burrowing', 'ephemeral', 'flying', 'stealthy', 'unblockable',
    'ambush', 'blitz', 'bloodlust', 'deadly', 'double strike', 'first strike',
    'lifesteal', 'rampage', 'reach', 'vigilant', 'waterbound',
    
    # Protection/Resistance
    'protected', 'shroud', 'ward', 'hexproof', 'indestructible',
    
    # Triggered abilities
    'genesis', 'demise', 'clash', 'breakthrough', 'strike',
    
    # Card types
    'spellcaster', 'ritual', 'aura', 'rune', 'cursed', 'item',
    
    # Mechanics
    'draw', 'discard', 'destroy', 'exile', 'return', 'bounce',
    'token', 'transform', 'morph', 'rubble', 'reanimate',
    'search', 'tutor', 'sacrifice', 'conjure', 'manifest',
    
    # Counters/Buffs
    'counter', '+1/+1', '-1/-1', 'buff', 'debuff', 'pump',
    
    # Targeting
    'target', 'each', 'all', 'choose', 'random',
    
    # Duration
    'permanent', 'turn', 'until end of turn', 'enters the battlefield'
]


def extract_keywords(rules_text: str) -> List[str]:
    """
    Extract keywords and abilities from card rules text
    
    Args:
        rules_text: Card's rulesText field
        
    Returns:
        List of normalized keywords found
    """
    if not rules_text:
        return []
    
    text_lower = rules_text.lower()
    found_keywords = []
    
    # Extract exact keyword matches
    for keyword in KEYWORDS:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    # Extract custom patterns
    # Genesis/Demise abilities
    if re.search(r'genesis\s*[→\-]', text_lower):
        found_keywords.append('genesis_trigger')
    if re.search(r'demise\s*[→\-]', text_lower):
        found_keywords.append('demise_trigger')
    
    # Draw effects
    if re.search(r'draw\s+\d+', text_lower):
        found_keywords.append('card_draw')
    if re.search(r'draw\s+a\s+(card|spell)', text_lower):
        found_keywords.append('card_draw')
    
    # Damage effects
    if re.search(r'deal[s]?\s+\d+\s+damage', text_lower):
        found_keywords.append('direct_damage')
    
    # Buff/debuff effects
    if re.search(r'[\+\-]\d+/[\+\-]\d+', text_lower):
        found_keywords.append('stat_modification')
    
    # Mana/cost manipulation
    if re.search(r'cost[s]?\s+\d+\s+less', text_lower):
        found_keywords.append('cost_reduction')
    
    # Search/tutor
    if 'search' in text_lower or 'look at' in text_lower:
        found_keywords.append('search_effect')
    
    return list(set(found_keywords))  # Remove duplicates


def load_embeddings() -> Optional[Dict]:
    """
    Load pre-computed card embeddings from cache
    
    Returns:
        Dict with 'model' and 'embeddings' keys, or None if not available
    """
    EMBEDDINGS_CACHE_FILE = "data/cache/embeddings.json"
    
    if not os.path.exists(EMBEDDINGS_CACHE_FILE):
        return None
    
    try:
        with open(EMBEDDINGS_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load embeddings: {e}")
        return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def get_card_stats(card: Dict) -> Dict:
    """
    Extract relevant stats from card for matching
    
    Args:
        card: Card dictionary
        
    Returns:
        Dict with normalized stats
    """
    guardian = card.get('guardian', {})
    
    return {
        'name': card.get('name', ''),
        'type': guardian.get('type', ''),
        'cost': guardian.get('cost'),
        'attack': guardian.get('attack'),
        'defence': guardian.get('defence'),
        'rarity': guardian.get('rarity', ''),
        'elements': card.get('elements', ''),
        'sub_types': card.get('subTypes', ''),
        'thresholds': guardian.get('thresholds', {}),
        'rules_text': guardian.get('rulesText', ''),
        'keywords': extract_keywords(guardian.get('rulesText', ''))
    }


def calculate_similarity_score(
    source_stats: Dict,
    candidate_stats: Dict,
    embeddings_data: Optional[Dict] = None
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate similarity score between two cards
    
    Uses vector embeddings if available, falls back to keyword matching
    
    Scoring weights (when using embeddings):
    - Vector similarity: 70% (primary - semantic understanding)
    - Element/thresholds: 20% (secondary)
    - Mana cost: 10% (bonus)
    
    Scoring weights (keyword fallback):
    - Keywords/abilities: 50% (primary)
    - Element/thresholds: 25% (secondary)
    - Mana cost: 15% (secondary)
    - Card type: 10% (bonus)
    
    Args:
        source_stats: Stats of the card to replace
        candidate_stats: Stats of potential replacement
        embeddings_data: Optional pre-loaded embeddings dict
        
    Returns:
        Tuple of (total_score, score_breakdown)
    """
    # Try vector similarity first if embeddings available
    if embeddings_data is not None:
        return _calculate_vector_similarity(source_stats, candidate_stats, embeddings_data)
    
    # Fallback to keyword-based similarity
    return _calculate_keyword_similarity(source_stats, candidate_stats)


def _calculate_vector_similarity(
    source_stats: Dict,
    candidate_stats: Dict,
    embeddings_data: Dict
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate similarity using vector embeddings
    
    Args:
        source_stats: Stats of the card to replace
        candidate_stats: Stats of potential replacement
        embeddings_data: Pre-loaded embeddings dict
        
    Returns:
        Tuple of (total_score, score_breakdown)
    """
    scores = {
        'vector': 0.0,
        'elements': 0.0,
        'cost': 0.0,
        'type': 0.0
    }
    
    # 1. VECTOR SIMILARITY (70% weight) - Primary criterion
    source_name = source_stats['name']
    candidate_name = candidate_stats['name']
    
    embeddings = embeddings_data.get('embeddings', {})
    source_vec = embeddings.get(source_name)
    candidate_vec = embeddings.get(candidate_name)
    
    if source_vec and candidate_vec:
        similarity = cosine_similarity(source_vec, candidate_vec)
        scores['vector'] = similarity * 70.0  # Convert to 0-70 scale
    else:
        # If embeddings missing, return low score to trigger fallback
        return 0.0, scores
    
    # 2. ELEMENTS/THRESHOLDS (20% weight) - Secondary criterion
    source_elem = source_stats['elements']
    candidate_elem = candidate_stats['elements']
    
    # Exact element match
    if source_elem == candidate_elem:
        scores['elements'] = 12.0
    elif source_elem and candidate_elem:
        # Partial element match
        source_elems = set(source_elem.split('/'))
        candidate_elems = set(candidate_elem.split('/'))
        overlap = len(source_elems & candidate_elems) / max(len(source_elems), len(candidate_elems))
        scores['elements'] += overlap * 12.0
    
    # Threshold similarity (8% of total)
    source_thresh = source_stats['thresholds']
    candidate_thresh = candidate_stats['thresholds']
    
    if source_thresh and candidate_thresh:
        total_diff = sum(abs(source_thresh.get(elem, 0) - candidate_thresh.get(elem, 0)) 
                        for elem in ['air', 'earth', 'fire', 'water'])
        # Lower diff = higher score (max 8 points)
        thresh_score = max(0, 8 - total_diff * 1.5)
        scores['elements'] += thresh_score
    
    # 3. MANA COST (10% weight) - Bonus
    source_cost = source_stats['cost']
    candidate_cost = candidate_stats['cost']
    
    if source_cost is not None and candidate_cost is not None:
        cost_diff = abs(source_cost - candidate_cost)
        if cost_diff == 0:
            scores['cost'] = 10.0
        elif cost_diff == 1:
            scores['cost'] = 7.0
        elif cost_diff == 2:
            scores['cost'] = 3.0
    
    total_score = sum(scores.values())
    
    return total_score, scores


def _calculate_keyword_similarity(
    source_stats: Dict,
    candidate_stats: Dict
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate similarity using keyword matching (fallback method)
    
    Args:
        source_stats: Stats of the card to replace
        candidate_stats: Stats of potential replacement
        
    Returns:
        Tuple of (total_score, score_breakdown)
    """
    scores = {
        'keywords': 0.0,
        'elements': 0.0,
        'cost': 0.0,
        'type': 0.0
    }
    
    # 1. KEYWORDS (50% weight) - Primary criterion
    source_keywords = set(source_stats['keywords'])
    candidate_keywords = set(candidate_stats['keywords'])
    
    if source_keywords and candidate_keywords:
        # Jaccard similarity: intersection / union
        intersection = len(source_keywords & candidate_keywords)
        union = len(source_keywords | candidate_keywords)
        scores['keywords'] = (intersection / union) * 100 * 0.50
    elif not source_keywords and not candidate_keywords:
        # Both have no keywords - perfect match
        scores['keywords'] = 50.0
    else:
        # One has keywords, other doesn't - use fuzzy text match
        source_text = source_stats['rules_text'].lower()
        candidate_text = candidate_stats['rules_text'].lower()
        text_similarity = fuzz.partial_ratio(source_text, candidate_text)
        scores['keywords'] = (text_similarity / 100) * 50.0
    
    # 2. ELEMENTS/THRESHOLDS (25% weight) - Secondary criterion
    source_elem = source_stats['elements']
    candidate_elem = candidate_stats['elements']
    
    # Exact element match
    if source_elem == candidate_elem:
        scores['elements'] = 15.0
    elif source_elem and candidate_elem:
        # Partial element match (e.g., "Fire/Water" vs "Fire")
        source_elems = set(source_elem.split('/'))
        candidate_elems = set(candidate_elem.split('/'))
        overlap = len(source_elems & candidate_elems) / max(len(source_elems), len(candidate_elems))
        scores['elements'] += overlap * 15.0
    
    # Threshold similarity (10% of total)
    source_thresh = source_stats['thresholds']
    candidate_thresh = candidate_stats['thresholds']
    
    if source_thresh and candidate_thresh:
        total_diff = sum(abs(source_thresh.get(elem, 0) - candidate_thresh.get(elem, 0)) 
                        for elem in ['air', 'earth', 'fire', 'water'])
        # Lower diff = higher score (max 10 points)
        thresh_score = max(0, 10 - total_diff * 2)
        scores['elements'] += thresh_score
    
    # 3. MANA COST (15% weight) - Secondary criterion
    source_cost = source_stats['cost']
    candidate_cost = candidate_stats['cost']
    
    if source_cost is not None and candidate_cost is not None:
        cost_diff = abs(source_cost - candidate_cost)
        if cost_diff == 0:
            scores['cost'] = 15.0
        elif cost_diff == 1:
            scores['cost'] = 10.0  # ±1 is acceptable
        elif cost_diff == 2:
            scores['cost'] = 5.0
        # else: 0 points
    
    # 4. CARD TYPE (10% bonus)
    if source_stats['type'] == candidate_stats['type']:
        scores['type'] = 10.0
    
    total_score = sum(scores.values())
    
    return total_score, scores


def find_replacements(
    target_card_name: str,
    all_cards: List[Dict],
    max_results: int = 3,
    min_score: float = 30.0,
    use_embeddings: bool = True
) -> List[Dict]:
    """
    Find replacement cards for a given card
    
    Args:
        target_card_name: Name of card to replace
        all_cards: List of all available cards
        max_results: Maximum number of recommendations to return
        min_score: Minimum similarity score (0-100)
        use_embeddings: Whether to use vector embeddings (falls back if unavailable)
        
    Returns:
        List of replacement card dicts with scores
    """
    # Find the target card
    target_card = next((c for c in all_cards if c['name'].lower() == target_card_name.lower()), None)
    
    if not target_card:
        return []
    
    target_stats = get_card_stats(target_card)
    
    # Load embeddings if requested
    embeddings_data = None
    if use_embeddings:
        embeddings_data = load_embeddings()
        if embeddings_data:
            print(f"Using vector embeddings (model: {embeddings_data.get('model')})")
        else:
            print("Embeddings not available, falling back to keyword matching")
    
    # Calculate scores for all other cards
    candidates = []
    
    for card in all_cards:
        # Skip the target card itself
        if card['name'] == target_card['name']:
            continue
        
        candidate_stats = get_card_stats(card)
        score, breakdown = calculate_similarity_score(
            target_stats, 
            candidate_stats,
            embeddings_data
        )
        
        # If vector similarity failed (score=0 with embeddings), try keyword fallback
        if embeddings_data and score == 0.0:
            score, breakdown = _calculate_keyword_similarity(target_stats, candidate_stats)
        
        if score >= min_score:
            candidates.append({
                'card': card,
                'score': score,
                'breakdown': breakdown,
                'stats': candidate_stats
            })
    
    # Sort by score (highest first)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    return candidates[:max_results]


def format_replacement_explanation(target_card: Dict, replacement: Dict) -> str:
    """
    Format explanation of why a card is a good replacement
    
    Args:
        target_card: Original card
        replacement: Replacement candidate with score data
        
    Returns:
        Formatted explanation string
    """
    card = replacement['card']
    score = replacement['score']
    breakdown = replacement['breakdown']
    stats = replacement['stats']
    
    lines = [f"*{card['name']}* (Match: {score:.0f}%)"]
    
    # Cost and type
    cost = stats['cost'] if stats['cost'] is not None else 'N/A'
    lines.append(f"• {stats['type']} - Cost: {cost}")
    
    # Stats (for minions)
    if stats['attack'] is not None and stats['defence'] is not None:
        lines.append(f"• {stats['attack']}/{stats['defence']}")
    
    # Element
    if stats['elements']:
        lines.append(f"• Elements: {stats['elements']}")
    
    # Why it matches
    reasons = []
    
    # Check if using vector or keyword scoring
    if 'vector' in breakdown:
        # Vector-based matching
        if breakdown['vector'] > 45:  # > 64% similarity (45/70)
            reasons.append("very similar abilities")
        elif breakdown['vector'] > 30:  # > 43% similarity (30/70)
            reasons.append("similar abilities")
    else:
        # Keyword-based matching
        if breakdown.get('keywords', 0) > 20:
            reasons.append("similar abilities")
    
    if breakdown.get('elements', 0) > 10:
        reasons.append("same element")
    if breakdown.get('cost', 0) >= 7:
        reasons.append("similar cost")
    
    if reasons:
        lines.append(f"• Match: {', '.join(reasons)}")
    
    return '\n'.join(lines)
