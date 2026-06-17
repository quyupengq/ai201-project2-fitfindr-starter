# FitFindr

FitFindr is a multi-tool AI agent that helps users search for secondhand clothing, style a selected item with their wardrobe, and create a short shareable outfit caption. The agent uses a planning loop instead of blindly calling every tool every time. It checks the result of each step, stores important information in session state, and stops early with a helpful message when the workflow cannot continue.

---

## Project Overview

A user can ask something like:

> "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

FitFindr then:

1. Searches the mock listings dataset for matching secondhand items.
2. Selects the best listing.
3. Suggests an outfit using the selected item and the user's wardrobe.
4. Creates a short fit card caption for the outfit.

If no listing matches the request, FitFindr stops early and explains what the user can change, such as raising the budget, removing the size filter, or using a broader search description.

---

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_key_here
```

Run the Gradio app:

```bash
python app.py
```

Then open the local URL shown in the terminal.

Run tests:

```bash
pytest tests/
```

---

## Tool Inventory

### Tool 1: `search_listings(description, size, max_price)`

**Purpose:**
Searches the mock secondhand listings dataset for items matching the user's requested description, size, and budget.

**Inputs:**

* `description` (`str`): The item or style the user is searching for, such as `"vintage graphic tee"` or `"90s track jacket"`.
* `size` (`str | None`): The requested size, such as `"M"` or `"XXS"`. If no size is given, this is `None`.
* `max_price` (`float | None`): The highest price the user wants to pay. If no price is given, this is `None`.

**Output:**
Returns a `list[dict]` of matching listing dictionaries. Each listing may include:

* `id`
* `title`
* `description`
* `category`
* `style_tags`
* `size`
* `condition`
* `price`
* `colors`
* `brand`
* `platform`

The results are sorted by a relevance score, with higher-scoring results first. If two items are similar in relevance, cheaper items are prioritized.

**Failure behavior:**
If no listings match, the function returns an empty list `[]`. It does not crash or return `None`.

---

### Tool 2: `suggest_outfit(new_item, wardrobe)`

**Purpose:**
Suggests an outfit using the selected secondhand item and the user's wardrobe.

**Inputs:**

* `new_item` (`dict`): The selected listing returned by `search_listings`.
* `wardrobe` (`dict`): The user's wardrobe dictionary. It should contain an `items` list, but the function can handle an empty wardrobe.

**Output:**
Returns a non-empty `str` containing an outfit suggestion.

Example:

```text
Style the Y2K Baby Tee — Butterfly Print with relaxed jeans, simple sneakers, and a clean outer layer like a denim jacket, hoodie, or flannel.
```

**Failure behavior:**
If `new_item` is missing, the function returns a message explaining that no thrifted item was selected. If the wardrobe is empty, the tool still gives general styling advice using common basics. If the Groq API call fails, the function returns a fallback outfit suggestion instead of crashing.

---

### Tool 3: `create_fit_card(outfit, new_item)`

**Purpose:**
Creates a short, shareable caption for the outfit.

**Inputs:**

* `outfit` (`str`): The outfit suggestion returned by `suggest_outfit`.
* `new_item` (`dict`): The selected listing returned by `search_listings`.

**Output:**
Returns a `str` containing a short fit card caption.

Example:

```text
Found the Y2K Baby Tee — Butterfly Print on depop for $18.0 and built the fit around it.
```

**Failure behavior:**
If the outfit string is empty or missing, the function returns a clear error message:

```text
I couldn't create a fit card because there was no outfit suggestion to summarize.
```

If the Groq API call fails, the function returns a fallback caption using the selected item and outfit suggestion.

---

## Planning Loop

The planning loop is implemented in `run_agent()` inside `agent.py`.

The agent does not call all tools unconditionally. It makes decisions based on what happened in the previous step.

### Planning loop steps

1. Initialize a new session dictionary with `_new_session(query, wardrobe)`.
2. Parse the user query using `_parse_query(query)`.
3. Store the parsed values in `session["parsed"]`.
4. Call `search_listings(description, size, max_price)`.
5. Store the results in `session["search_results"]`.
6. If no listings are found:

   * Set `session["error"]`.
   * Leave `session["selected_item"]`, `session["outfit_suggestion"]`, and `session["fit_card"]` as `None`.
   * Return the session early.
7. If listings are found:

   * Select the first listing.
   * Store it in `session["selected_item"]`.
8. Call `suggest_outfit(session["selected_item"], wardrobe)`.
9. Store the returned outfit in `session["outfit_suggestion"]`.
10. If the outfit suggestion is empty:

* Set `session["error"]`.
* Return the session early.

11. Call `create_fit_card(session["outfit_suggestion"], session["selected_item"])`.
12. Store the result in `session["fit_card"]`.
13. Return the completed session.

This makes the workflow conditional. For example, when `search_listings()` returns `[]`, the agent stops and does not call the outfit or fit card tools.

---

## State Management

State is stored in a session dictionary. This dictionary is the single source of truth for one interaction.

The session stores:

```python
{
    "query": query,
    "parsed": {},
    "search_results": [],
    "selected_item": None,
    "wardrobe": wardrobe,
    "outfit_suggestion": None,
    "fit_card": None,
    "error": None,
}
```

The most important state handoffs are:

1. `search_listings()` returns a list of results.
2. The agent saves the top result as `session["selected_item"]`.
3. `session["selected_item"]` is passed into `suggest_outfit()`.
4. The outfit suggestion is saved as `session["outfit_suggestion"]`.
5. `session["outfit_suggestion"]` and `session["selected_item"]` are passed into `create_fit_card()`.

This lets the agent move through the workflow without asking the user to re-enter the item or outfit details.

---

## Error Handling Strategy

| Tool              | Failure Mode                      | Agent Response                                                                                                                                                                       |
| ----------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `search_listings` | No results match the query        | The agent sets `session["error"]` and tells the user to raise the max price, remove the size filter, or use a broader description. It stops early and does not call the other tools. |
| `suggest_outfit`  | Wardrobe is empty                 | The tool gives general styling advice using common basics instead of crashing. The agent continues to the fit card step if the suggestion is valid.                                  |
| `suggest_outfit`  | Selected item is missing          | The tool returns a message saying no thrifted item was selected.                                                                                                                     |
| `create_fit_card` | Outfit input is missing or empty  | The tool returns an informative message saying it could not create a fit card because there was no outfit suggestion.                                                                |
| `create_fit_card` | Groq API fails or returns nothing | The tool returns a fallback caption using the selected item and outfit text.                                                                                                         |

### Concrete error example

Input:

```text
designer ballgown size XXS under $5
```

The search returns:

```python
[]
```

The agent response is:

```text
I couldn't find any listings matching that exact request. Try raising your max price, removing the size filter, or using a broader description.
```

In this case, `selected_item` remains `None`, `outfit_suggestion` remains `None`, and `fit_card` remains `None`.

---

## Testing

The project includes pytest tests in `tests/test_tools.py`.

The tests cover:

* normal search results
* no-results search
* price filtering
* empty wardrobe handling
* missing selected item handling
* empty fit card input
* normal fit card generation

Run tests with:

```bash
pytest tests/
```

I also manually tested the full tool chain with:

```bash
python agent.py
```

This shows both:

1. A happy path query that finds a listing, creates an outfit suggestion, and creates a fit card.
2. A no-results query that stops early with an error message.

---

## Gradio App

The interface is implemented in `app.py`.

Run it with:

```bash
python app.py
```

The app has:

* a textbox for the user's query
* a wardrobe selector
* one panel for the selected listing
* one panel for the outfit idea
* one panel for the fit card

Example successful query:

```text
vintage graphic tee under $30
```

Example failure query:

```text
designer ballgown size XXS under $5
```

The successful query fills all three panels. The failure query shows an error in the listing panel and leaves the outfit and fit card panels blank.

---

## Spec Reflection

### One way the spec helped

Writing `planning.md` first made the implementation easier because I already knew what each tool should accept, what it should return, and what should happen when something fails. The planning loop section was especially useful because it made it clear that the agent should stop early when search results are empty instead of calling the other tools with bad input.

### One way implementation diverged from the spec

The original plan described simple keyword matching, but the final `search_listings()` implementation added a relevance score and a cheaper-item tiebreaker. This still matches the overall spec, but it improves the quality of the selected listing by ranking better matches first instead of only filtering.

Another small difference is that the LLM tools include fallback responses. The spec said the tools should handle failure without crashing, and the fallback responses make the app usable even if the Groq API key is missing or the API call fails.

---

## AI Usage

### Instance 1: Planning document

I used ChatGPT to help turn the assignment requirements into a complete `planning.md`. I gave it the project instructions and the starter planning template. It helped draft the tool specifications, planning loop, state management section, error handling table, architecture diagram, and complete interaction walkthrough.

I reviewed and adjusted the output to make sure the tool names, input parameters, and return values matched the actual starter code.

### Instance 2: Tool implementation

I used ChatGPT to help implement the three required tools in `tools.py`. I gave it the Tool Specifications section from `planning.md` and the starter function stubs. It produced implementations for `search_listings()`, `suggest_outfit()`, and `create_fit_card()`.

I tested the generated code manually and found that the first version of `search_listings()` returned no results for `"vintage graphic tee"`. I debugged the dataset, checked the actual listing fields, and revised the search function to tokenize text, score keyword matches, and sort results by relevance.

### Instance 3: Planning loop and app wiring

I used ChatGPT to help implement `run_agent()` in `agent.py` using the Planning Loop, State Management, and Architecture sections from `planning.md`. It also helped implement `handle_query()` in `app.py`.

I verified the output by running `python agent.py` and testing both the happy path and no-results path in the Gradio interface.

---

## Demo Video Plan

The demo video will show:

1. Running the app with `python app.py`.
2. A successful query such as:

```text
vintage graphic tee under $30
```

3. The selected listing, outfit suggestion, and fit card appearing in the three output panels.
4. A verbal explanation that the selected listing is stored in session state and passed into the outfit tool.
5. A failure query such as:

```text
designer ballgown size XXS under $5
```

6. The app showing a helpful error message and stopping before outfit generation.

---

## Files

Important files:

```text
planning.md
tools.py
agent.py
app.py
tests/test_tools.py
tests/conftest.py
data/listings.json
data/wardrobe_schema.json
utils/data_loader.py
```

---

## Submission Checklist

* [x] `planning.md` completed before implementation
* [x] Three required tools implemented
* [x] Planning loop implemented
* [x] State management implemented with a session dictionary
* [x] Error handling implemented for each tool
* [x] Gradio app wired to the agent
* [x] Pytest tests added
* [x] README updated
* [ ] Demo video recorded
* [ ] GitHub repository submitted
