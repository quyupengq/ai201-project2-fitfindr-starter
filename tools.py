"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

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


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    listings = load_listings()

    if not description or not description.strip():
        return []

    keywords = description.lower().split()
    scored_results = []

    for item in listings:
        # Price filter
        if max_price is not None and item.get("price", 0) > max_price:
            continue

        # Size filter
        if size:
            item_size = str(item.get("size", "")).lower()
            requested_size = size.lower()

            if requested_size not in item_size:
                continue

        searchable_text = " ".join([
            str(item.get("title", "")),
            str(item.get("description", "")),
            str(item.get("category", "")),
            " ".join(item.get("style_tags", [])),
            " ".join(item.get("colors", [])),
            str(item.get("brand", "")),
            str(item.get("platform", "")),
        ]).lower()

        score = 0
        for word in keywords:
            if word in searchable_text:
                score += 1

        if score > 0:
            scored_results.append((score, item))

    scored_results.sort(key=lambda pair: pair[0], reverse=True)

    return [item for score, item in scored_results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    if not new_item:
        return "I couldn't suggest an outfit because no thrifted item was selected."

    client = _get_groq_client()

    item_title = new_item.get("title", "this thrifted item")
    item_description = new_item.get("description", "")
    item_colors = ", ".join(new_item.get("colors", []))
    item_tags = ", ".join(new_item.get("style_tags", []))

    wardrobe_items = wardrobe.get("items", []) if wardrobe else []

    if not wardrobe_items:
        prompt = f"""
You are FitFindr, a helpful secondhand fashion styling assistant.

The user is considering this thrifted item:
- Title: {item_title}
- Description: {item_description}
- Colors: {item_colors}
- Style tags: {item_tags}

The user's wardrobe is empty or not provided.

Give 1 practical outfit idea using common wardrobe basics.
Make it specific, casual, and useful.
Do not say you cannot help.
Keep it under 120 words.
"""
    else:
        formatted_wardrobe = []
        for piece in wardrobe_items:
            formatted_wardrobe.append(
                f"- {piece.get('name', piece.get('title', 'Unnamed item'))}: "
                f"{piece.get('category', 'unknown category')}, "
                f"colors: {', '.join(piece.get('colors', []))}, "
                f"style: {', '.join(piece.get('style_tags', []))}"
            )

        wardrobe_text = "\n".join(formatted_wardrobe)

        prompt = f"""
You are FitFindr, a helpful secondhand fashion styling assistant.

The user is considering this thrifted item:
- Title: {item_title}
- Description: {item_description}
- Colors: {item_colors}
- Style tags: {item_tags}

The user's wardrobe:
{wardrobe_text}

Suggest 1 complete outfit using the thrifted item and specific pieces from the wardrobe when possible.
Explain the vibe briefly.
Keep it casual and under 140 words.
"""

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

    if not result:
        return "I couldn't generate a specific outfit, but this item would work well with simple basics and neutral layers."

    return result

# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    if not outfit or not outfit.strip():
        return "I couldn't create a fit card because there was no outfit suggestion to summarize."

    if not new_item:
        return "I couldn't create a fit card because no thrifted item was selected."

    client = _get_groq_client()

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

    if not result:
        return f"Styled the {item_title} from {item_platform} for ${item_price} into an easy thrifted fit."

    return result