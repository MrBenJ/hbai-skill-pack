# Claude Code Skill Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the public `MrBenJ/hbai-skill-pack` repo: a plugin-marketplace repo containing the `hbai` plugin with four Claude Code skills (codex-review, codex-review-loop, context-hygiene, smart-compact), a two-skill Codex-side mirror pack (claude-review, claude-review-loop), and a teaching README.

**Architecture:** One repo = one marketplace + one plugin (`plugins/hbai/`) + a Codex-side mirror (`codex/skills/`). Two skill chains: an atomic Codex reviewer composed by a fix loop, and a context-health detector that triggers a compactor — plus the review chain mirrored with roles swapped (Codex drives, Claude reviews). Skills locate bundled scripts via the `${CLAUDE_SKILL_DIR}` substitution variable so both install paths (plugin, manual copy) work.

**Tech Stack:** Claude Code skills (Markdown + YAML frontmatter), Python 3 stdlib scripts, OpenAI Codex CLI (`codex exec --sandbox read-only`), git + gh.

**Spec:** `docs/superpowers/specs/2026-08-19-hbai-skill-pack-design.md`

## Global Constraints

- Repo root: `/Users/bjunya/code/hbai/opensource/hbai-skill-pack` (git already initialized on `main`; parent dirs are NOT git repos — never run git above the repo root).
- Plugin name is exactly `hbai`; marketplace name is exactly `hbai-skill-pack`.
- MIT license, copyright holder "Ben Junya".
- Verdict contract, exact strings: `VERDICT: NO BLOCKING ISSUES` and `VERDICT: BLOCKING ISSUES FOUND`. Blocking = any `[BLOCKER]` or `[MAJOR]` finding.
- Severity labels, exact: `[BLOCKER]`, `[MAJOR]`, `[MINOR]`, `[NIT]`.
- All script invocations in SKILL.md files use `python3 ${CLAUDE_SKILL_DIR}/scripts/<script>.py` — never `$SKILL_DIR` (doesn't exist in Claude Code).
- codex-review-loop must invoke the codex-review skill via the Skill tool — never inline the codex invocation. Mirror rule on the Codex side: claude-review-loop must invoke the claude-review skill by name and forbid inlining the `claude -p` invocation.
- Mirror pack lives at `codex/skills/claude-review/` and `codex/skills/claude-review-loop/` (Agent Skills format; manual install via `cp -R codex/skills/* ~/.codex/skills/`). Same verdict strings and severity labels as the Claude Code pair.
- Session lookup in both Python scripts: `~/.claude/projects` first, then `~/mnt/.claude/projects`.
- Commit after every task. **Do not create the GitHub remote or push until Ben approves the final README.**

---

### Task 1: Repo scaffolding (LICENSE, .gitignore, marketplace.json, plugin.json)

**Files:**
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `.claude-plugin/marketplace.json`
- Create: `plugins/hbai/.claude-plugin/plugin.json`

**Interfaces:**
- Produces: plugin `hbai` at source `./plugins/hbai` — every later skill lives under `plugins/hbai/skills/<skill-name>/`.

- [ ] **Step 1: Write LICENSE** — standard MIT text, `Copyright (c) 2026 Ben Junya`.

- [ ] **Step 2: Write .gitignore**

```
.DS_Store
__pycache__/
*.pyc
```

- [ ] **Step 3: Write `.claude-plugin/marketplace.json`**

```json
{
  "name": "hbai-skill-pack",
  "owner": {
    "name": "Ben Junya",
    "url": "https://github.com/MrBenJ"
  },
  "description": "Free Claude Code skills from Human Balance AI — built to teach skill chaining.",
  "plugins": [
    {
      "name": "hbai",
      "source": "./plugins/hbai",
      "description": "The Human Balance AI toolkit: codex-review, codex-review-loop, context-hygiene, smart-compact."
    }
  ]
}
```

- [ ] **Step 4: Write `plugins/hbai/.claude-plugin/plugin.json`**

```json
{
  "name": "hbai",
  "displayName": "HBAI Toolkit",
  "version": "1.0.0",
  "description": "Human Balance AI's free skill pack — two skill chains: Codex-powered code review (atomic reviewer + fix loop) and context health (detector + compactor).",
  "author": {
    "name": "Ben Junya",
    "url": "https://github.com/MrBenJ"
  },
  "homepage": "https://github.com/MrBenJ/hbai-skill-pack",
  "repository": "https://github.com/MrBenJ/hbai-skill-pack",
  "license": "MIT",
  "keywords": ["skills", "code-review", "codex", "context", "compaction"]
}
```

- [ ] **Step 5: Validate** — `python3 -m json.tool` on both JSON files; expect clean parse. If the `claude plugin validate` CLI subcommand exists on this machine, run it against the repo root too.

- [ ] **Step 6: Commit** — `git add -A && git commit -m "Scaffold marketplace repo: MIT license, marketplace + hbai plugin manifests"`

---

### Task 2: `/codex-review` skill + live verification

**Files:**
- Create: `plugins/hbai/skills/codex-review/SKILL.md`
- Scratch (not committed): `<scratchpad>/codex-verify/` — throwaway git repo with a planted bug

**Interfaces:**
- Produces: the verdict contract (exact strings in Global Constraints) and severity labels; consumed by codex-review-loop and the README.

- [ ] **Step 1: Write SKILL.md.** Frontmatter:

```yaml
---
name: codex-review
description: Run ONE code review of the current work using OpenAI's Codex CLI and report findings — never fix anything. Use when the user invokes /codex-review or asks for a Codex review / second-opinion review of uncommitted changes, a branch diff (e.g. main..HEAD), or specific files. Codex runs in a read-only sandbox; output is severity-labeled findings with file:line references and a final VERDICT line.
argument-hint: "[main..HEAD | file paths]"
---
```

Body must contain, in order:
1. **Preflight:** run `command -v codex`. If missing, stop and tell the user: install with `npm i -g @openai/codex`, then authenticate with `codex login`. Do not attempt the review.
2. **Resolve the review target** from the argument: none → uncommitted work (staged + unstaged + untracked); contains `..` → that branch diff; anything else → those file paths. Each target maps to explicit instructions in the prompt telling Codex which git command to run to see the changes (`git status` + `git diff HEAD` / `git diff <range>` / read the named files).
3. **Run the review** — exactly one Codex invocation, from the repo root, with a generous timeout (up to 10 minutes):

```bash
codex exec --sandbox read-only "<review prompt>"
```

The review prompt template (fill the TARGET line per step 2):

```
You are performing a one-shot code review. Review target: <TARGET>.

Rules:
1. Correctness bugs first (logic errors, crashes, data loss, security), style last.
2. Every finding must cite a concrete file:line reference.
3. Label every finding with a severity: [BLOCKER], [MAJOR], [MINOR], or [NIT].
4. Review the code that is there; do not propose rewrites of working code.
5. The very last line of your reply must be exactly one of:
VERDICT: NO BLOCKING ISSUES
VERDICT: BLOCKING ISSUES FOUND
Any [BLOCKER] or [MAJOR] finding means blocking. Only [MINOR]/[NIT] findings (or none) means NO BLOCKING ISSUES.
```

4. **Report:** relay Codex's findings faithfully (severity, file:line, description) and the verdict line verbatim. State explicitly that this skill never fixes anything — one shot, done. If the user wants a fix loop, point at codex-review-loop.

- [ ] **Step 2: Build the verification fixture.** In the scratchpad, `git init` a throwaway repo with one committed clean file, then add an uncommitted `stats.js` containing two planted bugs (off-by-one loop bound reading `arr[arr.length]`, and division by `values.length` without an empty-array guard).

- [ ] **Step 3: Run the real review** — execute the SKILL.md steps literally against the fixture repo: the preflight, target resolution (no argument), and the exact `codex exec --sandbox read-only` command. Expected: findings citing `stats.js` with line numbers and severities, final line `VERDICT: BLOCKING ISSUES FOUND`. If Codex's output drifts from the contract (missing verdict line, no severities), tighten the prompt template in SKILL.md and re-run until stable.

- [ ] **Step 4: Verify read-only holds** — `git -C <fixture> status` shows no modifications made by Codex.

- [ ] **Step 5: Commit** — `git add plugins/hbai/skills/codex-review && git commit -m "Add codex-review skill: one-shot read-only Codex review with verdict contract"`

---

### Task 3: `/codex-review-loop` skill + end-to-end verification

**Files:**
- Create: `plugins/hbai/skills/codex-review-loop/SKILL.md`

**Interfaces:**
- Consumes: the codex-review skill via the Skill tool (listed as `codex-review` or `hbai:codex-review` depending on install) and its verdict contract.

- [ ] **Step 1: Write SKILL.md.** Frontmatter:

```yaml
---
name: codex-review-loop
description: Iterative review-and-fix loop composed on top of the codex-review skill. Use when the user invokes /codex-review-loop or asks to review and fix until clean. Each round invokes the codex-review skill via the Skill tool (Codex stays read-only; Claude does the fixing), re-reviews, and stops at VERDICT: NO BLOCKING ISSUES or the round cap (default 3; pass a number to change it, e.g. /codex-review-loop 5).
argument-hint: "[max-rounds]"
---
```

Body must contain:
1. **Composition rule (stated first, as the skill's core discipline):** every review round MUST go through the Skill tool invoking the codex-review skill — find it in the available-skills list as `codex-review` (manual install) or `hbai:codex-review` (plugin install). NEVER run `codex` directly from this skill; if tempted to inline it, that is the anti-pattern this skill exists to teach against.
2. **Round cap:** parse the argument as an integer max-rounds; default 3; reject non-numeric arguments with a usage hint.
3. **The loop**, per round N: (a) invoke codex-review; (b) read the final verdict line; (c) if `VERDICT: NO BLOCKING ISSUES` → stop, success; (d) otherwise Claude fixes every `[BLOCKER]` and `[MAJOR]` finding (may also fix trivial `[MINOR]`s touched in passing); a finding may instead be **deferred** with an explicit one-line reason (false positive, out of scope, needs a product decision) — deferrals are allowed, silent skips are not; (e) record the round (found / fixed / deferred); (f) next round.
4. **Stop conditions:** clean verdict (success) or round cap reached (report remaining findings as unresolved).
5. **Final summary format** — a per-round accounting the user sees at the end:

```
## Review loop summary (N rounds)
Round 1: X findings → fixed: [list] · deferred: [finding — reason]
Round 2: ...
Outcome: clean verdict on round N | round cap reached with M unresolved findings
```

- [ ] **Step 2: End-to-end verification.** Reuse the Task 2 fixture repo (restore the buggy `stats.js` if needed). Execute the loop skill literally: round 1 invokes the codex-review flow → blocking verdict → fix the planted bugs in `stats.js` → round 2 re-invokes → expect `VERDICT: NO BLOCKING ISSUES` and stop. Confirm the loop stopped on the verdict (not the cap) and produce the summary in the specified format.

- [ ] **Step 3: Commit** — `git add plugins/hbai/skills/codex-review-loop && git commit -m "Add codex-review-loop skill: composes codex-review via the Skill tool"`

---

### Task 4: Port `hygiene` → `context-hygiene`

**Files:**
- Create: `plugins/hbai/skills/context-hygiene/SKILL.md` (ported from Cowork `hygiene/SKILL.md`)
- Create: `plugins/hbai/skills/context-hygiene/scripts/check_context.py` (ported)

**Interfaces:**
- Produces: `check_context.py` printing one JSON object `{percentage, tokens_used, context_window, model, error}`; the `find_claude_projects()` pattern reused verbatim in Task 5.

- [ ] **Step 1: Port the script.** Copy Cowork's `check_context.py`, then:

Replace `find_session_jsonl()`'s directory discovery with dual-environment lookup:

```python
def find_claude_projects():
    """Claude Code stores sessions in ~/.claude/projects; Claude Cowork's
    sandbox mounts them at ~/mnt/.claude/projects. Check both."""
    home = os.path.expanduser("~")
    for candidate in (
        os.path.join(home, ".claude", "projects"),
        os.path.join(home, "mnt", ".claude", "projects"),
    ):
        if os.path.isdir(candidate):
            return candidate
    return None
```

`find_session_jsonl()` calls it, keeps the existing "most recently modified `*.jsonl`, excluding `/subagents/`" heuristic, and drops the hardcoded `/sessions/nifty-intelligent-turing` fallback.

Replace the model table:

```python
CONTEXT_WINDOWS = {
    "claude-fable-5": 200_000,
    "claude-opus-5": 200_000,
    "claude-sonnet-5": 200_000,
    "claude-opus-4-6": 200_000,
    "claude-sonnet-4-6": 200_000,
    "claude-haiku-4-5-20251001": 200_000,
    "claude-haiku-4-5": 200_000,
    "default": 200_000,
}
```

Everything else (usage summation of `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`, JSON output shape) stays as-is.

- [ ] **Step 2: Run it live** — `python3 plugins/hbai/skills/context-hygiene/scripts/check_context.py`. Expected: `error: null`, a real model id, `tokens_used` > 0, percentage between 0 and 100, path found under `~/.claude/projects`.

- [ ] **Step 3: Port SKILL.md.** Frontmatter `name: context-hygiene`; description keeps the Cowork triggers but says `/context-hygiene`. Body changes only: (a) script invocation becomes `python3 ${CLAUDE_SKILL_DIR}/scripts/check_context.py` with a note that `${CLAUDE_SKILL_DIR}` is Claude Code's substitution for the skill's own directory; (b) every `/hygiene` mention → `/context-hygiene`; (c) the ≥40% offer says "run `/smart-compact`" (unchanged name). Keep the thresholds table and the slash-vs-natural-language tone section verbatim.

- [ ] **Step 4: Commit** — `git add plugins/hbai/skills/context-hygiene && git commit -m "Port hygiene skill from Claude Cowork as context-hygiene (dual-environment session lookup)"`

---

### Task 5: Port `smart-compact`

**Files:**
- Create: `plugins/hbai/skills/smart-compact/SKILL.md` (ported)
- Create: `plugins/hbai/skills/smart-compact/scripts/extract_session.py` (ported)

**Interfaces:**
- Consumes: the `find_claude_projects()` pattern from Task 4 (copied into this script — scripts stay self-contained per skill so manual installs work).

- [ ] **Step 1: Port the script.** Same two changes as Task 4 (dual-environment `find_claude_projects()`, updated `CONTEXT_WINDOWS`), plus title extraction for both environments — Cowork writes `ai-title` entries, Claude Code writes `summary` entries:

```python
            # Session title — Cowork uses "ai-title", Claude Code uses "summary"
            if etype == "ai-title":
                title = entry.get("aiTitle", title)
            elif etype == "summary":
                title = entry.get("summary", title)
```

Keep the message extraction, truncation budgets, and output shape unchanged. Verify against the live JSONL which entry types actually appear; if Claude Code sessions carry neither, the "Untitled session" fallback stands.

- [ ] **Step 2: Run it live** — `python3 plugins/hbai/skills/smart-compact/scripts/extract_session.py | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['error'], d['title'], d['percentage'], len(d['messages']))"`. Expected: `None`, a non-empty title (or documented fallback), sane percentage, ≥1 message.

- [ ] **Step 3: Port SKILL.md.** Changes from the Cowork original:
  - Description: "...or when **/context-hygiene** recommends compaction" (was /hygiene).
  - Phase 1: `python3 ${CLAUDE_SKILL_DIR}/scripts/extract_session.py`.
  - Phase 4a: save the handoff file to the **current project directory** (same filename pattern `[sanitized-title]-smart-compact-[date].md`).
  - Phase 4b rewritten for Claude Code: give the plain file path (no `computer://` link); instructions — start a fresh `claude` session in the same directory (or `/clear`) and open with "Read <file> and pick up where it leaves off"; DROP the sidebar-rename suggestion entirely.
  - Phase 4c: keep the tombstone block byte-for-byte.
  - Phases 2 and 3 (summary format, review loop) unchanged.

- [ ] **Step 4: Commit** — `git add plugins/hbai/skills/smart-compact && git commit -m "Port smart-compact skill from Claude Cowork (Claude Code delivery phase, dual-environment extractor)"`

---

### Task 6: Codex-side `claude-review` skill + live verification

**Files:**
- Create: `codex/skills/claude-review/SKILL.md`

**Interfaces:**
- Consumes: the verdict contract and severity labels from Global Constraints (identical strings — the contract is tool-agnostic).
- Produces: the claude-review skill name, invoked by claude-review-loop (Task 7).

- [ ] **Step 1: Write SKILL.md** (Agent Skills format, same as Codex's `~/.codex/skills` expects). Frontmatter:

```yaml
---
name: claude-review
description: Run ONE code review of the current work using Claude Code's headless mode and report findings — never fix anything. Use when the user invokes /claude-review or asks Codex for a Claude review / second-opinion review of uncommitted changes, a branch diff (e.g. main..HEAD), or specific files. Claude runs with a read-only tool allowlist; output is severity-labeled findings with file:line references and a final VERDICT line.
---
```

Body mirrors Task 2's structure exactly, with these substitutions:
1. **Preflight:** `command -v claude`; if missing: install with `npm i -g @anthropic-ai/claude-code`, then run `claude` once to log in.
2. **Target resolution:** identical three-way rule (none → uncommitted; `..` → branch diff; else file paths).
3. **Run the review** — one headless Claude invocation from the repo root, read-only enforced by an explicit tool allowlist (the mirror of `--sandbox read-only`):

```bash
claude -p --allowedTools "Read Grep Glob Bash(git diff:*) Bash(git status:*) Bash(git log:*)" "<review prompt>"
```

(Headless mode denies every tool not on the allowlist, so Claude cannot edit files.) The review prompt is the same template as Task 2 verbatim — same rules 1–5, same two VERDICT lines.
4. **Report:** relay findings + verdict verbatim; state that this skill never fixes; point at claude-review-loop for the fix loop.

- [ ] **Step 2: Verify live.** In the Task 2 fixture repo (buggy `stats.js` restored as uncommitted work), run the exact command from the SKILL.md. Expected: findings citing `stats.js` lines with severities, final line `VERDICT: BLOCKING ISSUES FOUND`. If the `--allowedTools` syntax rejects or Claude gets blocked from reading the diff, adjust the allowlist syntax (check `claude -p --help`) until the review completes with read-only tools only, and bake the working syntax into SKILL.md.

- [ ] **Step 3: Verify read-only holds** — `git -C <fixture> status` unchanged by the review run.

- [ ] **Step 4: Commit** — `git add codex && git commit -m "Add Codex-side claude-review skill: headless read-only Claude review, same verdict contract"`

---

### Task 7: Codex-side `claude-review-loop` skill + verification

**Files:**
- Create: `codex/skills/claude-review-loop/SKILL.md`

**Interfaces:**
- Consumes: the claude-review skill (Task 6) by name; the verdict contract.

- [ ] **Step 1: Write SKILL.md.** Frontmatter:

```yaml
---
name: claude-review-loop
description: Iterative review-and-fix loop composed on top of the claude-review skill. Use when the user invokes /claude-review-loop or asks Codex to have Claude review and then fix until clean. Each round invokes the claude-review skill (Claude stays read-only; Codex does the fixing), re-reviews, and stops at VERDICT: NO BLOCKING ISSUES or the round cap (default 3; pass a number to change it).
---
```

Body mirrors Task 3, adapted to Codex's composition idiom:
1. **Composition rule:** every round MUST use the claude-review skill — invoke it by name; do NOT re-implement or inline the `claude -p` invocation in this skill (same wording discipline Ben's aria skills use: "do not re-implement these checks inline").
2. Round cap parsing identical to Task 3 (default 3).
3. Loop, stop conditions, deferral rules, and final summary format identical to Task 3, with fixer = Codex and reviewer = Claude.

- [ ] **Step 2: Verify.** Preferred: full end-to-end — restore the buggy fixture, copy both mirror skills into `~/.codex/skills/`, then run `codex exec --sandbox danger-full-access --cd <fixture> "Use the claude-review-loop skill on the uncommitted changes"` (full access is required because Codex must both edit files and shell out to `claude`, which needs network; the run is confined to the throwaway fixture). Expected: ≥2 rounds, fixes applied by Codex, stops on clean verdict, summary printed. Fallback if that run is flaky: verify the rounds step-by-step manually (run claude-review, apply fixes as Codex would, re-run to clean verdict) and record in the README's build notes that the Codex-side loop was verified semi-manually. Remove the copied skills from `~/.codex/skills/` afterward.

- [ ] **Step 3: Commit** — `git add codex && git commit -m "Add Codex-side claude-review-loop skill: composes claude-review, Codex fixes"`

---

### Task 8: README

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: exact install commands (Task 1 manifests), verdict contract (Task 2), both chain designs (Tasks 2–5).

- [ ] **Step 1: Write README.md** with these sections, in order:
  1. **Title + intro** — free skill pack for Claude Code from Ben at Human Balance AI; the `hbai` plugin is the HBAI toolkit and this pack is what's in it today; the real product is the lesson: how to chain skills.
  2. **Install** — both paths: (a) `/plugin marketplace add MrBenJ/hbai-skill-pack` then `/plugin install hbai@hbai-skill-pack` (skills become `/hbai:<name>`); (b) manual: copy any folder from `plugins/hbai/skills/` into `~/.claude/skills/` (skills become bare `/<name>`). Note that examples in the README use bare names.
  3. **The four skills** — one subsection each: what it does, usage line, and a short stylized example transcript (codex-review showing severity findings + verdict line; codex-review-loop showing a 2-round loop + summary; context-hygiene showing the stats + health rating; smart-compact showing the handoff flow + tombstone).
  4. **The chaining pattern** — the teaching core. Both chains: `/codex-review` → `/codex-review-loop` (a skill invoking a skill in a loop via the Skill tool) and `/context-hygiene` → `/smart-compact` (a skill whose output triggers another). Why the atomic skill stays single-purpose (independently testable, reusable, one contract to stabilize) and why the composite reuses instead of duplicating (one source of truth for the review prompt/verdict; fix logic and review logic evolve independently). Call out the verdict line as the machine-readable interface between the two skills.
  5. **The mirror pack** — the same review chain with roles swapped: Codex drives, Claude reviews read-only. Install: `cp -R codex/skills/* ~/.codex/skills/`, invoked from Codex as `claude-review` / `claude-review-loop`. Teaching point: the verdict contract is tool-agnostic — the identical exact strings coordinate the chain no matter which agent reviews and which fixes; also note the composition-mechanism difference (Claude Code has a Skill tool; Codex composes by skill-name reference).
  6. **How this was built** — design decisions (read-only sandbox so the reviewer can never touch the code; exact-string verdict as an API between skills; round cap as a safety valve); the Cowork→Claude Code port (session path `~/mnt/.claude/projects` → `~/.claude/projects` with fallback kept for dual-environment support; `$SKILL_DIR` env var → `${CLAUDE_SKILL_DIR}` substitution; delivery phase rewritten from Cowork's Downloads/sidebar world to Claude Code's project-directory world; `ai-title` vs `summary` JSONL entries); note the specs/plans under `docs/superpowers/` as the actual working artifacts.
  7. **License** — MIT; footer: from Ben at Human Balance AI with site link.

- [ ] **Step 2: Commit** — `git add README.md && git commit -m "Add teaching README: install paths, skill docs, chaining pattern, build notes"`

---

### Task 9: Fresh-eyes pass on all six SKILL.md files

**Files:**
- Modify (as needed): all four `plugins/hbai/skills/*/SKILL.md` and both `codex/skills/*/SKILL.md`

- [ ] **Step 1: Re-read superpowers:writing-skills** and apply its fresh-eyes checklist to each SKILL.md: description states when-to-use from the user's words; no instruction depends on context only this session has; steps executable by a cold reader; consistent naming; no dead references (especially `/hygiene` remnants or `$SKILL_DIR`).

- [ ] **Step 2: Grep for known drift** — `grep -rn 'SKILL_DIR\|/hygiene\|mnt/.claude' plugins/ codex/ README.md` and confirm every hit is intentional (`${CLAUDE_SKILL_DIR}` and documented Cowork fallbacks only), and `grep -rn 'VERDICT:' plugins/ codex/ README.md` to confirm the exact strings match everywhere.

- [ ] **Step 3: Fix + commit** — `git add -A && git commit -m "Fresh-eyes pass on skill docs"` (skip commit if no changes).

---

### Task 10: Present README to Ben (gate), then publish

- [ ] **Step 1: STOP and show Ben the final README** (and repo tree). No remote exists yet. Wait for approval.

- [ ] **Step 2 (post-approval): Create the public repo and push** — `gh repo create MrBenJ/hbai-skill-pack --public --source . --push --description "Free Claude Code skill pack from Human Balance AI — four skills, two chains, and the lesson of how to compose them."`

- [ ] **Step 3: Smoke-test the published install path** — `/plugin marketplace add MrBenJ/hbai-skill-pack` from a shell-driven check or report the exact commands for Ben to run.
