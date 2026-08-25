---
name: claude-review-loop
description: Use when the user invokes /claude-review-loop or asks Codex to have Claude review and fix until clean, to loop Claude reviews, or to keep reviewing until a review passes. Composes the claude-review skill — Claude reviews read-only, Codex fixes, repeat. Accepts an optional round cap (default 3) and review target.
---

# /claude-review-loop — Review, Fix, Repeat (for Codex)

Drive the claude-review skill in a loop: Claude Opus reviews (read-only tool
allowlist), Codex fixes the blocking findings, Claude Opus re-reviews — until
the verdict is clean or the round cap is hit. The roles never blur: **Claude
only reviews, Codex only fixes.**

This is the mirror of the Claude Code–side `codex-review-loop` skill: same
loop, roles swapped.

## The composition rule

Every review round MUST be performed by the **claude-review skill** — invoke
it by name and follow it exactly. Do not re-implement its checks inline:
NEVER run `claude --model opus -p` directly from this skill. This skill contains
zero review logic on purpose: the explicit Opus selection, review prompt,
read-only allowlist, and verdict contract live in exactly one place —
claude-review — so they cannot drift.

| Excuse | Reality |
|--------|---------|
| "Invoking the other skill has overhead; I'll just run claude directly" | The overhead is the point of the lesson. Inlining forks the model selection and review contract. |
| "I need a slightly different prompt this round" | You don't. The contract is fixed; pass a different target argument if needed. |
| "The claude-review skill isn't installed" | Then STOP and tell the user to copy it into ~/.codex/skills/ — don't imitate it. |

## Setup

- **Arguments:** use `/claude-review-loop [max-rounds] [target]`. If the first
  token is a positive integer, it is the cap; otherwise the cap is 3 and the
  entire argument is the target. All remaining text after a cap is the
  target. The target accepts the same forms as claude-review: none,
  `main..HEAD`, or file paths. Examples: `/claude-review-loop`,
  `/claude-review-loop 5`, `/claude-review-loop main..HEAD`, and
  `/claude-review-loop 2 main..HEAD`.
- Keep the target and a round log (target / findings / fixed / deferred) as
  you go — you need them for the final summary.

## The loop (round N of cap)

1. **Review:** on round 1, invoke the claude-review skill with the parsed
   target, or with no argument when no target was supplied. On every later
   round, invoke it with that **same target**. The claude-review range target
   includes both the original range and dirty fixes on top of `HEAD`; never
   narrow a range review to only the fix diff. If round 1 had no supplied
   target and claude-review widened a clean feature branch to a range, retain
   that reported range as the target for every later round.
2. **Read the verdict** — the last `VERDICT:` line in the review output:
   - `VERDICT: NO BLOCKING ISSUES` → stop. Success.
   - `VERDICT: BLOCKING ISSUES FOUND` → continue to step 3.
3. **Fix:** Codex fixes every `[BLOCKER]` and `[MAJOR]` finding. `[MINOR]`
   and `[NIT]` findings are optional — fix them only if trivial while
   already editing that code.
   - A finding may be **deferred** instead of fixed, but only with an
     explicit one-line reason: it's a false positive, it's out of scope for
     this change, or it needs a product decision from the user. Deferring
     silently — skipping a finding without recording why — is not allowed.
4. **Record the round** in the log, then start round N+1. If N was the last
   round under the cap, stop: report the cap was reached and list what
   remains unresolved.

## Final summary

Always end with this accounting, whatever the outcome:

```
## Review loop summary (N rounds)
Target: <target reviewed, including uncommitted changes when present>
Round 1: X findings → fixed: [list] · deferred: [finding — reason]
Round 2: ...
Outcome: clean verdict on round N | round cap reached with M unresolved findings
```

Deferred findings carry into the outcome line only if they were `[BLOCKER]`
or `[MAJOR]` — they are why a cap-reached loop isn't silently "clean".
