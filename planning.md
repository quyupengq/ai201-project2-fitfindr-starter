# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Searches the mock secondhand listings dataset for clothing items that match the user's requested item description, size, and max price. It returns matching listings so the agent can choose one item to style.
**Input parameters:**
description (str): The item or style the user is searching for, such as "vintage graphic tee" or "black denim jacket".
size (str): The requested clothing size, such as "S", "M", "L", or None if the user did not give a size.
max_price (float): The highest price the user wants to pay, or None if the user did not give a budget.

**What it returns:**
Returns a list of dictionaries. Each dictionary represents one listing from the mock dataset. A result can include fields like id, title, description, category, style_tags, size, condition, price, colors, brand, and platform.

The list should be sorted so the best or most relevant match appears first.
**What happens if it fails or returns nothing:**
If no listings match, the tool returns an empty list []. The agent should tell the user that no exact matches were found and suggest changing the search by raising the max price, removing the size filter, or using a broader description. The agent should stop early and should not call suggest_outfit or create_fit_card.

---

### Tool 2: suggest_outfit

**What it does:**
Creates an outfit suggestion using the selected thrifted item and the user's wardrobe. It explains how the new item can be styled with clothes the user already owns.
**Input parameters:**
new_item (dict): The selected listing returned from search_listings.
wardrobe (dict): The user's wardrobe data, following the provided wardrobe schema.

**What it returns:**
Returns a string with one practical outfit suggestion. The suggestion should mention the new item, connect it to wardrobe pieces, and explain the overall style.
Example return:
"Pair the faded band tee with your baggy jeans and chunky sneakers for a relaxed 90s grunge look. Roll the sleeves once and add a hoodie or flannel for layering."
**What happens if it fails or returns nothing:**
If the wardrobe is empty or very small, the tool should still return a general outfit suggestion instead of crashing. For example, it can suggest common basics like relaxed jeans, neutral sneakers, or a simple jacket. If new_item is missing or invalid, the tool should return an error message string so the agent can stop safely.
---

### Tool 3: create_fit_card

**What it does:**
Generates a short, shareable outfit caption based on the selected thrifted item and the outfit suggestion. The caption should sound like something someone might post on Instagram or TikTok

**Input parameters:**
outfit (str): The outfit suggestion returned from suggest_outfit.
new_item (dict): The selected listing returned from search_listings.
**What it returns:**
Returns a short string caption for the full outfit.

Example return:
"thrifted this faded tee for $22 and it instantly made the fit feel intentional 🖤 baggy jeans + chunky sneakers did the rest"

**What happens if it fails or returns nothing:**
If the outfit input is missing, empty, or incomplete, the tool should return an informative error message instead of crashing. The agent should display that message in the fit card section. If the LLM returns a weak or empty response, the tool should create a simple fallback caption using the item title and price.

---

### Additional Tools (if any)

No additional tools for the required version. I will finish the three required tools first before adding stretch features.

Possible stretch feature later: retry logic with fallback search. If the first search returns no results, the agent could retry with a looser size or price filter and tell the user what changed.
---

## Planning Loop

**How does your agent decide which tool to call next?**
The agent uses a session dictionary and a step-by-step planning loop. It does not call every tool automatically. It checks the result of each tool before deciding whether to continue.

Start with the user's query.
Extract the item description, requested size, and max price from the query.
Store those values in the session.
Call search_listings(description, size, max_price).
Store the returned list in session["search_results"].
If search_results is empty:
Set session["error"] to a helpful no-results message.
Set session["selected_item"], session["outfit_suggestion"], and session["fit_card"] to None.
Return the session early.
If listings are found:
Choose the first result as the selected item.
Store it in session["selected_item"].
Call suggest_outfit(session["selected_item"], session["wardrobe"]).
Store the returned string in session["outfit_suggestion"].
If the outfit suggestion is missing or empty:
Set session["error"].
Set session["fit_card"] to None.
Return the session early.
If the outfit suggestion is valid:
Call create_fit_card(session["outfit_suggestion"], session["selected_item"]).
Store the returned caption in session["fit_card"].
Return the completed session.

The loop is done when either an error stops the workflow early or the final fit card has been created.
---

## State Management

**How does information from one tool get passed to the next?**
Information is passed through a session dictionary. Each tool result is saved in the session before the next tool runs.

The session tracks:

query: the original user request
description: the item description extracted from the query
size: requested size, or None
max_price: requested budget, or None
wardrobe: the wardrobe used for outfit suggestions
search_results: the list returned from search_listings
selected_item: the first matching listing chosen by the agent
outfit_suggestion: the string returned from suggest_outfit
fit_card: the caption returned from create_fit_card
error: a helpful error message if the workflow cannot continue

