# src/keyword_extractor.py
import json
import spacy
from pathlib import Path
from src.logging_config import get_logger, debug_stop, debug_checkpoint, debug_skip_stops

logger = get_logger(__name__)

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
    # Debug checkpoint at function start
    debug_checkpoint("extract_keywords_start", 
                    description_length=len(description),
                    tech_dict_categories=len(TECH_DICT),
                    stopwords_count=len(STOPWORDS))
    
    # Debug stop before keyword extraction
    if not debug_skip_stops():
        debug_stop("About to extract keywords from job description", 
                  description_length=len(description),
                  description_preview=description[:200] + "..." if len(description) > 200 else description)
    
    found_keywords = set()

    # ✅ 1. Match dictionary terms (case-insensitive) - no length filter for dictionary terms
    lower_desc = description.lower()
    for category, terms in TECH_DICT.items():
        for term in terms:
            if term.lower() in lower_desc:
                found_keywords.add(term)

    # Debug checkpoint after dictionary matching
    debug_checkpoint("dictionary_matching_complete", 
                    dictionary_keywords_found=len(found_keywords))

    # ✅ 2. Use spaCy to find extra nouns/entities - apply minimum length filter
    doc = nlp(description)
    for token in doc:
        # Grab potential skills (proper nouns & acronyms)
        if token.pos_ in ["PROPN", "NOUN"] and len(token.text) > 2:
            term_lower = token.text.lower()
            # ✅ Filter out generic terms
            if term_lower not in STOPWORDS:
                found_keywords.add(token.text)

    # Debug checkpoint at function end
    debug_checkpoint("extract_keywords_complete", 
                    total_keywords=len(found_keywords),
                    keywords_preview=list(found_keywords)[:10])

    return sorted(found_keywords)
