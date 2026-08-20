# claude-code-skill-pack

**Free Claude Code skills from [Ben Junya](https://github.com/MrBenJ) at Human Balance AI.**

This repo installs as one plugin — **`hbai`**, the Human Balance AI toolkit. This pack
is what's in it today; new free skills land in the same plugin, so one install keeps
paying off.

But the skills are only half the gift. The other half is the lesson: **how to chain
skills together**. Every skill here is either an atomic building block or a composite
that reuses one — and the whole repo shows its work, from design docs to the port
notes. Read it like a tutorial, not just a toolbox.

## Install

**Path 1 — plugin (recommended).** In Claude Code:

```
/plugin marketplace add MrBenJ/claude-code-skill-pack
/plugin install hbai@claude-code-skill-pack
```

Skills are invoked with the plugin prefix: `/hbai:codex-review`, `/hbai:smart-compact`, etc.

**Path 2 — manual, zero friction.** Copy any skill folder into your personal skills
directory:

```bash
git clone https://github.com/MrBenJ/claude-code-skill-pack
cp -R claude-code-skill-pack/plugins/hbai/skills/* ~/.claude/skills/
```

Skills are invoked bare: `/codex-review`, `/smart-compact`, etc. (The examples below
use the bare names.)

**Bonus — the Codex mirror.** The `codex/skills/` folder contains two skills for
OpenAI's Codex CLI (same review chain, roles swapped — see [The mirror pack](#the-mirror-pack)):

```bash
cp -R claude-code-skill-pack/codex/skills/* ~/.codex/skills/
```

## The four skills

### `/codex-review` — one-shot outside code review

Runs OpenAI's Codex CLI as an outside reviewer over your uncommitted changes, a branch
diff, or specific files — in a **read-only sandbox**, so it can never touch your code.
It reports severity-labeled findings with `file:line` references and ends with a
machine-readable verdict. It never fixes anything.

Requires the Codex CLI: `npm i -g @openai/codex`, then `codex login`.

```
> /codex-review

⏺ Running Codex in a read-only sandbox over your uncommitted changes…

  [MAJOR] stats.js:4 — Loop bound `i <= arr.length` reads arr[arr.length]
  (undefined), so every sum() result is NaN.

  VERDICT: BLOCKING ISSUES FOUND
```

Also: `/codex-review main..HEAD` (branch diff) or `/codex-review src/auth.ts` (files).

### `/codex-review-loop` — review, fix, repeat

The composite. Each round it **invokes `/codex-review` as a skill** — it contains zero
review logic of its own. If the verdict is blocking, Claude fixes the findings (Codex
stays read-only; Claude is the fixer), then re-invokes the review. Stops on a clean
verdict or the round cap (default 3 — `/codex-review-loop 5` raises it).

```
> /codex-review-loop

⏺ Round 1: invoking /codex-review… 1 finding → fixing stats.js:4
⏺ Round 2: invoking /codex-review… 1 finding → fixing stats.js:11
⏺ Round 3: invoking /codex-review… clean ✓

  ## Review loop summary (3 rounds)
  Round 1: 1 finding → fixed: [MAJOR] stats.js:4 off-by-one · deferred: none
  Round 2: 1 finding → fixed: [MAJOR] stats.js:11 empty-array NaN · deferred: none
  Outcome: clean verdict on round 3
```

(That transcript is real — it's the verification run from this repo's build, condensed.)

### `/context-hygiene` — context window health check

Reads your live session log and reports how full the context window is, with a
plain-language health rating. When it's crowded (≥40%), it recommends `/smart-compact`.

```
> /context-hygiene

  **47.3%** · 94,612 / 200,000 tokens
  ⚠️ Caution — Approaching unreliable levels of context size. Consider compaction.

  Would you like me to run /smart-compact to compress this conversation and
  free up context?
```

### `/smart-compact` — human-in-the-loop compaction

A safe alternative to blind compaction. It extracts your full conversation from the
session log, drafts a structured handoff document (what you were doing, decisions
made, open threads, and a paste-ready resume prompt), **iterates on it with you until
you approve**, then saves it to your project directory and closes the session with a
tombstone. Nothing gets discarded without your sign-off.

```
> /smart-compact

⏺ Extracted 28 messages (80.5% context used). Here's the draft handoff…
  Does this capture everything?

> add the bit about the staging database decision

⏺ Updated. Saved to ./skill-pack-build-smart-compact-2026-08-19.md
  Start a fresh session here and open with:
  "Read skill-pack-build-smart-compact-2026-08-19.md and pick up where it leaves off."

  =======================================
  ======== CONVERSATION COMPACTED ========
  ====PLEASE CONTINUE IN ANOTHER WINDOW===
  =======================================
```

## The chaining pattern

This pack contains two skill chains, and they demonstrate two different ways skills
compose.

### Chain 1: a skill that calls a skill — `/codex-review` → `/codex-review-loop`

`/codex-review-loop` never runs `codex` itself. Every round goes through the Skill
tool, invoking `/codex-review` like a function call. The two skills communicate
through a deliberately rigid interface — the verdict contract:

```
VERDICT: NO BLOCKING ISSUES
VERDICT: BLOCKING ISSUES FOUND
```

Exact strings, always the last line of the review. The loop doesn't parse prose or
guess sentiment; it keys off one machine-readable line. That line is an API.

**Why not just put the codex command inside the loop skill?** The same reason you
don't copy-paste a function body everywhere you need it:

- **Single source of truth.** The review prompt, the sandbox flag, and the verdict
  contract live in one file. Tighten the prompt once and both the one-shot review and
  the loop get the improvement. Inline it and the two copies drift.
- **Independent testing.** The atomic skill was verified against a deliberately buggy
  fixture on its own, before the loop existed. A composite built on a proven unit
  only has to prove the *composition*.
- **Reuse beyond this pack.** Anything can key off the verdict line — your own CI
  skill, a pre-commit ritual, a different loop with different fix rules.

### Chain 2: a skill whose output triggers another — `/context-hygiene` → `/smart-compact`

This pair chains differently: no Skill-tool call, no loop. `/context-hygiene` is a
*detector* — it measures and rates. At ≥40% it ends by offering `/smart-compact`, the
*actor*. The handoff is conversational: the detector's recommendation becomes the
user's (or Claude's) next invocation.

