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
from config import GROQ_API_KEY, LLM_MODEL, MAX_TOOL_ROUNDS
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

_client = Groq(api_key=GROQ_API_KEY)

# ── Tool 1: search_listings ───────────────────────────────────────────────────
# def cache_desc():
#     dict = {}
#     listings = load_listings
#     for desc in listings["description"]:
        
#         sorted_desc = sorted(desc.lower().split(""))
#         dict[desc] = sorted_desc
#     return sorted_desc

# _CACHED_DESC = cache_desc

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # Replace this with your implementation
    listings = load_listings()
    score = {}
    if max_price:
        listings = [item for item in listings if item["price"] <= max_price]

    # Filter by size if size is provided
    if size:
        listings = [item for item in listings if item["size"] == size]
    
    search_keywords = set(description.lower().split())
    
    scored_listings = []
    
    # 3. Score each remaining listing
    for item in listings:
        # Turn the item's description into a list of lowercase words
        desc_words = item["description"].lower().split()
        
        # Count how many search keywords appear in this description
        score = sum(1 for word in desc_words if word in search_keywords)
        
        # 4. Drop any listings with a score of 0
        if score > 0:
            # Dynamically inject the score into the dictionary so we can sort by it
            item_with_score = item.copy()
            item_with_score["score"] = score
            scored_listings.append(item_with_score)
            
    # 5. Sort by score, highest first
    # lambda x: x["score"] tells Python to sort using the score value
    scored_listings.sort(key=lambda x: x["score"], reverse=True)

    return scored_listings


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Replace this with your implementation
    wardrobe_items = wardrobe.get('items', [])
    
    # 1. New item uses 'title' from _listings.json
    item_title = new_item.get('title', 'this item')
    item_brand = new_item.get('brand') or 'Unknown Brand'
    if not wardrobe_items: 
        # 2. Empty Wardrobe Prompt
        prompt = f"The user is considering buying this item: {item_title} by brand: {item_brand}. Their wardrobe is empty. Provide general styling advice, what kinds of items pair well, and what vibe it suits."
    else:
        # 3. Format the wardrobe items into a readable string
        wardrobe_lines = []
        for item in wardrobe_items:
            w_name = item.get('name', 'Unnamed Piece')
            w_cat = item.get('category', 'clothing')
            wardrobe_lines.append(f"- {w_name} ({w_cat})")
            
        wardrobe_str = "\n".join(wardrobe_lines)
        
        prompt = f"""
            The user is considering buying: {item_title} (Brand: {item_brand}).
            
            Suggest 1 to 2 complete outfits styling this new item by pairing it with specific pieces from their current wardrobe listed below:
            {wardrobe_str}
            
            Be specific about which wardrobe items to pick and describe the resulting outfit vibe.
        """

    # Connect to Groq API
    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,  
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert personal fashion stylist. Give clear, concise outfit suggestions."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.7
        )
        
        # 4. Return the LLM's response as a string
        return response.choices[0].message.content

    except Exception as e:
        # Graceful fallback if the API call fails
        print(f"Groq API Error: {e}")
        return f"Styling advice is currently unavailable, but that {new_item['brand']} item looks great!"


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Replace this with your implementation
    if not outfit or not outfit.strip():
        return "Error: Cannot generate a caption because no outfit suggestion was provided."

    # Extract details for easy prompt integration
    item_title = new_item.get("title", "this thrifted find")
    price = new_item.get("price", "thrifted price")
    platform = new_item.get("platform", "online")

    # 2. Build a prompt detailing the item information and style requirements
    prompt = f"""
        Create a short, shareable social media caption (Instagram/TikTok style) for an outfit.

        Item Details:
        - Item Name: {item_title}
        - Price: ${price}
        - Platform: {platform}
        
        Outfit Concept:
        {outfit}

        Strict Rules:
        1. Keep it brief: exactly 2 to 4 sentences total.
        2. Feel casual, enthusiastic, and authentic—like a real person posting an OOTD, not an advertisement.
        3. Naturally mention the item name, price (include '$'), and platform exactly once each. 
        4. Focus on capturing the specific vibe of the outfit.
        5. Do not include meta-text, markdown tags, hashtags, or emoji placeholders like '[emoji]'. Real emojis are fine.
    """

    # 3. Call the LLM with a higher temperature for natural variety
    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a trendsetting social media manager specializing in fashion, streetwear, and thrifting content."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.95  # Higher temperature makes the captions sound different each time
        )
        
        return response.choices[0].message.content.strip()

    except Exception as e:
        # Gracefully handle API errors without raising an exception
        print(f"Groq API Error in create_fit_card: {e}")
        return f"Just styled this amazing {item_title} I found on {platform} for only ${price}! Loving how it completes the vibe."