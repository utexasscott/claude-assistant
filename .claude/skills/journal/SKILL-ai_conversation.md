# AI Conversation Processing — Journal Subskill

This file is loaded by the journal skill (`SKILL.md`) when the input is identified as an AI conversation transcript. The rules here replace the general prose-cleaning instructions for Steps 5–7 of the journal skill.

**This file is not a skill.** It has no frontmatter and is not user-invocable. It is a procedure document loaded on-demand by the journal skill only.

---

## Detecting AI Conversation Format

An input is an AI conversation if it contains any of:
- Alternating speaker blocks with a named AI (Gemini, ChatGPT, Claude, GPT, etc.)
- Explicit speaker labels ("[User]:", "Gemini:", "Me:", "[AI name]:")
- A consistent separator pattern (e.g., `--`) between alternating turns

When detected, complete the full classification pass described below **before writing a single word of the journal entry.**

---

## Step 1: Classify Every Turn

Walk through the transcript from start to finish. For each AI turn, look at the user's immediate response and classify the pair as one of three cases.

### Case 1 — the user's Own Thought
**Signal:** Appears in the user's turn, not in direct response to an AI claim. The user states something from their own experience, memory, or perspective without the AI having just proposed it.

**Example:**
> [User]: *"I think I lose all of my friends and connections because I do this to everyone. I think it's because I value honesty above everything else."*

**Journal handling:** Write as the user's voice, full prose, no attribution needed. This is primary source material.

**Profile / biography implications:** Valid source. Can inform profile and biography files.

---

### Case 2 — The User Resonated With an AI Claim
**Signal:** An AI makes a claim or offers a framing. the user's next turn does NOT push back — he continues the thread, adds supporting detail, says "yes", "absolutely", "exactly", "that makes sense", or simply goes along with the premise.

**Example:**
> Gemini: *"You've basically described yourself as a social 'Early Adopter.'"*
> [User]: *"Absolutely. I was horrible at dating until suddenly I was a player."*

**Journal handling:** Include the AI section under the attribution callout. Note in the user's following turn that he found the framing resonant. Do not strip the user's reply — include it in his voice.

**Attribution callout (required — paste verbatim):**
> *⚠️ AI-generated response. The analysis below was produced by [AI Name], not the user. The user found it helpful and added it to the record, but it may contain errors, overreach, or clinically unverified claims. It should be read as a thinking tool, not ground truth.*

**Profile / biography implications:** The AI claim is a **hypothesis the user resonated with** — not a confirmed self-assessment. If noting in profiles, use: *"The user resonated with the framing that..."* — never *"The user is..."* or *"The user believes..."*

---

### Case 3 — The User Pushed Back
**Signal:** the user's next turn corrects the AI, redirects, adds context that changes the framing, or explicitly disagrees. Signals include: "I've got to clarify...", "that's not quite right", "you're not getting it", or any turn where the user is fixing something the AI got wrong.

**Example:**
> Gemini: *[frames the user's "player" period as something he enjoyed and mastered]*
> [User]: *"I've got to clarify the 'player' stage I mentioned earlier. I only entered that stage because I didn't know what else to do. I hated it."*

**Journal handling:** Journal ONLY the user's correction. The AI claim that prompted it is noise — omit it entirely. the user's clarification stands on its own as Case 1 content.

**Profile / biography implications:** The AI claim is **rejected**. Ignore it. the user's correction is a valid standing-fact candidate.

---

## Step 2: Handle AI Closing Questions

AI systems often end turns with a question ("Since you've been doing work on psychology..."). These are conversational prompts, not content.

- If the user answered the question in their next turn, their answer is already captured as Case 1/2/3 above
- Omit the AI's closing question from the journal unless it directly frames what follows
- Never include AI questions as though they were journal content

---

## Step 3: Write the Journal Entry

Now that every turn is classified, write the polished journal entry using these rules:

**Structure:**
1. Lead with the user's own statements (Case 1 content) — these are the narrative spine
2. For Case 2 AI sections, insert under `## [Topic] — AI Response` heading with the attribution callout
3. For Case 3, write only the user's correction as normal prose — no mention of the AI's original claim
4. Omit all AI closing questions

**Prose flow:**
- the user's turns are written in first-person, clean prose ("I think I lose all my friends...")
- AI-attributed sections are reproduced faithfully under the attribution heading — do not clean them up
- The journal should read as: the user's reflections, periodically interrupted by AI response sections he found useful

**Section placement:**
- If the user moves between topics across the conversation, organize by topic (Section headers), not by conversation order
- Chronological within a topic, but topic-first structure

---

## The Firewall Rule

The journal file is the firewall between the AI conversation and downstream profile/biography updates. The profile-updater and biography-extractor agents read the journal file — not the raw transcript. Their correctness depends entirely on this file accurately labeling what came from the user vs. what came from AI.

**Do not let AI-attributed content escape the attribution callout.** If it's labeled correctly here, the agents downstream will skip it correctly.

---

## Shared Context

Never propagate AI-attributed sections into shared context files (e.g., co-parenting journal, shared summaries). AI responses belong in the private journal only. the user's own Case 1 and Case 3 statements are eligible for shared context if otherwise appropriate.