The selected item from search_listings becomes the new_item input for suggest_outfit. The outfit suggestion from suggest_outfit becomes the outfit input for create_fit_card. This lets the agent complete a full workflow without asking the user to re-enter the same information.
---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | The agent tells the user no exact listings were found and suggests raising the budget, removing the size filter, or using a broader description. The agent stops early and does not call the other tools.|
| suggest_outfit | Wardrobe is empty |The tool returns a general styling suggestion using common clothing basics. The agent continues to create a fit card if the suggestion is valid. |
| create_fit_card | Outfit input is missing or incomplete |The tool returns an informative error message instead of crashing. The agent displays that message in the fit card output. |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

flowchart TD A[User input] --> B[Planning Loop] B --> C[Extract description, size, max_price] C --> D[Session stores query details] D --> E[search_listings(description, size, max_price)] E --> F{Listings found?} F -- No --> G[Set session error] G --> H[Return early to user] F -- Yes --> I[Store selected_item in session] I --> J[suggest_outfit(selected_item, wardrobe)] J --> K{Outfit suggestion valid?} K -- No --> L[Set session error] L --> H K -- Yes --> M[Store outfit_suggestion in session] M --> N[create_fit_card(outfit_suggestion, selected_item)] N --> O[Store fit_card in session] O --> P[Return selected item, outfit suggestion, and fit card to user]

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I will use ChatGPT to help implement each tool one at a time. For search_listings, I will give ChatGPT the Tool 1 section of this planning document and ask it to implement search_listings(description, size, max_price) using load_listings() from utils/data_loader.py. I expect it to produce a function that filters listings by description, size, and max price.

Before using the code, I will verify that it returns a list, handles None for size and max price, and returns [] when there are no matches. I will test it with at least three queries: one normal query, one impossible query, and one price-filter query.

For suggest_outfit, I will give ChatGPT the Tool 2 section and the wardrobe schema. I will ask it to implement the function using Groq and llama-3.3-70b-versatile. I expect it to return a useful outfit suggestion string. I will verify that it handles an empty wardrobe and does not crash.

For create_fit_card, I will give ChatGPT the Tool 3 section. I will ask it to create a function that uses the outfit suggestion and selected item to generate a short caption. I will verify that the caption is short, different for different inputs, and that the function handles an empty outfit string.
**Milestone 4 — Planning loop and state management:**
I will use ChatGPT to help implement run_agent() in agent.py. I will give it the Planning Loop, State Management, and Architecture sections from this planning document. I expect it to produce a planning loop that calls search_listings first, branches if no results are found, stores the selected item in the session, passes it to suggest_outfit, then passes the outfit suggestion to create_fit_card.

Before using the code, I will check that it does not call all three tools unconditionally. I will verify that it stores search_results, selected_item, outfit_suggestion, and fit_card in the session. I will also test the no-results path to confirm that the agent stops early and leaves fit_card as None.
---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent reads the user query and extracts the search information.

description = "vintage graphic tee"
size = None because the user did not give a size
max_price = 30.0

The agent calls:

search_listings("vintage graphic tee", size=None, max_price=30.0)

The tool returns a list of matching listings. For example:

[
    {
        "id": "item_001",
        "title": "Faded Band Tee",
        "description": "Vintage-style graphic band tee",
        "category": "tops",
        "style_tags": ["vintage", "graphic", "grunge"],
        "size": "M",
        "condition": "Good",
        "price": 22.0,
        "colors": ["black", "gray"],
        "brand": "Unknown",
        "platform": "Depop"
    }
]
The agent stores the full list in session["search_results"] and stores the first item in session["selected_item"].
**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
The agent uses the selected item and the wardrobe to create a styling suggestion.

The agent calls:

suggest_outfit(session["selected_item"], session["wardrobe"])

The tool returns:

Pair the faded band tee with your baggy jeans and chunky sneakers for a relaxed 90s grunge look. Roll the sleeves once and add a hoodie or flannel if you want more shape and layering.

The agent stores this string in session["outfit_suggestion"].
**Step 3:**
<!-- Continue until the full interaction is complete -->
The agent uses the outfit suggestion and selected item to create a shareable fit card.

The agent calls:

create_fit_card(session["outfit_suggestion"], session["selected_item"])

The tool returns:

thrifted this faded band tee for $22 and it instantly gave the fit that 90s grunge feel 🖤 baggy jeans + chunky sneakers carried

The agent stores this string in session["fit_card"].
**Final output to user:**
<!-- What does the user actually see at the end? -->
The user sees three completed panels:

Selected Item:
Faded Band Tee — $22 on Depop, Good condition

Outfit Suggestion:
Pair the faded band tee with your baggy jeans and chunky sneakers for a relaxed 90s grunge look. Roll the sleeves once and add a hoodie or flannel if you want more shape and layering.

Fit Card:
thrifted this faded band tee for $22 and it instantly gave the fit that 90s grunge feel 🖤 baggy jeans + chunky sneakers carried