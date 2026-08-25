# hbai-skill-pack

Hi! I'm Ben. I'm a software engineer specialized in Agentic AI and personal automation.

This repo contains agent skills I use on a daily basis with both Claude Code (my personal preference) and Codex. 

These skills are free to use. To get the most out of these skills, you'll need both [Claude Code](https://code.claude.com/docs/en/quickstart) and [Codex](https://chatgpt.com/codex/) installed on your CLI. My daily driver is a Macbook Pro M series machine, and I use iTerm2 as my terminal emulator

I run an AI education and consultancy firm called [Human Balance AI](https://humanbalanceai.com). If you're looking for help creating fully autonomous workflows with AI, [book a call with me](https://humanbalanceai.com/consultation) and I can help you navigate the wild world of Agentic AI in simple, easy to understand language. 



## Install

**Agent Install (recommended)** 
Have your agent install this skill pack for you. Copy this prompt into Claude Code or Codex. 

```md
Install the HBAI skill pack at https://github.com/MrBenJ/hbai-skill-pack for either Claude Code or Codex. Ask me any clarifying questions if anything is unclear. 
```

**Path 1 — plugin** In Claude Code:

```
/plugin marketplace add MrBenJ/hbai-skill-pack
/plugin install hbai@hbai-skill-pack
```

Skills are invoked with the plugin prefix: `/hbai:codex-review`, `/hbai:handoff`, etc.

**Path 2 — manual, zero friction.** Copy any skill folder into your personal skills
directory:

```bash
git clone https://github.com/MrBenJ/hbai-skill-pack
cp -R hbai-skill-pack/plugins/hbai/skills/* ~/.claude/skills/
```

Skills are invoked bare: `/codex-review`, `/smart-compact`, etc. (The examples below
use the bare names.)

**Path 3 — the Codex CLI skills.** The portable `handoff` skill and the
`claude-review` / `claude-review-loop` pair work with OpenAI's Codex CLI. Copy them
into Codex's skills directory:

```bash
cp -R hbai-skill-pack/codex/skills/* ~/.codex/skills/
```

In Codex they're invoked as `/handoff`, `/claude-review`, and
`/claude-review-loop`.

## The skills

### `/codex-review` — one-shot outside code review

Runs OpenAI's Codex CLI as an outside reviewer over your uncommitted changes, a branch
diff, or specific files — in a **read-only sandbox**, so it can never touch your code.
It reports severity-labeled findings with `file:line` references and ends with a
machine-readable verdict. The CLI transcript and footer are discarded; only Codex's
final reply is relayed, with each finding exactly once. It never fixes anything.

With no target, a dirty tree reviews the working changes. A clean feature branch with
commits ahead of the default branch automatically reviews `<default>..HEAD` and says
so; a clean default branch stops instead of reviewing nothing. An explicit range also
includes any uncommitted changes on top of `HEAD`.

Requires the Codex CLI: `npm i -g @openai/codex`, then `codex login`. The skill checks
both the binary and logged-in state before starting.

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
verdict or the round cap. Usage is `/codex-review-loop [max-rounds] [target]`; the cap
defaults to 3, and the target accepts a range or file paths. The same target is retained
for every round, with uncommitted fixes included on top of a range.

```
> /codex-review-loop 2 main..HEAD

⏺ Round 1: reviewing main..HEAD… 1 finding → fixing stats.js:3
⏺ Round 2: reviewing main..HEAD + working tree… clean ✓

  ## Review loop summary (2 rounds)
  Target: main..HEAD, including uncommitted changes on top of HEAD
  Round 1: 1 finding → fixed: [MAJOR] stats.js:3 off-by-one · deferred: none
  Round 2: 0 findings → fixed: none · deferred: none
  Outcome: clean verdict on round 2
```

(That transcript is real — it's the target-threading verification run, condensed.)

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

### `/handoff` — continue with another coding agent

Creates one paste-ready prompt so another coding agent can continue the current
work without access to this conversation. It reconciles the goal and decisions
from the chat with the live repository state, includes the work already completed,
verification, constraints, and concrete next steps, and stays vendor-neutral so
you can paste it into whichever coding subscription you want to use next.

The skill is read-only: it does not continue the implementation or write a handoff
file. Its single-block output contract also makes it useful as a small composition
primitive inside larger skills. Pass an optional focus when you want to steer the
next agent: `/handoff finish the failing integration test`. A composing skill can
invoke `handoff` after a manual install or `hbai:handoff` from the plugin, provide
its known context and desired format, then relay the content of the returned block.

Use `/smart-compact` to compress the current session into a reviewed handoff file;
use `/handoff` when you only need a prompt to paste into a different coding agent.

````text
> /handoff focus next on the failing integration test

⏺ ```text
  Continue the work in `/path/to/project` on the current feature branch.
  Preserve the existing working-tree changes. The implementation is complete;
  the remaining task is to diagnose and fix the failing integration test in…
  ```
````

### `/claude-review` — one-shot outside code review (Codex CLI)

The `codex-review` pair with the roles swapped: in these two skills Codex is the
driver and Claude is the outside reviewer. `/claude-review` runs Claude Code headless
with the Opus model explicitly selected (`claude --model opus -p`) and a **read-only
tool allowlist**, so it can never touch your code — same review prompt, same severity
labels, same verdict strings as `/codex-review`. It reports each finding once and
never fixes. Like its mirror, no argument on a clean feature branch widens to
`<default>..HEAD`, a clean default branch stops, and an explicit range includes dirty
work on top of `HEAD`.

Codex launches Claude outside its own sandbox so Claude can use the host's existing
login and network access. Claude still remains read-only because the explicit tool
allowlist denies editing tools.

Requires Claude Code: `npm i -g @anthropic-ai/claude-code`, then run `claude` once
to log in.

```
> /claude-review

⏺ Running headless Claude with a read-only tool allowlist over your uncommitted changes…

  [BLOCKER] stats.js:4 — Off-by-one loop bound: `i <= arr.length` adds
  arr[arr.length] (undefined), so every sum() result is NaN.
  [MINOR] stats.js:11 — average([]) divides by zero and returns NaN with no guard.

  VERDICT: BLOCKING ISSUES FOUND
```

### `/claude-review-loop` — review, fix, repeat (Codex CLI)

The counterpart of `/codex-review-loop`. Each round invokes the `claude-review`
skill — Claude reviews read-only, Codex fixes the blocking findings, repeat — until
the verdict is clean or the round cap is hit. Usage is
`/claude-review-loop [max-rounds] [target]`; the same range or file target is passed
through every round, including the working-tree fixes layered on a range. Findings
can be deferred instead of fixed, but only with a stated reason, and the final summary
names the target and accounts for every finding.

```
> /claude-review-loop

⏺ Round 1: invoking claude-review… 2 findings → fixing stats.js:4, deferring the [MINOR]
⏺ Round 2: invoking claude-review… clean ✓

  ## Review loop summary (2 rounds)
  Target: uncommitted changes
  Round 1: 2 findings → fixed: [BLOCKER] stats.js:4 off-by-one ·
           deferred: [MINOR] average([]) NaN — API decision for the caller
  Outcome: clean verdict on round 2
```

(Also a real transcript — Codex drove this loop against the same buggy fixture
during this repo's build.)

## How this was built

This pack was designed, planned, and verified in the open. The actual working
documents are in [`docs/superpowers/`](docs/superpowers/): the design spec and the
task-by-task implementation plan.

**Design decisions worth stealing:**

- **The reviewer can never write.** Codex runs under `--sandbox read-only`; headless Claude runs with a read-only `--allowedTools` allowlist.
- **Exact-string verdicts.** The one rigid `VERDICT:` line costs the reviewer nothing and lets anything downstream — the loop skills here, your own CI, a pre-commit ritual — key off it without parsing prose.
- **A round cap as a safety valve.** Review loops can oscillate (fix A, reviewer now wants B, fix B, reviewer misses A…). Cap it, and make the cap-reached outcome honest: unresolved findings are listed, never silently dropped.
- **Deferrals over silent skips.** The loop may decline to fix a finding (false positive, out of scope) but must say so with a reason. The final summary accounts for every finding of every round.
- **Handoffs as an atomic primitive.** `/handoff` has one job and a stable output shape: turn verified session and workspace state into a portable continuation prompt. Other skills can invoke it and relay the result without inheriting prompt-generation logic of their own.

**The Cowork → Claude Code port** (`context-hygiene` and `smart-compact` started life as Claude Cowork skills):

- **Session paths differ.** Cowork's sandbox mounts session logs at
  `~/mnt/.claude/projects`; Claude Code keeps them at `~/.claude/projects`. Both scripts now check the Claude Code path first and fall back to the Cowork mount, so the skills work in both environments.
- **`$SKILL_DIR` doesn't exist in Claude Code.** Cowork exposes the skill's directory as an env var; Claude Code instead substitutes `${CLAUDE_SKILL_DIR}` inside the SKILL.md itself. Every script invocation was rewritten to use it — which is also what makes both install paths (plugin and manual copy) work unchanged.
- **The session-file heuristic got sharpened.** "Most recently modified JSONL" was safe inside Cowork's one-session sandbox, but Claude Code users run concurrent sessions. The scripts now scope the search to the current project's folder (Claude Code encodes your working directory into the folder name) before falling back.

Every skill was verified live before shipping. The latest Codex review hardening run
used Codex CLI 0.147.0 against a scratch repo: final-message-only capture returned one
copy of a blocking finding and verdict, a clean feature branch widened to
`main..HEAD`, a clean `main` stopped, a two-round `main..HEAD` loop retained the range
plus its working-tree fix, and an empty `CODEX_HOME` stopped at login preflight. The
ported scripts were verified against a live Claude Code session log.

## License

[MIT](LICENSE) © 2026 Ben Junya

---

*From Ben at [**Human Balance AI**](https://humanbalanceai.com?origin=hbai-skill-pack) — practical AI skills for people who'd rather understand their tools than worship them. This pack is free; share it.
