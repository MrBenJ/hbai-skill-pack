# HBAI Skill Pack — Repository Instructions

`CLAUDE.md` and `AGENTS.md` are mirrors. Keep them byte-for-byte identical so
Claude Code, Codex, and other coding harnesses receive the same repository
guidance.

## Purpose

This repository publishes real plugins and skills that Ben uses in everyday
software-engineering work. The goals are to:

- share practical agent workflows that are useful outside this repository;
- keep pace with coding-agent capabilities and turn what works into reusable
  tools;
- make those tools available to people using different subscriptions and coding
  harnesses; and
- build awareness and trust for Human Balance AI through the quality of the work.

This is not a dumping ground for demos or speculative prompt snippets. Prefer a
small set of maintained skills with genuine day-to-day value.

HBAI promotion should be understated. Lead with usefulness, evidence, and clear
documentation. A light company mention or call to action is appropriate; salesy
copy, inflated claims, and marketing that obscures the tool are not.

## Compatibility

Design for coding-harness portability. Claude Code and OpenAI Codex are the two
first-class targets, but avoid unnecessary assumptions that prevent a skill from
working elsewhere.

- Treat the common Agent Skills shape (`<skill-name>/SKILL.md` with YAML
  frontmatter) as the default for portable skills.
- Keep core workflow instructions vendor-neutral when the task is vendor-neutral.
- Use harness-specific tools, variables, or invocation syntax only when the
  capability genuinely requires them, and make that boundary obvious.
- For a harness-neutral skill, expose it to both Claude Code and Codex when
  practical. If separate copies are required, keep their behavior and public
  contract aligned.
- Do not assume that installing the Claude plugin also installs anything from
  `codex/skills/`, or vice versa.

Agent names are technical facts when a workflow intentionally composes multiple
products, as the review skills do. Do not introduce a product identity into
otherwise portable prompts or user-facing output.

## Repository layout

- `.claude-plugin/marketplace.json` — Claude Code marketplace entry.
- `plugins/hbai/.claude-plugin/plugin.json` — HBAI plugin manifest and version.
- `plugins/hbai/skills/` — skills distributed through the Claude Code plugin and
  available for manual Claude Code installation.
- `codex/skills/` — skills distributed for manual Codex installation.
- `README.md` — public installation, usage, examples, positioning, and build notes.
- `docs/superpowers/` — historical design and implementation artifacts; do not
  rewrite them merely to make old plans describe newer repository state.

This repository has no root package manager or generic test suite. Validate the
artifact being changed with its own tooling.

## Skill design

- Skill folder names and frontmatter `name` values use lowercase letters, digits,
  and hyphens, and must match each other.
- Descriptions say what the skill does and when it should activate. They should be
  precise enough to avoid unrelated automatic invocation.
- Keep `SKILL.md` focused on decisions and workflow knowledge another capable agent
  would not reliably infer. Avoid generic advice and unnecessary scaffolding.
- Add scripts, references, or assets only when they materially improve reliability
  or reuse. Keep an ordinary skill self-contained.
- Remember that users may manually copy one skill directory. Cross-skill
  dependencies must be intentional, documented, and fail clearly when unavailable.
- Preserve user scope and authorization. A skill may inspect relevant state, but it
  must not imply permission to commit, push, deploy, message people, discard work,
  or perform other external mutations.
- Never include secrets, credentials, private session data, or machine-specific
  personal information in examples or generated artifacts.

## Skill chaining

Prefer composition over duplicated workflow logic:

- Keep atomic skills independently useful and testable.
- Give outputs consumed by other skills a small, explicit, stable contract.
- A composing skill should invoke or reference the atomic skill by its installed
  name instead of reimplementing its internals.
- Account for both naming forms where relevant: bare names after manual install and
  `hbai:<skill-name>` inside the Claude plugin.
- Define honest stopping behavior when a chain can loop, block, or partially
  succeed.

## Documentation and brand voice

Write in a direct, practical, human voice. Explain the outcome first, then the
mechanics that help someone use or trust it. Prefer concrete examples over hype.

When adding or materially changing a public skill:

1. Update `README.md` with its purpose, invocation, and a concise example.
2. Update affected marketplace or plugin descriptions when the capability list has
   changed.
3. Bump the plugin version when the distributed Claude plugin changes.
4. Keep install instructions accurate for both Claude Code and Codex.
5. Do not claim a workflow was verified live unless it actually was.

## Validation

Before reporting a skill change complete:

- validate the changed `SKILL.md` with an available Agent Skills validator;
- run `claude plugin validate .` when the Claude marketplace or plugin changes;
- parse modified JSON manifests with `python3 -m json.tool`;
- run `git diff --check` and inspect the full diff, including new files;
- run any bundled scripts or behavior checks affected by the change; and
- confirm `CLAUDE.md` and `AGENTS.md` still match exactly.

Do not push, publish, create a release, or mutate installed global skills unless the
user explicitly asks.
