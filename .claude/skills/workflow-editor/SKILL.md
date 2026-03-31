---
name: workflow-editor
description: Use when creating a new workflow, adding a workflow, defining a new process, updating an existing workflow, modifying workflow steps, making changes to a workflow, or refactoring content between a workflow and a skill.
---

## What This Skill Does

Handles creating new workflows and updating existing ones. For creation, follows the documented SOP in `create_workflow.md`. For updates, reads all affected files before touching anything, applies changes in the right order, and verifies consistency.

---

## Step 1: Determine Intent

| Request | Path |
|---|---|
| Creating a new workflow | Go to Step 2 |
| Updating one or more existing workflows | Go to Step 3 |

---

## Step 2: Creating a New Workflow

Read `workflows/public/create_workflow.md` in full and follow it from Step 1 through Step 6.

---

## Step 3: Updating an Existing Workflow

### Read First, Edit Second

Before touching any file, read:

1. `workflows/_index.md` — understand the full workflow landscape
2. Every affected workflow in full
3. Any skill the workflow references (e.g., `/context`, `/journal`) or whose content overlaps with what's changing
4. Those skills in full

### Understand the Scope

Before making any edits, establish:
- What specifically is changing, and why?
- Is content moving between a workflow and a skill?
- Will any trigger phrases, file references, or step sequences change?
- Does the workflow index need updating?

### Apply Changes in the Right Order

| Change type | Order |
|---|---|
| Moving content from workflow → skill | Update the skill first, then remove from workflow and add skill reference |
| Adding new content to a skill a workflow uses | Update the skill first, then update any workflow references if needed |
| Workflow-only edits (steps, structure, tone) | Edit the workflow directly |
| Trigger phrase changes | Edit the workflow, then update `_index.md` |

### Verify Before Finishing

- **No content gap** — anything removed from the workflow is now covered in a skill (or deliberately dropped)
- **No duplication** — the same rule or guidance doesn't appear in both a workflow and a skill
- **No broken references** — any `/skill-name` or file path mentioned in the workflow still exists
- **Workflow index is current** — triggers and file paths are accurate

---

## Notes

- Read every affected file before editing any of them. Never edit based on partial context.
- When deciding where something belongs: workflow-specific timing and cadence stays in the workflow; reusable mechanics, format rules, and quality gates belong in the skill.
- If the scope is larger than expected, surface that to the user before proceeding.
- Skill creation and optimization uses `/skill-builder`, not this skill.
