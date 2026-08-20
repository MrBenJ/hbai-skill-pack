# Claude Code Skill Pack — Design

**Date:** 2026-08-19
**Repo:** `MrBenJ/claude-code-skill-pack` (public, MIT)
**Status:** Approved by Ben 2026-08-19

## Purpose

A free skill pack for Ben's audience, and a teaching artifact: the theme is
**chaining skills together**. Four skills, two chains, and a README that shows
the work instead of shipping black boxes. Claude Code–specific.

## Repo structure

The repo is simultaneously a **plugin marketplace** and the container for one
plugin named **`hbai`** — the Human Balance AI umbrella plugin. Framing: the
plugin is the growing HBAI toolkit; this pack is what's in it today. Future
free skills get added to the same plugin, so one install keeps paying off.

```
claude-code-skill-pack/
├── .claude-plugin/
│   └── marketplace.json          # name: claude-code-skill-pack, owner: MrBenJ, one plugin entry
├── plugins/
│   └── hbai/
│       ├── .claude-plugin/
│       │   └── plugin.json       # name: hbai, MIT, author Ben Junya
│       └── skills/
│           ├── codex-review/SKILL.md
│           ├── codex-review-loop/SKILL.md
│           ├── context-hygiene/
│           │   ├── SKILL.md
│           │   └── scripts/check_context.py
│           └── smart-compact/
│               ├── SKILL.md
│               └── scripts/extract_session.py
├── codex/
│   └── skills/                   # the mirror pack — Codex-side skills (manual install)
│       ├── claude-review/SKILL.md
│       └── claude-review-loop/SKILL.md
├── README.md
├── LICENSE                       # MIT, copyright Ben Junya
└── docs/superpowers/             # specs + plans, committed — part of "show the work"
```

**Install paths (both documented in README):**

1. Marketplace: `/plugin marketplace add MrBenJ/claude-code-skill-pack`, then
   `/plugin install hbai@claude-code-skill-pack`. Skills invoke as
   `/hbai:codex-review` etc.
2. Manual, zero-friction: copy any folder from `plugins/hbai/skills/` into
   `~/.claude/skills/`. Skills invoke bare: `/codex-review` etc.

**Script location mechanism:** Claude Code has no `$SKILL_DIR` env var. The
documented portable mechanism is the `${CLAUDE_SKILL_DIR}` substitution
variable inside SKILL.md content — it resolves to the skill's own directory in
both install paths. All script invocations use
`python3 ${CLAUDE_SKILL_DIR}/scripts/<script>.py`.

## Skill 1: `/codex-review` — the atomic unit

One code review by OpenAI's Codex CLI. Reviews and reports. Never fixes.

- **Preflight:** `command -v codex`. If absent, stop gracefully with install
  instructions: `npm i -g @openai/codex`, then `codex login`.
- **Target resolution** from the optional argument:
  - No argument → uncommitted changes (staged + unstaged + untracked).
  - Argument containing `..` (e.g. `main..HEAD`) → branch diff.
  - Anything else → specific file paths.
- **Invocation:** `codex exec --sandbox read-only "<review prompt>"` — the
  read-only sandbox guarantees Codex can never edit files. Codex runs in the
  repo cwd and reads the diff itself (it can run `git diff` read-only).
- **Review prompt contract** (what the prompt demands of Codex):
  - Correctness bugs first, then everything else.
  - Concrete `file:line` references on every finding.
  - Severity labels: `[BLOCKER]`, `[MAJOR]`, `[MINOR]`, `[NIT]`.
  - Exactly one machine-readable final line:
    `VERDICT: NO BLOCKING ISSUES` or `VERDICT: BLOCKING ISSUES FOUND`.
    (Blocking = any BLOCKER or MAJOR finding.)
- The skill reports Codex's findings and the verdict, then stops. One shot.

## Skill 2: `/codex-review-loop` — the chaining lesson

A composite skill that **invokes the codex-review skill via the Skill tool**
each round — never inlines the codex logic. The point is composition.

- **Argument:** optional max rounds; default 3.
- **Loop:** invoke codex-review (as `hbai:codex-review` or `codex-review`,
  whichever the current install exposes in the skill list) → read the verdict
  line → if blocking: Claude fixes BLOCKER/MAJOR findings (Codex stays
  read-only; Claude is the fixer), may defer a finding with a stated reason
  (false positive, out of scope, needs product decision) → re-invoke.
- **Stop conditions:** `VERDICT: NO BLOCKING ISSUES`, or round cap reached.
- **Output:** per-round summary — what was found, what was fixed, what was
  deferred and why, and how the loop ended.

## Skills 3 & 4: the Cowork ports

Ported from Ben's Claude Cowork skills. This pair is already a chain:
context-hygiene detects, smart-compact acts.

### `hygiene` → **`context-hygiene`** (renamed)

- Rename everywhere, including smart-compact's description ("when
  /context-hygiene recommends compaction").
- SKILL.md: same behavior (percentage, token counts, four-tier health rating,
  offer compaction at ≥40%), script path via `${CLAUDE_SKILL_DIR}`.

### `smart-compact`

