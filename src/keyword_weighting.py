# src/keyword_weighting.py
import json
import os

# Load category weights
with open(os.path.join(os.path.dirname(__file__), "keyword_weights.json")) as f:
    KEYWORD_WEIGHTS = json.load(f)

def weigh_keywords(description: str, keywords: list) -> list:
    """
    Assigns weights to extracted keywords based on frequency and category boost.
    Returns a sorted list of (keyword, score) tuples from highest to lowest weight.
    """

    lower_desc = description.lower()
    weighted_list = []

    for kw in keywords:
        freq = lower_desc.count(kw.lower())
        bonus = 0

        if kw in KEYWORD_WEIGHTS.get("tech", []):
            bonus = 2
        elif kw in KEYWORD_WEIGHTS.get("methodology", []):
            bonus = 1
        # soft skills (bonus = 0) get no boost

        score = (freq * 2) + bonus
        weighted_list.append((kw, score))

    # Sort by score descending
    return sorted(weighted_list, key=lambda x: x[1], reverse=True)
