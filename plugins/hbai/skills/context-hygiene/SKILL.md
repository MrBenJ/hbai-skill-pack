---
name: context-hygiene
description: Use when the user invokes /context-hygiene, asks about context usage, wonders if the conversation is getting too long, asks whether they should compact or start fresh, or asks how much memory Claude has left. Reports context window usage with a plain-language health rating and recommends compaction when context is crowded.
---

# /context-hygiene — Context Health Check

When this skill is invoked, check how much of the current context window has
been consumed and report it clearly.

## Step 1: Measure context usage

Run the bundled script (`${CLAUDE_SKILL_DIR}` is Claude Code's substitution
for this skill's own directory, so this works for both plugin and manual
installs):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_context.py
```

The script outputs a single JSON object:

```json
{
  "percentage": 27.7,
  "tokens_used": 55351,
  "context_window": 200000,
  "model": "claude-sonnet-5",
  "error": null
}
```

If `error` is non-null, report it plainly and stop.

## Step 2: Report the result

Always show all three of these:
- The percentage (e.g. **27.7%**)
- The raw token count (e.g. `55,351 / 200,000 tokens`)
- A one-line status based on the thresholds below

### Health thresholds

| Range    | Label    | Status line |
|----------|----------|-------------|
| 0–39%    | ✅ Healthy   | Good to go. Chat away. |
| 40–50%   | ⚠️ Caution   | Approaching unreliable levels of context size. Consider compaction. |
| 51–70%   | 🔶 Warning   | Context is too large to be considered reliable. Claude may not remember some things in this conversation due to the size. Recommend compaction. |
| 71–100%  | 🚨 Critical  | Context is extremely large and can have severe memory issues or hallucinations. Urgently recommend compaction. |

### Tone: slash command vs. natural language

How the user invoked this skill changes the tone of the response:

- **Explicit `/context-hygiene`** — lead directly with the stats. Clean, no
  preamble.
- **Natural language** (e.g. "how full is my context?", "should I compact?")
  — add a brief human opener first that mentions the percentage and that you
  ran `/context-hygiene`, then show the stats. This lets the user know what
  you did to get the answer.

**Natural language example:**
> You're looking good at 32.7% — I ran `/context-hygiene` to check.
> **32.7%** · `65,471 / 200,000 tokens`
> ✅ Healthy — Good to go. Chat away.

Keep it short either way — no need to explain what context windows are unless
the user asks.

## Step 3: Offer compaction (only if ≥ 40%)

If the percentage is 40% or higher, add a prompt at the end offering to
compact:

> Would you like me to run `/smart-compact` to compress this conversation and
> free up context?

Do not offer this below 40% — there's nothing to worry about at that level.
