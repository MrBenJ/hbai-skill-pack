---
name: codex-review-loop
description: Use when the user invokes /codex-review-loop or asks to review and fix until clean, to loop Codex reviews, or to keep reviewing until a review passes. Composes the codex-review skill — Codex reviews read-only, Claude fixes, repeat. Accepts an optional round cap (default 3) and review target.
argument-hint: "[max-rounds] [main..HEAD | file paths]"
---

# /codex-review-loop — Review, Fix, Repeat

Drive the codex-review skill in a loop: Codex reviews (read-only), Claude
fixes the blocking findings, Codex re-reviews — until the verdict is clean or
the round cap is hit. The roles never blur: **Codex only reviews, Claude only
fixes.**

## The composition rule

Every review round MUST be performed by invoking the **codex-review skill**
via the Skill tool. Find it in the available-skills list — it is named
`codex-review` (manual install) or `hbai:codex-review` (plugin install).

NEVER run `codex` directly from this skill. This skill contains zero review
logic on purpose: the review prompt, the sandbox flag, and the verdict
contract live in exactly one place — codex-review — so they cannot drift.

| Excuse | Reality |
|--------|---------|
| "Invoking the skill has overhead; I'll just run codex exec" | The overhead is the point of the lesson. Inlining forks the review contract. |
| "I need a slightly different prompt this round" | You don't. The contract is fixed; pass a different target argument if needed. |
| "The skill isn't in my list under that exact name" | Look for both names. If neither exists, STOP and tell the user codex-review isn't installed. |

## Setup

- **Arguments:** use `/codex-review-loop [max-rounds] [target]`. If the first
  token is a positive integer, it is the cap; otherwise the cap is 3 and the
  entire argument is the target. All remaining text after a cap is the
  target. The target accepts the same forms as codex-review: none,
  `main..HEAD`, or file paths. Examples: `/codex-review-loop`,
  `/codex-review-loop 5`, `/codex-review-loop main..HEAD`, and
  `/codex-review-loop 2 main..HEAD`.
- Keep the target and a round log (target / findings / fixed / deferred) as
  you go — you need them for the final summary.

## The loop (round N of cap)

1. **Review:** on round 1, invoke the codex-review skill with the parsed
   target, or with no argument when no target was supplied. On every later
   round, invoke it with that **same target**. The codex-review range target
   includes both the original range and dirty fixes on top of `HEAD`; never
   narrow a range review to only the fix diff. If round 1 had no supplied
   target and codex-review widened a clean feature branch to a range, retain
   that reported range as the target for every later round.
2. **Read the verdict** — the last `VERDICT:` line in the review output:
   - `VERDICT: NO BLOCKING ISSUES` → stop. Success.
   - `VERDICT: BLOCKING ISSUES FOUND` → continue to step 3.
3. **Fix:** Claude fixes every `[BLOCKER]` and `[MAJOR]` finding. `[MINOR]`
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
