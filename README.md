# claude-code-skill-pack

**Free Claude Code skills from [Ben Junya](https://github.com/MrBenJ) at Human Balance AI.**

This repo installs as one plugin — **`hbai`**, the Human Balance AI toolkit. This pack
is what's in it today; new free skills land in the same plugin, so one install keeps
paying off.

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
OpenAI's Codex CLI (same review pair, roles swapped — see [The mirror pack](#the-mirror-pack)):

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

## The mirror pack

`codex/skills/` ships the same review pair with the roles swapped, as skills for
OpenAI's Codex CLI:

| | Claude Code pack | Codex mirror |
|---|---|---|
| Driver / fixer | Claude | Codex |
| Reviewer (read-only) | Codex, `--sandbox read-only` | Claude, `claude -p` + read-only `--allowedTools` |
| Skills | `/codex-review`, `/codex-review-loop` | `claude-review`, `claude-review-loop` |
| Verdict contract | `VERDICT: …` exact strings | **identical** |

Same review prompt, same verdict strings — only the plumbing differs (Claude Code's
loop invokes the review skill via the Skill tool; Codex's loop references the
`claude-review` skill by name).

## How this was built

This pack was designed, planned, and verified in the open. The actual working
documents are in [`docs/superpowers/`](docs/superpowers/): the design spec and the
task-by-task implementation plan.

**Design decisions worth stealing:**

- **The reviewer can never write.** Codex runs under `--sandbox read-only`; headless
  Claude runs with a read-only `--allowedTools` allowlist. Separating "the thing that
  finds problems" from "the thing that changes code" isn't just safety — it's what
  makes the loop's roles legible.
- **Exact-string verdicts.** The one rigid `VERDICT:` line costs the reviewer nothing
  and lets anything downstream — the loop skills here, your own CI, a pre-commit
  ritual — key off it without parsing prose.
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
  the cross-reference in `smart-compact`'s description — skills that mention each
  other by name have to be renamed together.

Every skill was verified live before shipping: the review skills against a scratch
repo with planted bugs (three real Codex rounds to a clean verdict), the ported
scripts against a live Claude Code session log.

## License

[MIT](LICENSE) © 2026 Ben Junya

---

*From Ben at **Human Balance AI** — practical AI skills for people who'd rather
understand their tools than worship them. This pack is free; share it.*