Same principle, different mechanism: the detector doesn't know how to compact, and
the compactor doesn't know how to measure. Each stays single-purpose; the chain lives
in the recommendation.

### The pattern in one sentence

**Atomic skills do one thing and expose a stable output; composite skills orchestrate
atomic ones through that output instead of reimplementing them.**

## The mirror pack

To prove the pattern is tool-agnostic, `codex/skills/` ships the review chain with
the roles swapped, as skills for OpenAI's Codex CLI:

| | Claude Code pack | Codex mirror |
|---|---|---|
| Driver / fixer | Claude | Codex |
| Reviewer (read-only) | Codex, `--sandbox read-only` | Claude, `claude -p` + read-only `--allowedTools` |
| Skills | `/codex-review`, `/codex-review-loop` | `claude-review`, `claude-review-loop` |
| Verdict contract | `VERDICT: …` exact strings | **identical** |

Two things worth noticing:

- **The verdict contract didn't change.** The interface between "reviewer" and
  "fixer" doesn't care which model plays which role — that's what makes it a real
  interface.
- **The composition mechanism did.** Claude Code has a Skill tool, so the loop
  invokes the review skill programmatically. Codex composes by reference: the loop
  skill names the `claude-review` skill and forbids re-implementing it inline. Same
  discipline, different plumbing.

## How this was built

This pack practices what it teaches — it was designed, planned, and verified in the
open. The actual working documents are in [`docs/superpowers/`](docs/superpowers/):
the design spec and the task-by-task implementation plan.

**Design decisions worth stealing:**

- **The reviewer can never write.** Codex runs under `--sandbox read-only`; headless
  Claude runs with a read-only `--allowedTools` allowlist. Separating "the thing that
  finds problems" from "the thing that changes code" isn't just safety — it's what
  makes the loop's roles legible.
- **Exact-string verdicts.** Prose is for humans; contracts are for chains. The one
  rigid line costs the reviewer nothing and makes every consumer trivial.
- **A round cap as a safety valve.** Review loops can oscillate (fix A, reviewer now
  wants B, fix B, reviewer misses A…). Cap it, and make the cap-reached outcome
  honest: unresolved findings are listed, never silently dropped.
- **Deferrals over silent skips.** The loop may decline to fix a finding (false
  positive, out of scope) but must say so with a reason. The final summary accounts
  for every finding of every round.

**The Cowork → Claude Code port** (`context-hygiene` and `smart-compact` started life
as Claude Cowork skills):

- **Session paths differ.** Cowork's sandbox mounts session logs at
  `~/mnt/.claude/projects`; Claude Code keeps them at `~/.claude/projects`. Both
  scripts now check the Claude Code path first and fall back to the Cowork mount, so
  the skills work in both environments.
- **`$SKILL_DIR` doesn't exist in Claude Code.** Cowork exposes the skill's directory
  as an env var; Claude Code instead substitutes `${CLAUDE_SKILL_DIR}` inside the
  SKILL.md itself. Every script invocation was rewritten to use it — which is also
  what makes both install paths (plugin and manual copy) work unchanged.
- **The session-file heuristic got sharpened.** "Most recently modified JSONL" was
  safe inside Cowork's one-session sandbox, but Claude Code users run concurrent
  sessions. The scripts now scope the search to the current project's folder (Claude
  Code encodes your working directory into the folder name) before falling back.
- **Delivery had to change worlds.** Cowork's `smart-compact` saved to Downloads,
  linked with `computer://`, and suggested a sidebar rename. The Claude Code version
  saves to your project directory and hands you a resume line for a fresh session.
  The tombstone survived the port untouched — some things are load-bearing *and* fun.
- **One rename with teeth.** `hygiene` became `context-hygiene`, which meant chasing
  the cross-reference in `smart-compact`'s description — the exact kind of coupling
  the chaining pattern warns you about.

Every skill was verified live before shipping: the review skills against a scratch
repo with planted bugs (three real Codex rounds to a clean verdict), the ported
scripts against a live Claude Code session log.

## License

[MIT](LICENSE) © 2026 Ben Junya

---

*From Ben at **Human Balance AI** — practical AI skills for people who'd rather
understand their tools than worship them. This pack is free; share it.*
