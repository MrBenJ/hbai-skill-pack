---
name: codex-review
description: Use when the user invokes /codex-review or asks for a Codex review, a second-opinion code review, or an outside review of uncommitted changes, a branch diff (e.g. main..HEAD), or specific files. Runs OpenAI's Codex CLI in a read-only sandbox as the reviewer. Reports findings only — never fixes anything.
argument-hint: "[main..HEAD | file paths]"
---

# /codex-review — One-Shot Codex Code Review

Run exactly ONE code review using OpenAI's Codex CLI as an outside reviewer,
then report its findings. Codex runs in a read-only sandbox, so it can never
touch the code. This skill reviews and reports — it does not fix. One shot,
done.

## Step 1: Preflight

```bash
command -v codex
codex login status
```

If `codex` is not found, or `codex login status` does not report a logged-in
state, STOP. Tell the user:

> Codex CLI isn't installed. Install it with `npm i -g @openai/codex`, then
> authenticate with `codex login`, and re-run `/codex-review`.

Do not attempt the review any other way.

## Step 2: Resolve the review target

From the skill argument:

| Argument | Target | TARGET line for the prompt |
|---|---|---|
| none + dirty tree | Uncommitted work | `the uncommitted changes in this repository (staged, unstaged, and untracked files); run 'git status' and 'git diff HEAD' to see them, and read untracked files directly` |
| none + clean tree | The current feature branch's commits ahead of the default branch, or stop if there are none | `the diff <default>..HEAD in this repository; run 'git diff <default>..HEAD' to see it, and also review any uncommitted changes on top of HEAD; run 'git status' and 'git diff HEAD', and read untracked files directly` |
| contains `..` (e.g. `main..HEAD`) | Branch diff plus any dirty work on top of `HEAD` | `the diff <range> in this repository; run 'git diff <range>' to see it, and also review any uncommitted changes on top of HEAD; run 'git status' and 'git diff HEAD', and read untracked files directly` |
| anything else | Specific files | `these files: <paths>; read each one directly` |

When no argument was given, run `git status --porcelain` before selecting a
target. If it is non-empty, use the uncommitted-work target. If it is empty:

1. Resolve the default branch with
   `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, stripping the
   leading `origin/`. If that fails, use the existing local `main` branch,
   then the existing local `master` branch.
2. Read the current branch with `git branch --show-current`.
3. If the current branch differs from the default branch, run
   `git rev-list --count <default>..HEAD`. When the count is greater than
   zero, review `<default>..HEAD` and tell the user in one line that the tree
   was clean, so the review widened to that range.
4. Otherwise STOP. Tell the user there is nothing to review and show these
   three argument forms: `/codex-review`, `/codex-review main..HEAD`, and
   `/codex-review <file paths>`.

Do not invoke Codex until this resolution produces a non-empty target.

## Step 3: Run the review

One Codex invocation, from the repository root, passing the prompt on stdin
(the `-` argument) to avoid shell-quoting problems. Codex reviews can take a
few minutes — use a generous timeout (up to 10 minutes).

```bash
REVIEW_OUT="$(mktemp "${TMPDIR:-/tmp}/codex-review.XXXXXX")"
REVIEW_ERR="$(mktemp "${TMPDIR:-/tmp}/codex-review-stderr.XXXXXX")"

codex exec --sandbox read-only -o "$REVIEW_OUT" - <<'EOF' > /dev/null 2>"$REVIEW_ERR"
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
EOF
```

Replace `<TARGET>` with the TARGET line from Step 2. `--sandbox read-only` is
non-negotiable — it is what guarantees the reviewer cannot edit files.

Read **only** `$REVIEW_OUT` after the command finishes. It contains exactly
the final Codex reply once, without the session transcript or CLI footer. Do
not relay, inspect, or load the discarded stdout.

## Step 4: Report

Relay to the user:

1. Every finding exactly once, faithfully, and in the order Codex gave it.
   Format each one as severity label first, then `file:line`, then the
   description. Do not soften, reorder, merge, duplicate, or drop findings.
2. The verdict line — the last `VERDICT:` line in `$REVIEW_OUT` — verbatim,
   on its own line.

If Codex reports it ran the project's tests/build itself, relay that too —
it's evidence, not noise.

Then stop. This skill NEVER fixes, stages, commits, or edits anything — not
even a one-character fix that seems obvious. If the user wants findings fixed
and re-reviewed automatically, point them at `/codex-review-loop`, which
composes this skill.

If `$REVIEW_OUT` is missing or empty after the run, say so explicitly and
show the tail of `$REVIEW_ERR` so the failure is diagnosable. If the file is
not empty but has no verdict line, say so explicitly and quote the raw tail
of `$REVIEW_OUT`. Never invent a verdict. Remove both temporary files after
reporting.
