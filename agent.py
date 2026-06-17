"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""


import os
import json
from dotenv import load_dotenv
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, MAX_TOOL_ROUNDS
from tools import search_listings, suggest_outfit, create_fit_card
# ── session state ─────────────────────────────────────────────────────────────
_client = Groq(api_key=GROQ_API_KEY)

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # TODO: implement the planning loop
    session = _new_session(query, wardrobe)
    
    current_phase = "PARSE_QUERY"
    tool_rounds = 0
    
    # The main loop keeps spinning until we hit an error, complete the final phase, or break
    while current_phase is not None:
        tool_rounds += 1
        
        # Circuit Breaker Guard
        if tool_rounds > MAX_TOOL_ROUNDS:
            session["error"] = f"Agent stopped: Exceeded MAX_TOOL_ROUNDS limit of {MAX_TOOL_ROUNDS}."
            break

        # --- PHASE 1: PARSE QUERY ---
        if current_phase == "PARSE_QUERY":
            try:
                parsing_prompt = f"""You are a strict data extraction engine. Analyze this shopping query: "{query}"
                
                    Extract these 3 fields:
                    1. "description": Keywords describing the item.
                    2. "size": Size string if mentioned, else null.
                    3. "max_price": Number for max price if mentioned, else null. Do not include currency symbols.

                    Your response must be ONLY a raw JSON object. No conversation, no markdown formatting blocks, no explanation.
                    Format:
                    {{
                        "description": "string",
                        "size": "string" or null,
                        "max_price": number or null
                    }}"""  
                response = _client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[{"role": "user", "content": parsing_prompt}],
                    temperature=0.0
                )
                cleaned_response = response.choices[0].message.content.strip()
                if cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response.strip("`").replace("json", "", 1).strip()
                
                session["parsed"] = json.loads(cleaned_response)
                
                # Advance to next phase upon success
                current_phase = "SEARCH_LISTINGS"
                
            except Exception as e:
                session["error"] = f"Failed to parse user query: {str(e)}"
                current_phase = None  # Terminate loop early

        # --- PHASE 2: SEARCH LISTINGS ---
        elif current_phase == "SEARCH_LISTINGS":
            try:
                search_results = search_listings(
                    description=session["parsed"].get("description", ""),
                    size=session["parsed"].get("size"),
                    max_price=session["parsed"].get("max_price")
                )
                session["search_results"] = search_results
                
                if not search_results:
                    session["error"] = "No listings found matching your search parameters."
                    current_phase = None  # Terminate early
                else:
                    session["selected_item"] = search_results[0]
                    current_phase = "SUGGEST_OUTFIT"  # Advance
                    
            except Exception as e:
                session["error"] = f"Error during search execution: {str(e)}"
                current_phase = None

        # --- PHASE 3: SUGGEST OUTFIT ---
        elif current_phase == "SUGGEST_OUTFIT":
            try:
                session["outfit_suggestion"] = suggest_outfit(session["selected_item"], session["wardrobe"])
                current_phase = "CREATE_FIT_CARD"  # Advance
            except Exception as e:
                session["error"] = f"Failed to generate outfit suggestion: {str(e)}"
                current_phase = None

        # --- PHASE 4: CREATE FIT CARD ---
        elif current_phase == "CREATE_FIT_CARD":
            try:
                session["fit_card"] = create_fit_card(session["outfit_suggestion"], session["selected_item"])
                current_phase = None  # Goal achieved! Clean break out of loop
            except Exception as e:
                session["error"] = f"Failed to generate fit card caption: {str(e)}"
                current_phase = None

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
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
    print(f"Error message: {session2['error']}")
