#!/usr/bin/env python3
"""
extract_session.py — reads the current session's JSONL and outputs
a structured JSON object for the /smart-compact skill to summarize.

Works in both environments:
  - Claude Code:   sessions live in ~/.claude/projects
  - Claude Cowork: the sandbox mounts them at ~/mnt/.claude/projects

Extracts:
  - title: AI-generated session title
  - date: session start date (ISO)
  - messages: condensed user/assistant conversation (text only, no tool noise)
  - total_tokens: last known input token count
  - context_window: model context window size
  - model: model name
"""

import json
import os
import glob
import re
import sys
from datetime import datetime, timezone

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

# Max chars per message before truncation (keeps summary context lean)
MSG_CHAR_LIMIT = 800
# Max total chars of conversation to pass for summarisation
TOTAL_CHAR_LIMIT = 40_000


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


def encode_project_dir(path):
    """Claude Code names each project folder after its working directory,
    with every non-alphanumeric character replaced by '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def find_session_jsonl():
    """Find the most recently modified session JSONL (excluding subagent files).
    The live session is written on every turn, so newest-by-mtime is the
    current conversation. Prefer the current project's folder so a concurrent
    session in another project can't win; fall back to all projects (Cowork's
    layout has no per-project match for the sandbox cwd)."""
    claude_projects = find_claude_projects()
    if claude_projects is None:
        return None

    project_dir = os.path.join(claude_projects, encode_project_dir(os.getcwd()))
    for root in (project_dir, claude_projects):
        candidates = []
        for path in glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True):
            if "/subagents/" not in path:
                candidates.append((os.path.getmtime(path), path))
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]

    return None


def extract_text_content(content):
    """Pull plain text from a message content field (str or list of blocks)."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", "").strip())
                # Skip tool_use, tool_result, images — noise for summarisation
        return "\n".join(p for p in parts if p)
    return ""


def main():
    jsonl_path = find_session_jsonl()
    if not jsonl_path:
        print(json.dumps({"error": "Could not locate session JSONL.", "messages": []}))
        sys.exit(0)

    title = "Untitled session"
    start_ts = None
    last_usage = None
    last_model = None
    messages = []

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            etype = entry.get("type")

            # Session title — current Claude Code and Cowork write "ai-title";
            # older Claude Code versions wrote "summary" entries instead
            if etype == "ai-title":
                title = entry.get("aiTitle", title)
            elif etype == "summary":
                title = entry.get("summary", title)

            # User messages
            elif etype == "user":
                ts = entry.get("timestamp")
                if ts and start_ts is None:
                    start_ts = ts
                msg_content = entry.get("message", {})
                if isinstance(msg_content, dict):
                    raw = extract_text_content(msg_content.get("content", ""))
                else:
                    raw = extract_text_content(msg_content)
                if raw:
                    truncated = raw[:MSG_CHAR_LIMIT] + ("…" if len(raw) > MSG_CHAR_LIMIT else "")
                    messages.append({"role": "user", "content": truncated})

            # Assistant messages
            elif etype == "assistant":
                msg = entry.get("message", {})
                if isinstance(msg, dict):
                    raw = extract_text_content(msg.get("content", ""))
                    usage = msg.get("usage")
                    model = msg.get("model")
                    if usage:
                        last_usage = usage
                    if model:
                        last_model = model
                    if raw:
                        truncated = raw[:MSG_CHAR_LIMIT] + ("…" if len(raw) > MSG_CHAR_LIMIT else "")
                        messages.append({"role": "assistant", "content": truncated})

    # Trim total conversation size if it's huge
    total_chars = sum(len(m["content"]) for m in messages)
    if total_chars > TOTAL_CHAR_LIMIT:
        # Keep first few messages (establish context) + last bulk (recent work)
        kept = []
        budget = TOTAL_CHAR_LIMIT
        # First 5 messages for opening context
        for m in messages[:5]:
            kept.append(m)
            budget -= len(m["content"])
        kept.append({"role": "system", "content": "[ ... earlier conversation omitted for brevity ... ]"})
        # Fill remaining budget from most recent messages
        recent = []
        for m in reversed(messages[5:]):
            if budget <= 0:
                break
            recent.append(m)
            budget -= len(m["content"])
        kept.extend(reversed(recent))
        messages = kept

    # Token stats
    total_input = 0
    if last_usage:
        total_input = (
            last_usage.get("input_tokens", 0)
            + last_usage.get("cache_read_input_tokens", 0)
            + last_usage.get("cache_creation_input_tokens", 0)
        )
    context_window = CONTEXT_WINDOWS.get(last_model or "", CONTEXT_WINDOWS["default"])
    pct = round(total_input / context_window * 100, 1) if context_window else 0

    # Date
    date_str = "unknown date"
    if start_ts:
        try:
            dt = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            date_str = start_ts[:10]

    print(json.dumps({
        "error": None,
        "title": title,
        "date": date_str,
        "model": last_model or "unknown",
        "total_tokens": total_input,
        "context_window": context_window,
        "percentage": pct,
        "messages": messages,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
