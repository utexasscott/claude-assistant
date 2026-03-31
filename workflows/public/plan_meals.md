# Workflow: Plan My Meals This Week

## Objective
Plan 7 days of dinners (and optionally lunches/breakfasts) based on available recipes and pantry inventory. Determine what to buy, add the trip to Google Calendar, and push the final grocery list directly into the configured section of the Keep shopping list.

---

## When to Run
- Once a week, ideally Sunday or Monday morning before the first meal of the week.

---

## Required Inputs
- `context/recipes/*.md` — at least a handful of recipe files (see `context/recipes/_example.md` for format)
- `pantry.md` — current pantry inventory
- Google Calendar OAuth (`token_calendar.json`)
- Google Keep auth (`KEEP_EMAIL` + `KEEP_MASTER_TOKEN` in `.env`)
- `.env` configured with `TIMEZONE`, `CALENDAR_IDS`, `KEEP_SHOPPING_NOTE_TITLE`, `KEEP_GROCERY_STORE_SECTION`

**First-time setup only:**
```
pip install gkeepapi gpsoauth
python tools/setup_keep_auth.py
```

---

## Steps

### Step 1 — Ask about the grocery trip timing

Before doing anything else, ask the user:

> "Before I start planning: do you plan to go to the grocery store before tonight's dinner?
> And when do you next plan to go? (e.g., 'today at 10am', 'tomorrow morning', 'Tuesday afternoon')"

Capture:
- `go_before_tonight` — boolean (yes/no)
- `trip_date` — the date (YYYY-MM-DD) of the next grocery trip
- `trip_time` — approximate time in HH:MM (24h)
- `trip_duration` — how long they usually spend at the store (default: 60 minutes)

This matters for meal planning: meals planned before the trip must come from current pantry stock only.

---

### Step 2 — Load this week's calendar

```bash
python tools/get_calendar_events.py --date <YYYY-MM-DD>
```

Run this for each of the next 7 days (Monday–Sunday or today through today+6).
Output files: `.tmp/calendar_YYYY-MM-DD.json`

Scan the results to identify:
- Evenings that are already committed (dinner out, events after 5pm)
- Nights that are busy or likely short on cooking time
- Days off that allow for more ambitious recipes

If `get_calendar_events.py` doesn't support multi-day fetching natively, call it once per day.

---

### Step 3 — Load recipes and pantry

```bash
python tools/get_recipes.py
python tools/get_pantry.py
```

Outputs:
- `.tmp/recipes.json`
- `.tmp/pantry.json`

---

### Step 4 — Propose a 7-day meal plan (agent step)

Read all three data sources and reason through the week:

**Rules:**
1. Meals planned **before** `trip_date` must use only what's already in the pantry.
2. Meals planned **on or after** `trip_date` can use ingredients that will be purchased.
3. Match meal complexity to the evening — easy recipes (tagged `easy`, `quick`, `30min`) for busy nights; more involved ones for open evenings.
4. Prioritize using up perishables already in the pantry (produce, proteins in fridge).
5. If fewer recipes exist than days, it's okay to suggest "leftover night," a simple pantry meal (pasta with olive oil and parmesan), or flag that more recipes are needed.
6. Aim for variety — avoid repeating the same protein two nights in a row.

**Present the plan in this format:**

```
MEAL PLAN — Week of [date]

Mon Mar 2  → Chicken Tikka Masala (pantry only ✓)
Tue Mar 3  → Leftover night
Wed Mar 4  [grocery trip] → Shrimp tacos (ingredients to buy)
Thu Mar 5  → Sheet pan salmon with asparagus
Fri Mar 6  → Homemade pizza (easy, ~30min)
Sat Mar 7  → Pasta puttanesca
Sun Mar 8  → Grilled chicken with roasted veggies
```

Then ask:
> "Does this plan work? Any swaps, skips, or nights you'd like to change?"

Incorporate any changes before moving on.

---

### Step 5 — Calculate the grocery list (agent step)

