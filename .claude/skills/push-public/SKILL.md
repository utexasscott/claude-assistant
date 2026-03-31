---
name: push-public
description: Use when pushing to the public repo, updating the public repo, syncing public content, or running push-public. Syncs public-safe files from personal-assistant to the claude-assistant public GitHub repo.
argument-hint: "optional commit message"
disable-model-invocation: true
metadata:
  visibility: public
---

## What This Skill Does

Runs `tools/push_public.sh` to sync public-safe files to the `claude-assistant` public GitHub repo. No reasoning — just execute and report.

## Steps

1. Run the script:
   ```
   bash tools/push_public.sh "$1"
   ```
   If no argument was provided, run without arguments (the script has a default commit message).

2. Report the output back to the user — what was copied, whether anything changed, and whether the push succeeded.

## Notes

- The script handles everything: clone/pull the public repo, copy whitelisted files, sanitize CLAUDE.md, commit, and push.
- If the script exits with "Nothing changed", tell the user the public repo is already up to date.
- Do not modify which files get synced — that list is maintained in `tools/push_public.sh`.
- Public repo: https://github.com/utexasscott/claude-assistant
