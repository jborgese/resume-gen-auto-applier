def clean_text(text: str) -> str:
    """Normalize scraped text by removing excessive newlines and trimming spaces."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines)
