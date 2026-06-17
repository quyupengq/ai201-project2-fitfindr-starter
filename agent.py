"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.
    """
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


# ── query parsing helpers ─────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from a natural language query.

    This parser is intentionally simple and rule-based:
    - price comes from patterns like "under $30", "below 30", or "$30"
    - size comes from patterns like "size M" or "size XXS"
    - description is the remaining cleaned query
    """
    original_query = query
    cleaned = query.lower()

    max_price = None
    size = None

    # Find max price: "under $30", "below 30", "max $25", "$30"
    price_match = re.search(
        r"(?:under|below|max|maximum|less than)\s*\$?\s*(\d+(?:\.\d+)?)",
        cleaned,
    )

    if not price_match:
        price_match = re.search(r"\$(\d+(?:\.\d+)?)", cleaned)

    if price_match:
        max_price = float(price_match.group(1))
        cleaned = cleaned.replace(price_match.group(0), " ")

    # Find size: "size M", "size XXS", etc.
    size_match = re.search(
        r"\bsize\s+([a-z0-9/.\-]+)",
        cleaned,
        flags=re.IGNORECASE,
    )

    if size_match:
        size = size_match.group(1).upper()
        cleaned = cleaned.replace(size_match.group(0), " ")

    # Remove common phrases safely
    phrase_patterns = [
        r"\bi'?m looking for\b",
        r"\bim looking for\b",
        r"\blooking for\b",
        r"\bi want\b",
        r"\bfind me\b",
        r"\bshow me\b",
        r"\bwhat'?s out there\b",
        r"\bwhats out there\b",
        r"\bhow would i style it\b",
        r"\bhow to style it\b",
        r"\bhow would i wear it\b",
        r"\bi mostly wear\b",
        r"\bmostly wear\b",
    ]

    description = cleaned

    for pattern in phrase_patterns:
        description = re.sub(pattern, " ", description)

    # Remove standalone filler words only, not letters inside words
    description = re.sub(r"\b(a|an|the|and|or|with)\b", " ", description)

    # Remove punctuation
    description = re.sub(r"[^a-z0-9\s/\-]", " ", description)

    # Collapse extra spaces
    description = " ".join(description.split())

    if not description:
        description = original_query

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }
# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for one interaction.

    The agent:
    1. Parses the query.
    2. Searches listings.
    3. Stops early if no listings are found.
    4. Stores the selected item in session state.
    5. Suggests an outfit.
    6. Creates a fit card.
    7. Returns the final session dictionary.
    """
    session = _new_session(query, wardrobe)

    parsed = _parse_query(query)
    session["parsed"] = parsed

    description = parsed["description"]
    size = parsed["size"]
    max_price = parsed["max_price"]

    search_results = search_listings(
        description=description,
        size=size,
        max_price=max_price,
    )

    session["search_results"] = search_results

    if not search_results:
        session["error"] = (
            "I couldn't find any listings matching that exact request. "
            "Try raising your max price, removing the size filter, or using a broader description."
        )
        return session

    selected_item = search_results[0]
    session["selected_item"] = selected_item

    outfit_suggestion = suggest_outfit(selected_item, wardrobe)
    session["outfit_suggestion"] = outfit_suggestion

    if not outfit_suggestion or not outfit_suggestion.strip():
        session["error"] = (
            "I found an item, but I couldn't generate an outfit suggestion for it."
        )
        return session

    fit_card = create_fit_card(outfit_suggestion, selected_item)
    session["fit_card"] = fit_card

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )

    print("Parsed:", session["parsed"])

    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )

    print("Parsed:", session2["parsed"])
    print(f"Error message: {session2['error']}")
    print(f"Selected item: {session2['selected_item']}")
    print(f"Fit card: {session2['fit_card']}")