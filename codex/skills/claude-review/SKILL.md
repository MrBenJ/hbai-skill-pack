---
name: claude-review
description: Use when the user invokes /claude-review or asks Codex for a Claude review, a second-opinion code review, or an outside review of uncommitted changes, a branch diff (e.g. main..HEAD), or specific files. Runs Claude Code headless outside the Codex sandbox, with a read-only tool allowlist as the reviewer. Reports findings only — never fixes anything.
---

# /claude-review — One-Shot Claude Code Review (for Codex)

Run exactly ONE code review using Claude Code's headless mode as an outside
reviewer, then report its findings. Claude runs with a read-only tool
allowlist, so it can never touch the code. This skill reviews and reports —
it does not fix. One shot, done.

This is the mirror of the Claude Code–side `codex-review` skill: same review
contract, roles swapped.

## Step 1: Preflight

```bash
command -v claude
```

If `claude` is not found, STOP. Tell the user:

> Claude Code isn't installed. Install it with
> `npm i -g @anthropic-ai/claude-code`, run `claude` once to log in, then
> re-run /claude-review.

Do not attempt the review any other way.

## Step 2: Resolve the review target

From the argument:

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
   three argument forms: `/claude-review`, `/claude-review main..HEAD`, and
   `/claude-review <file paths>`.

Do not invoke Claude until this resolution produces a non-empty target.

## Step 3: Run the review

One headless Claude invocation, from the repository root, passing the prompt
on stdin (the `-` argument). The `--allowedTools` allowlist is the read-only
guarantee — headless mode denies every tool not on it, so Claude cannot edit
files. It is non-negotiable. Reviews can take a few minutes — allow up to 10.

**Run this invocation outside the Codex sandbox on the first attempt.** Use the
host's escalated or outside-sandbox execution option (for example,
`sandbox_permissions: require_escalated` when available) and request approval if
the host requires it. A sandboxed Codex process may hide Claude's existing login
and network access, producing a false `Not logged in` result even when Claude is
authenticated on the host. Do not use a failed sandboxed invocation as an
authentication check and do not make the user log in again before retrying outside
the sandbox.

Outside-sandbox execution only lets the Claude CLI reach its existing credentials
and service. It does not make the review writable: the `--allowedTools` allowlist
below remains the required write barrier. If outside-sandbox execution is denied,
stop and explain that the review cannot run; do not fall back to a sandboxed review
or a different reviewer.

```bash
claude -p --allowedTools "Read Grep Glob Bash(git diff:*) Bash(git status:*) Bash(git log:*)" - <<'EOF'
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

Replace `<TARGET>` with the TARGET line from Step 2. The verdict is the last
`VERDICT:` line in the output.

## Step 4: Report

Relay to the user:

1. Every finding exactly once, faithfully, and in the order Claude gave it.
   Format each one as severity label first, then `file:line`, then the
   description. Do not soften, reorder, merge, duplicate, or drop findings.
2. The verdict line, verbatim, on its own line.

If Claude reports it ran the project's tests/build itself, relay that too —
it's evidence, not noise.

Then stop. This skill NEVER fixes, stages, commits, or edits anything — not
even a one-character fix that seems obvious. If the user wants findings fixed
and re-reviewed automatically, point them at the `claude-review-loop` skill,
which composes this one.

If the output is missing the verdict line, say so explicitly and quote the
raw tail of the output instead of inventing a verdict.
