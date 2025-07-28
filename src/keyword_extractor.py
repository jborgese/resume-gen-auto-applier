import spacy

nlp = spacy.load("en_core_web_sm")

def extract_keywords(text: str) -> list:
    doc = nlp(text)
    keywords = [token.text for token in doc if token.is_alpha and not token.is_stop]
    return list(set(keywords))
# src/keyword_extractor.py