Four-phase flow unchanged (Extract → Summarize → Review → Deliver). Delivery
phase fully adapted from Cowork to Claude Code:

- Handoff file saved to the **current project directory** (not Downloads).
- Continuation instructions: start a fresh Claude Code session (or `/clear`)
  and reference/paste the handoff file.
- Dropped: `computer://` link (plain path instead), sidebar-rename suggestion.
- **Kept: the ASCII tombstone** — it works anywhere and it's a signature touch.

### Script changes (both `check_context.py` and `extract_session.py`)

- **Dual-environment session lookup:** check `~/.claude/projects` (Claude
  Code) first, fall back to `~/mnt/.claude/projects` (Cowork sandbox mount).
  Documented in the README as intentional dual-environment support.
- Remove the hardcoded Cowork sandbox fallback home path.
- Update the model → context-window table with current model IDs
  (claude-fable-5, claude-opus-5, claude-sonnet-5, claude-haiku-4-5); default
  stays 200,000.
- Session-file heuristic stays "most recently modified JSONL, excluding
  subagents" — the live session is written on every turn.
- **Porting risk to verify live:** Cowork JSONL has an `ai-title` entry type;
  Claude Code uses `summary` entries. `extract_session.py` handles both and
  falls back to a title derived from the project directory name.

## Skills 5 & 6: the mirror pack (Codex-side)

Added by Ben mid-design: the same review chain flipped — **Codex drives,
Claude reviews.** Codex CLI (≥0.147.0) supports the same Agent Skills format
(`~/.codex/skills/<name>/SKILL.md`), so the pack ships two Codex skills:

- **`claude-review`** — the atomic unit, mirrored. Preflight `command -v
  claude` (install: `npm i -g @anthropic-ai/claude-code`, then `claude login`
  guidance). Same target resolution. Invokes headless Claude as reviewer:
  `claude -p "<review prompt>"` with an explicit read-only tool allowlist
  (`Read`, `Grep`, `Glob`, read-only `git` commands) — the mirror of Codex's
  `--sandbox read-only`. Same review-prompt contract, same severity labels,
  same exact `VERDICT:` lines. Reports, never fixes.
- **`claude-review-loop`** — composes claude-review. Codex has no Skill tool;
  the idiomatic Codex composition mechanism is a skill that instructs Codex to
  invoke the other skill by name and forbids re-implementing it inline. Same
  loop shape: Claude reviews read-only, Codex fixes, re-review, stop on clean
  verdict or cap (default 3, argument-overridable). Same summary format.

**Repo placement:** `codex/skills/claude-review/` and
`codex/skills/claude-review-loop/` — outside `plugins/` because Claude Code
marketplaces don't serve Codex. Install is manual:
`cp -R codex/skills/* ~/.codex/skills/`.

**Teaching value:** the verdict line is a tool-agnostic interface — the same
contract works no matter which agent is the reviewer and which is the fixer.

**Verification note:** claude-review is verified live against the buggy
fixture. The loop's end-to-end run requires Codex to shell out to `claude`
(network) while fixing files, which Codex's `workspace-write` sandbox blocks;
verify with a full-access `codex exec` run confined to the throwaway fixture
repo, or fall back to verifying the loop's rounds step-by-step manually and
documenting that.

## README

Audience: Ben's users/students receiving this as a freebie. Sections:

1. **What this is** — the HBAI toolkit framing, light HBAI intro (from Ben at
   Human Balance AI, link to site/courses).
2. **Install** — both paths, with the note that manual installs get bare skill
   names and plugin installs get the `/hbai:` prefix.
3. **The four skills** — what each does, usage, example transcripts (stylized).
4. **The chaining pattern** — skill composition taught from both pairs:
   `/codex-review` → `/codex-review-loop` (a skill that calls a skill in a
   loop) and `/context-hygiene` → `/smart-compact` (a skill whose output
   triggers another). Why the atomic skill stays single-purpose and the
   composite reuses it instead of duplicating logic. Plus the mirror pack as
   proof the pattern is tool-agnostic: same chain, roles swapped, same
   verdict contract.
5. **How this was built** — design decisions, the Cowork→Claude Code port and
   what had to change (paths, `$SKILL_DIR` → `${CLAUDE_SKILL_DIR}`, delivery
   phase), and the read-only sandbox choice for Codex.
6. **License / footer** — MIT, light HBAI touch.

## Verification (before "done")

1. Scratch git repo with a deliberately buggy file: run the real
   `codex exec --sandbox read-only` review and confirm findings + verdict line.
2. Execute the codex-review-loop flow end-to-end on that sample; confirm it
   stops on the clean verdict.
3. Run both Python scripts on this machine; confirm they find the live session
   JSONL under `~/.claude/projects` and return sane numbers.
4. Mirror pack: run the real `claude -p` read-only review against the buggy
   fixture and confirm findings + verdict; verify the Codex-side loop per the
   verification note above.
5. Fresh-eyes pass on each SKILL.md per superpowers:writing-skills.

## Constraints

- Commit as we go with clear messages.
- **No push to GitHub until Ben has reviewed the final README.**
- `~/code/hbai/` is not a git repo; git lives only inside this new folder.
