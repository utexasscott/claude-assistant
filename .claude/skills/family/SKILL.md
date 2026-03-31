---
name: family
description: Use when receiving an update about a family member, researching gift ideas, looking up gift ideas for a family member, or updating a family profile. DO NOT use for mental health treatment program research, admissions research, or program finding — those have dedicated workflows in the workflow index.
---

## Context

All family data lives in `context/family/`. Before any operation, read the relevant file(s):

- `context/family/family_overview.md` — household structure, living situation, high-level summary
- `context/family/[person].md` — individual profiles (one file per person)

Check `context/family/family_overview.md` first to learn who's in the household and what files exist.

---

## Route Based on Request

| What the user says | Operation |
|---|---|
| "Update on [name]…" / "Just so you know, [name]…" / "Remember that [name]…" | **Update profile** |
| "Gift ideas for [name]?" / "What should I get [name] for…" | **Gift ideas** |
| "Research gifts for…" / "What's popular for [age]-year-olds who like…" | **Gift research** |
| "Add that to my Gifts list" / "Put [X] on Keep" | **Add to Keep** |

---

## Operation: Update Profile

1. Read the relevant family member's profile file.
2. Determine whether to append to the Updates Log, revise an existing section, or add a new section.
3. Edit the file — update the "Last updated" date.
4. Confirm the change briefly.

**Rules:**
- Keep updates factual and neutral in tone.
- Never delete previous Updates Log entries — append only.
- Flag anything suggesting a change in health, safety, or living situation, as it may affect other workflows.
- Handle mental health context, medical diagnoses, and family transitions (separation, divorce, co-parenting) with care — factual and supportive only.
- Maintain neutral framing for co-parenting context — no adversarial language.

**Fields to keep current:**
- Age (recalculate from DOB around birthdays — flag upcoming birthdays)
- Interests (add/remove as they evolve)
- Health/support context (factual, clinical-level notes only)
- Gift Ideas & Notes (running list, never delete old entries)
- Updates Log (append only)

---

## Operation: Gift Ideas

1. Read the relevant family member's profile.
2. Review their interests, sensitivities, and any prior gift notes.
3. Offer 3–5 specific, thoughtful suggestions with brief rationale for each.
4. Ask if the user wants to save any to the profile's Gift Ideas & Notes or research further.

**Gift idea rules:**
- Check the person's current interests before defaulting to anything.
- Review health/support notes for any sensitivities (noise, competition, overwhelm, etc.).
- Flag gifts that require heavy parental involvement unless it's a shared activity the user would enjoy.
- Flag upcoming birthdays within 60 days when suggesting gifts.

---

## Operation: Gift Research

1. Read the relevant family member's profile.
2. Use WebSearch to find age-appropriate, interest-matched options.
3. Return results with: item name, approximate price, why it fits this person, any caveats.
4. Offer to save top picks to the profile's Gift Ideas & Notes section.

---

## Operation: Add to Keep

**No Google Keep tool exists yet.**

Until the tool is built:
1. Tell the user which items to add manually to Google Keep.
2. Log them in the relevant family member's profile under "Gift Ideas & Notes."

When the tool is available, this operation will call:
```
python tools/add_to_keep.py --item "gift description" --person "Name"
```

---

## Proactive Profile Updates

When the user provides new information about a family member in any conversation — even if this skill wasn't explicitly invoked — update the relevant file before the session ends. Do not wait to be asked.

---

## Upcoming Birthdays

Read `context/family/family_overview.md` or individual profiles to find DOBs. Flag any birthday within 60 days when relevant.
