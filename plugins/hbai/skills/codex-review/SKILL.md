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
```

If `codex` is not found, STOP. Tell the user:

> Codex CLI isn't installed. Install it with `npm i -g @openai/codex`, then
> authenticate with `codex login`, and re-run `/codex-review`.

Do not attempt the review any other way.

## Step 2: Resolve the review target

From the skill argument:

| Argument | Target | TARGET line for the prompt |
|---|---|---|
| none | Uncommitted work | `the uncommitted changes in this repository (staged, unstaged, and untracked files); run 'git status' and 'git diff HEAD' to see them, and read untracked files directly` |
| contains `..` (e.g. `main..HEAD`) | Branch diff | `the diff <range> in this repository; run 'git diff <range>' to see it` |
| anything else | Specific files | `these files: <paths>; read each one directly` |

## Step 3: Run the review

One Codex invocation, from the repository root, passing the prompt on stdin
(the `-` argument) to avoid shell-quoting problems. Codex reviews can take a
few minutes — use a generous timeout (up to 10 minutes).

```bash
codex exec --sandbox read-only - <<'EOF'
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

Note: the Codex CLI prints a `tokens used` footer after the reply, so the
verdict is the **last `VERDICT:` line in the output**, not necessarily the
last line of stdout.

## Step 4: Report

Relay to the user:

1. Every finding, faithfully: severity label, `file:line`, description. Do not
   soften, merge, or drop findings.
2. The verdict line, verbatim, on its own line.

Then stop. This skill NEVER fixes, stages, commits, or edits anything — not
even a one-character fix that seems obvious. If the user wants findings fixed
and re-reviewed automatically, point them at `/codex-review-loop`, which
composes this skill.

If the Codex output is missing the verdict line, say so explicitly and quote
the raw tail of the output instead of inventing a verdict.
