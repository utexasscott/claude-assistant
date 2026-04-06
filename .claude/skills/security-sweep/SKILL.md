---
name: security-sweep
description: Use when running a security sweep, checking committed files for personal data, scanning for PII, auditing the repo for sensitive content, or doing a privacy check.
argument-hint: "[brief|thorough] — default: thorough"
metadata:
  visibility: public
---

## What This Skill Does

Scans committed files for two threats:
- **Credentials** — API keys, secrets, or hardcoded tokens in any committed file
- **Personal data** — PII or user-specific proper nouns in files that sync to the public repo

## Modes

- **brief** — scans only staged/modified files (fast pre-commit gate; called by session-end)
- **thorough** — scans all tracked files (full audit; default when invoked directly)

## Steps

1. Read `workflows/public/security_sweep.md` in full.
2. Determine the mode:
   - If an argument was provided, use it (`brief` or `thorough`)
   - If no argument was provided, use `thorough`
3. Follow the workflow as written, using the determined mode throughout.
