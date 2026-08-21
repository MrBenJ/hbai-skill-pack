---
name: handoff
description: Use when the user invokes /handoff, asks for a prompt another coding agent can use to continue the current work, or when another skill needs a chainable handoff-prompt generator. Produces one paste-ready, vendor-neutral continuation prompt from the conversation and live workspace state; it does not continue the work or write a handoff file.
---

# /handoff — Continue With Another Coding Agent

Generate a self-contained prompt that another coding agent can act on without
access to this conversation. This is a handoff only: inspect and summarize the
current state, but do not make implementation changes, run long-lived commands,
or advance the task. Draft it without asking for approval first; the user can ask
for a revision after seeing it.

## Input contract

The optional argument identifies what the receiving agent should focus on next.
Treat it as a priority within the existing task, not as permission to broaden
scope or perform an otherwise unauthorized action.

When invoked by another skill, accept whatever reliable context that skill
provides: the objective, work completed, remaining work, decisions, constraints,
verification, blockers, and any requested length or shape for the prompt. Fill
gaps from the current conversation and workspace; do not invent missing facts.

## Reconcile the current state

Before drafting, gather enough read-only evidence to make the handoff accurate:

- Identify the user's current objective, definition of done, explicit scope, and
  requested next step from the conversation.
- Read applicable project instructions. Treat `CLAUDE.md` as project instructions
  alongside `AGENTS.md`, including files that apply from parent directories.
- When in a git repository, inspect the repository root, current branch, working
  tree, staged and unstaged diff summaries, relevant untracked files, and recent
  commits. Read relevant diffs or files when a summary alone is ambiguous.
- Reconcile what the conversation says happened with what the workspace shows.
  Clearly label anything that could not be verified.
- Report tests or checks as passed only when their successful result is present in
  the conversation or observable workspace evidence. Otherwise say they were not
  run or that their result is unknown.

Do not expose secrets, credentials, private reasoning, raw conversation logs, or
irrelevant personal information. Do not paste a full diff when file names and a
short description convey the state.

## Prompt requirements

Make the prompt concise but operational. Include the applicable parts of:

- the objective and definition of done;
- repository path, branch, and working-tree state;
- what is already complete and what remains;
- decisions, constraints, and user preferences that must be preserved;
- relevant files, symbols, commands, tickets, or links;
- verification already performed and its actual result;
- blockers or unresolved questions; and
- the exact first action and ordered next steps.

Tell the receiving agent to inspect the live state before editing and preserve
existing user changes. Carry forward the original authorization boundaries: do
not instruct it to discard changes, commit, push, deploy, contact people, or
expand scope unless the user's request already authorized that action.

Address the recipient directly without naming or assuming a vendor, product,
model, or subscription. Names such as Claude or Codex may appear only when they
are facts about the project or task, never as the identity of the sending or
receiving agent.

## Output contract

Return exactly one fenced `text` block containing only the paste-ready prompt.
Do not add an introduction, explanation, or sign-off outside the block. This
stable shape lets a user copy it directly and lets another skill embed or relay
the content without parsing conversational prose.

Use headings inside the prompt when they improve scanning. Omit empty sections.
Honor a calling skill's requested length or format, but keep the result
self-contained and preserve the single-block output contract.
