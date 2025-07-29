# src/keyword_extractor.py
import json
import spacy
from pathlib import Path

# Load spaCy model once
nlp = spacy.load("en_core_web_sm")

# ✅ Load tech dictionary JSON
with open(Path(__file__).parent / "tech_dictionary.json", "r") as f:
    TECH_DICT = json.load(f)

# ✅ Load stopwords JSON
with open(Path(__file__).parent / "stopwords.json", "r") as f:
    STOPWORDS = set(json.load(f)["stopwords"])

def extract_keywords(description: str):
    """Return a list of relevant keywords from the description."""
    found_keywords = set()

    # ✅ 1. Match dictionary terms (case-insensitive)
    lower_desc = description.lower()
    for category, terms in TECH_DICT.items():
        for term in terms:
            if term.lower() in lower_desc:
                found_keywords.add(term)

    # ✅ 2. Use spaCy to find extra nouns/entities
    doc = nlp(description)
    for token in doc:
        # Grab potential skills (proper nouns & acronyms)
        if token.pos_ in ["PROPN", "NOUN"] and len(token.text) > 2:
            term_lower = token.text.lower()
            # ✅ Filter out generic terms
            if term_lower not in STOPWORDS:
                found_keywords.add(token.text)

    return sorted(found_keywords)
