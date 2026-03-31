---
name: recipes
description: Use when adding a recipe, editing a recipe, updating a recipe, listing recipes, showing recipes, viewing a recipe, deleting a recipe, or managing the recipe collection.
argument-hint: "[add | edit | list | view | delete] [recipe name]"
metadata:
  visibility: public
---

## Context

All recipes live in `context/recipes/`. One file per recipe, named in `snake_case.md` (e.g., `chicken_tikka_masala.md`). Skip files starting with `_` — those are templates.

See `context/recipes/_example.md` for the canonical format.

---

## Route Based on Request

Determine the operation from `$ARGUMENTS` or from what the user said:

| Request | Operation |
|---|---|
| "add a recipe for…" / "save this recipe" | **Add** |
| "edit / update / change my [recipe]" | **Edit** |
| "show my recipes" / "what recipes do I have" / "list recipes" | **List** |
| "show me [recipe]" / "what's in my [recipe]" | **View** |
| "delete / remove [recipe]" | **Delete** |

---

## Recipe File Format

```markdown
# Recipe Title

**Servings:** 4 | **Prep:** 20m | **Cook:** 30m | **Tags:** chicken, easy, 30min

## Ingredients
- 1 lb chicken breast
- 2 cloves garlic, minced
- 1 tbsp olive oil

## Instructions
1. Step one.
2. Step two.
3. Step three.

## Notes
- Can substitute shrimp for chicken.
- Freezes well for up to 3 months.
```

**Tags to use consistently** (used by meal planner for filtering):

| Category | Values |
|---|---|
| Difficulty | `easy`, `medium`, `advanced` |
| Time | `quick` (≤20m total), `30min` (≤30m), `1hr`, `slow` |
| Protein | `chicken`, `beef`, `pork`, `shrimp`, `salmon`, `fish`, `vegetarian`, `vegan` |
| Style | `pasta`, `tacos`, `soup`, `salad`, `grill`, `sheet-pan`, `one-pot` |
| Use | `kid-friendly`, `meal-prep`, `freezer-friendly` |

---

## Operation: Add

1. Collect the recipe details from what the user provides. Ask for anything missing:
   - Recipe name (required)
   - Servings, prep time, cook time (ask if not given)
   - Ingredients — confirm the list looks complete before writing
   - Instructions — numbered steps
   - Tags — suggest appropriate ones based on the recipe; confirm with user
   - Notes — optional

2. Determine the filename: recipe name → snake_case + `.md`. Check if a file already exists at that path. If it does, warn the user and ask: replace it, create a variant name, or cancel?

3. Write the file to `context/recipes/<filename>.md` using the format above.

4. Confirm with the exact filename written and a brief summary of what was saved.

---

## Operation: Edit

1. Identify the recipe. If the user names it, find the matching file in `context/recipes/`. If the name is ambiguous or not found, list the closest matches and ask for clarification.

2. Read the file before making any changes.

3. Apply the requested changes. Common edits:
   - Adding/removing/changing ingredients
   - Rewriting or reordering instructions
   - Updating servings, times, or tags
   - Adding or removing notes

4. For small edits (one ingredient, one tag), just apply them. For larger changes (rewriting instructions, restructuring), show a before/after summary and confirm before writing.

5. Write the updated file and confirm what changed.

---

## Operation: List

Read all `.md` files in `context/recipes/` (skip `_` prefixed files) and display:

```
Your recipes (N total):

  chicken_tikka_masala.md — Chicken Tikka Masala [chicken, medium, 1hr]
  shrimp_tacos.md         — Shrimp Tacos [shrimp, easy, 30min]
  pasta_puttanesca.md     — Pasta Puttanesca [pasta, vegetarian, easy]
```

If the directory is empty or doesn't exist, say so and offer to add the first recipe.

---

## Operation: View

Read the file and display it cleanly — title, metadata line, then ingredients and instructions formatted for easy reading. Don't show raw markdown syntax.

---

## Operation: Delete

1. Confirm the recipe name and ask the user to confirm the deletion before removing the file.
2. Delete the file.
3. Confirm it's been removed.

---

## Edge Cases

| Situation | How to handle |
|---|---|
| Recipe name already exists on Add | Warn the user. Ask: overwrite, rename, or cancel? |
| User gives partial info | Write what you have, flag missing sections clearly |
| User pastes a recipe from the web | Parse it into standard format, confirm before saving |
| Ambiguous recipe name | List partial matches and ask which one |
| `context/recipes/` doesn't exist | Create it automatically on first write |
