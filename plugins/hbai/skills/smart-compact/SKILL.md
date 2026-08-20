---
name: smart-compact
description: Use when the user invokes /smart-compact, asks to compact or summarize the conversation before starting fresh, says context is getting too long, or when /context-hygiene recommends compaction. Human-in-the-loop alternative to blind compaction — nothing gets discarded without the user's sign-off.
---

# /smart-compact — Human-in-the-Loop Compaction

Smart Compact is a safe alternative to blind compaction. It generates a
summary of the full conversation, lets the user review and refine it, then
delivers a handoff document they can use to continue seamlessly in a fresh
session — with nothing important lost.

The workflow has four phases:
1. **Extract** — read the full conversation from the session log
2. **Summarize** — generate a structured handoff document
3. **Review** — iterate with the user until they're satisfied
4. **Deliver** — save the file, give instructions, close with the tombstone

---

## Phase 1: Extract conversation data

Run the bundled extraction script (`${CLAUDE_SKILL_DIR}` is Claude Code's
substitution for this skill's own directory, so this works for both plugin
and manual installs):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_session.py
```

This returns a JSON object with:
- `title` — the session's AI-generated title
- `date` — when the session started (YYYY-MM-DD)
- `percentage` — context window usage
- `messages` — the conversation in `{role, content}` format
- `error` — non-null if something went wrong

If `error` is non-null, report it and stop.

---

## Phase 2: Generate the handoff document

Using the extracted messages, write a structured summary in this exact
format. Be thorough — the goal is that someone (or Claude) reading this file
cold could pick up right where things left off without missing anything
important.

```markdown
# [Session Title] — Handoff Summary
**Date:** YYYY-MM-DD
**Context at compact:** X% (X,XXX / 200,000 tokens)

## What we were working on
[1–2 sentences: the main goal or project of this session]

## Key context & background
[Bullet list: important background, preferences, constraints, or facts the user shared that future work depends on]

## What was built / completed
[Bullet list: files created or modified, tasks finished, decisions implemented]

## Decisions made
[Bullet list: choices made and the reasoning behind them, so they don't get relitigated]

## Open threads
[Bullet list: things in progress, unresolved, or explicitly mentioned as "next"]

## To continue in a new session
Paste this as your first message to a fresh Claude session:

---
[A self-contained resume prompt written in first person as the user. 3–6 sentences. Should re-establish who the user is, what project they're on, what was just completed, and what they want to do next. Concrete enough that Claude can pick up without re-reading anything.]
---
```

After drafting, show it to the user and ask:
**"Does this capture everything? Let me know if anything is missing, wrong,
or needs more detail before I save the file."**

---

## Phase 3: Review loop

Iterate based on user feedback. Keep refining until the user explicitly
approves — something like "looks good", "ship it", "that's it", "perfect",
etc.

When asking for feedback, prompt them to consider:
- Is the resume prompt specific enough for a fresh Claude to pick up seamlessly?
- Any decisions or context that isn't captured?
- Any files or work that should be listed?

Don't move to Phase 4 until approval is confirmed.

---

## Phase 4: Deliver

### 4a. Build the filename

Compute the filename from the session title and date:
- Take the `title` from the extraction output
- Lowercase it, replace spaces and special characters with hyphens, strip leading/trailing hyphens
- Format: `[sanitized-title]-smart-compact-[date].md`
- Example: `claude-code-skill-pack-smart-compact-2026-08-19.md`

Save the approved handoff document to the **current project directory** using
the Write tool.

### 4b. Instructions to the user

Tell the user:

1. **The file's path** — plain and copyable.
2. **How to continue** — start a fresh Claude Code session in this same
   directory (new `claude`, or `/clear` in this one) and open with:
   > Read `[handoff file path]` and pick up where it leaves off.

### 4c. The tombstone

After all instructions, end your final message with this exact block. Do not
modify it, do not add anything after it:

```
=======================================
======== CONVERSATION COMPACTED ========
====PLEASE CONTINUE IN ANOTHER WINDOW===
=======================================
```

This marks the conversation as finished. If someone opens this session by
accident later, they'll see immediately that the work has continued
elsewhere.
