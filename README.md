# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

---

## Interaction Walkthrough

<!-- Walk through a complete interaction step by step: natural language query → each tool call (and why) → final fit card.
     Walk through this carefully — it's how graders follow your agent's reasoning without a live demo.
     Use a specific example — do not leave this as a template. -->

**User query:** "looking for a 90s track jacket in size M"

**Step 1 — Tool called:**
- Tool: search_listings
- Input:max_price (float/int or None), size (str or None), description (str)
- Why this tool: To find all available listing that best match the requested description style.
- Output: 🔥 TOP MATCH FOUND!

        📌 Title: 90s Track Jacket — Navy/White Stripe
        🏷️ Brand: Champion
        💰 Price: $45.0
        📏 Size: M
        🎨 Colors: navy, white
        📲 Platform: POSHMARK
        ✨ Match Score: 3

        📝 Description:
        Authentic 90s track jacket with stripe detail down the sleeves. Full zip. Lightweight — great for layering.

**Step 2 — Tool called:**
- Tool: suggest_outfit
- Input: new_item='', wardrobe={}
- Why this tool: To create a full outfit look by combining the discovered thrift store item with actual clothing pieces currently inside the user's closet.
- Output: To style the 90s Track Jacket — Navy/White Stripe from Champion, I suggest two complete outfits:

**Outfit 1: Casual Streetwear**
Pair the 90s Track Jacket with the baggy straight-leg jeans (dark wash) and chunky white sneakers. Add the white ribbed tank top underneath the jacket for a layered look. Finish the outfit with the brown leather belt and black crossbody bag for a relaxed, casual vibe that's perfect for everyday wear. This outfit exudes a classic 90s streetwear feel with a modern twist.

**Outfit 2: Sporty Chic**
Combine the 90s Track Jacket with the wide-leg khaki trousers and black combat boots for a sporty yet stylish ensemble. Layer the oversized grey crewneck sweatshirt under the jacket for a cozy touch. This outfit has a great balance of sporty and chic elements, making it ideal for a casual day out or a low-key evening event. The contrast between the navy/white stripe jacket and the khaki trousers adds a nice visual interest to the overall look.

**Step 3 — Tool called:**
- Tool: create_fit_card
- Input: outfit, new_item, price, platform 
- Why this tool: To take the generated style suggestions and turn them into a short, upbeat, ready-to-post caption for social media.
- Output: I'm loving this casual streetwear vibe I've got going on today, all thanks to my new 90s Track Jacket — Navy/White Stripe from Poshmark for $45.0. I paired it with some baggy straight-leg jeans, chunky white sneakers, and a white ribbed tank top for a relaxed look that's giving me major 90s feels 🙌. The combo is perfect for everyday wear, and I'm all about that laid-back style 🛍️. This jacket is totally a wardrobe staple!

**Final output to user:**
 A found listing with suggestions from their example wardrobe and a short caption. 
---

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` |No listings match the price, size, or description parameters. | Saves a clear explanation message to the session error key and stops the execution loop early so empty data isn't passed along.|
| `suggest_outfit` | The AI network call drops or a wardrobe key is formatted unexpectedly. | Catches the issue safely, avoids a system crash by using backup lookup text defaults, and provides a friendly offline advice note.|
| `create_fit_card` | The provided outfit text input is empty, blank, or the AI request fails. | Returns a charming, pre-built fallback post template filled in with the item name, price, and marketplace so the user still gets an output. |

---

## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->

* **One way planning.md helped during implementation:**
  It helped map out exactly how information travels between tools before writing any code. Noticing early on that the market listings file used a "title" label while the user wardrobe file used a "name" label kept me from breaking the code with dictionary lookup errors.

* **One divergence from your spec, and why:**
  I chose to use a continuous while loop driven by a phase name tracker rather than a rigid top-to-bottom recipe. This structure makes it incredibly clean to exit early or skip directly to error logging the exact moment a tool reports zero matching results.
---

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.
