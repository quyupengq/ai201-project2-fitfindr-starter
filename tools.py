"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Helper functions ──────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """Turn text into lowercase searchable words."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _format_list(values) -> str:
    """Safely format a list field like colors or style_tags."""
    if not values:
        return ""
    if isinstance(values, list):
        return ", ".join(str(v) for v in values)
    return str(values)


def _fallback_outfit(new_item: dict) -> str:
    """Simple backup outfit response if the LLM is unavailable."""
    title = new_item.get("title", "this thrifted item")
    colors = _format_list(new_item.get("colors", []))
    tags = _format_list(new_item.get("style_tags", []))

    return (
        f"Style the {title} with relaxed jeans, simple sneakers, and a clean outer layer "
        f"like a denim jacket, hoodie, or flannel. The colors ({colors}) and vibe ({tags}) "
        f"make it easy to build a casual thrifted outfit without overthinking it."
    )


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Returns:
        A list of matching listing dicts, sorted by relevance.
        Returns [] if nothing matches.
    """
    listings = load_listings()

    if not description or not description.strip():
        return []

    keywords = _tokenize(description)

    if not keywords:
        return []

    if max_price is not None:
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = None

    scored_results = []

    for item in listings:
        price = item.get("price", 0)

        if max_price is not None and price > max_price:
            continue

        if size:
            requested_size = str(size).lower().strip()
            item_size = str(item.get("size", "")).lower()

            if requested_size not in item_size:
                continue

        searchable_text = " ".join(
            [
                str(item.get("title", "")),
                str(item.get("description", "")),
                str(item.get("category", "")),
                _format_list(item.get("style_tags", [])),
                _format_list(item.get("colors", [])),
                str(item.get("brand", "")),
                str(item.get("platform", "")),
            ]
        ).lower()

        searchable_tokens = set(_tokenize(searchable_text))

        score = 0

        for word in keywords:
            if word in searchable_tokens:
                score += 2
            elif word in searchable_text:
                score += 1

        if description.lower().strip() in searchable_text:
            score += 5

        if score > 0:
            scored_results.append((score, price, item))

    scored_results.sort(key=lambda result: (-result[0], result[1]))

    return [item for score, price, item in scored_results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest an outfit.

    Returns:
        A non-empty string with an outfit suggestion.
        Handles empty wardrobes gracefully.
    """
    if not new_item:
        return "I couldn't suggest an outfit because no thrifted item was selected."

    item_title = new_item.get("title", "this thrifted item")
    item_description = new_item.get("description", "")
    item_colors = _format_list(new_item.get("colors", []))
    item_tags = _format_list(new_item.get("style_tags", []))
    item_price = new_item.get("price", "unknown price")
    item_platform = new_item.get("platform", "a secondhand platform")

    wardrobe_items = wardrobe.get("items", []) if wardrobe else []

    if wardrobe_items:
        formatted_wardrobe = []
        for piece in wardrobe_items:
            formatted_wardrobe.append(
                f"- {piece.get('name', piece.get('title', 'Unnamed item'))}: "
                f"{piece.get('category', 'unknown category')}, "
                f"colors: {_format_list(piece.get('colors', []))}, "
                f"style: {_format_list(piece.get('style_tags', []))}"
            )

        wardrobe_text = "\n".join(formatted_wardrobe)

        prompt = f"""
You are FitFindr, a helpful secondhand fashion styling assistant.

The user is considering this thrifted item:
- Title: {item_title}
- Description: {item_description}
- Price: ${item_price}
- Platform: {item_platform}
- Colors: {item_colors}
- Style tags: {item_tags}

The user's wardrobe:
{wardrobe_text}

Suggest 1 complete outfit using the thrifted item and specific pieces from the wardrobe when possible.
Explain the vibe briefly.
Keep it casual, specific, and under 140 words.
"""
    else:
        prompt = f"""
You are FitFindr, a helpful secondhand fashion styling assistant.

The user is considering this thrifted item:
- Title: {item_title}
- Description: {item_description}
- Price: ${item_price}
- Platform: {item_platform}
- Colors: {item_colors}
- Style tags: {item_tags}

The user's wardrobe is empty or not provided.

Give 1 practical outfit idea using common wardrobe basics.
Make it specific, casual, and useful.
Do not say you cannot help.
Keep it under 120 words.
"""

    try:
        client = _get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a concise secondhand fashion stylist.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.7,
            max_tokens=220,
        )

        result = response.choices[0].message.content.strip()

        if result:
            return result

    except Exception:
        pass

    return _fallback_outfit(new_item)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Returns:
        A short caption string.
        If outfit is empty, returns a descriptive error message.
    """
    if not outfit or not outfit.strip():
        return "I couldn't create a fit card because there was no outfit suggestion to summarize."

    if not new_item:
        return "I couldn't create a fit card because no thrifted item was selected."

    item_title = new_item.get("title", "thrifted piece")
    item_price = new_item.get("price", "unknown price")
    item_platform = new_item.get("platform", "a secondhand platform")
    item_condition = new_item.get("condition", "secondhand")

    prompt = f"""
Create a short social media outfit caption.

Thrifted item:
- Title: {item_title}
- Price: ${item_price}
- Platform: {item_platform}
- Condition: {item_condition}

Outfit idea:
{outfit}

Requirements:
- 2 to 4 short sentences
- casual and authentic
- mention the item title, price, and platform naturally once
- do not sound like a product description
- okay to use 1 emoji
- no hashtags
"""

    try:
        client = _get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You write casual outfit captions that sound natural and specific.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=1.0,
            max_tokens=180,
        )

        result = response.choices[0].message.content.strip()

        if result:
            return result

    except Exception:
        pass

    return (
        f"Found the {item_title} on {item_platform} for ${item_price} and built the fit around it. "
        f"{outfit}"
    )