From the approved 7-day plan:

1. Collect all ingredients from the recipes assigned to days **on or after** `trip_date`.
2. Compare each ingredient against `pantry.json` (use `normalized_items` for fuzzy matching — strip quantities and articles before comparing).
3. Flag ingredients already in the pantry as "have it."
4. Compile the remaining ingredients as the shopping list.
5. Deduplicate and consolidate (e.g., two recipes each needing garlic → list garlic once).
6. Group by store section where possible: Produce, Proteins, Dairy, Dry Goods, Canned/Jarred, Frozen, Other.

**Present the shopping list:**

```
GROCERY LIST

Produce
  - 1 lb asparagus
  - 1 lb cherry tomatoes
  - 1 lime

Proteins
  - 1 lb shrimp (peeled, deveined)
  - 2 salmon fillets

Dairy
  - 1 cup heavy cream

Canned/Jarred
  - 1 can (14oz) diced tomatoes

Other
  - Corn tortillas
```

Then ask:
> "Does this list look right? Anything to add or remove before I push it to Keep and add the grocery trip to your calendar?"

---

### Step 6 — Save the approved grocery list

Once approved, write the list to `.tmp/heb_list.json` as a flat array of strings.
Format each item simply: `"1 lb asparagus"`, `"Corn tortillas"`, `"Heavy cream (1 cup)"`.

```json
[
  "1 lb asparagus",
  "1 lb cherry tomatoes",
  "1 lime",
  "1 lb shrimp (peeled, deveined)",
  "2 salmon fillets",
  "Heavy cream (1 cup)",
  "Diced tomatoes, 14oz can",
  "Corn tortillas"
]
```

The file is a flat list — section groupings are implied by the presentation in Step 5 but Keep doesn't support nested lists.

---

### Step 7 — Add the Grocery Trip to Google Calendar

```bash
python tools/add_calendar_event.py \
  --title "grocery run" \
  --date <trip_date> \
  --time <trip_time> \
  --duration <trip_duration> \
  --description "Meal plan grocery run — see Shopping list in Keep" \
  --color 5
```

Color 5 = banana (yellow) — visually distinct from focus blocks (teal).

If the user wasn't sure of the exact time, use a reasonable default (e.g., 10:00) and note it in the description.

---

### Step 8 — Update the Keep shopping list

```bash
python tools/update_keep_list.py
```

This clears the configured grocery store section in the Keep shopping list and replaces it with the contents of `.tmp/heb_list.json`.

On success, confirm:
> "Done! The grocery store section in your Keep shopping list has been updated with [N] items, and the grocery trip is on your calendar for [day] at [time]."

---

## Edge Cases

| Situation | How to handle |
|---|---|
| No recipes in `context/recipes/` | Warn the user. Offer to plan simple pantry meals and ask if they want to add recipes first. |
| All pantry items are depleted | Plan all meals from purchased ingredients, remind user to update `pantry.md` after each shop. |
| Pantry is empty or `pantry.md` is just the template | Ask the user what they have on hand before proceeding. |
| Grocery trip is already on the calendar | Mention it and ask if they want to add another event or skip Step 7. |
| Keep auth fails | Direct user to re-run `python tools/setup_keep_auth.py`. |
| User wants breakfast/lunch included | Extend the plan to include those meals. Add their ingredients to the same shopping list. |
| Pantry has something listed but it's "used up" | `pantry.md` is self-reported. Ask if they want to update it before calculating the list. |

---

## Improvement Log
*(Update this section when you discover constraints, better methods, or recurring issues.)*

---

## Notes
- `pantry.md` should be updated after every grocery run and as items are used up. It's the user's responsibility to keep it current.
- The Keep shopping list's grocery store section header must exist as an unchecked list item in the note for the update tool to find it. Set `KEEP_GROCERY_STORE_SECTION` in `.env` to the exact label used in your Keep note.
- `get_calendar_events.py` fetches one day at a time — call it once per day for the 7-day window.
