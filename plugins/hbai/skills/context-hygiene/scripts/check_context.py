#!/usr/bin/env python3
"""
check_context.py — reads the current session's JSONL to calculate context window usage.
Outputs a single JSON object for the /context-hygiene skill to interpret.

Works in both environments:
  - Claude Code:   sessions live in ~/.claude/projects
  - Claude Cowork: the sandbox mounts them at ~/mnt/.claude/projects
"""

import json
import os
import glob
import re
import sys

# Context window sizes by model (tokens)
CONTEXT_WINDOWS = {
    "claude-fable-5": 200_000,
    "claude-opus-5": 200_000,
    "claude-sonnet-5": 200_000,
    "claude-opus-4-6": 200_000,
    "claude-sonnet-4-6": 200_000,
    "claude-haiku-4-5-20251001": 200_000,
    "claude-haiku-4-5": 200_000,
    # Fallback for any unknown model
    "default": 200_000,
}


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


def get_last_usage(jsonl_path):
    """Return the usage dict from the last assistant message that has one."""
    last_usage = None
    last_model = None

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if entry.get("type") == "assistant" and "message" in entry:
                msg = entry["message"]
                usage = msg.get("usage")
                model = msg.get("model")
                if usage:
                    last_usage = usage
                if model:
                    last_model = model

    return last_usage, last_model


def main():
    jsonl_path = find_session_jsonl()

    if not jsonl_path:
        print(json.dumps({
            "error": "Could not locate session data. No JSONL file found.",
            "percentage": None,
        }))
        sys.exit(0)

    last_usage, model = get_last_usage(jsonl_path)

    if not last_usage:
        print(json.dumps({
            "error": "No token usage data found in session.",
            "percentage": None,
        }))
        sys.exit(0)

    input_tokens = last_usage.get("input_tokens", 0)
    cache_read = last_usage.get("cache_read_input_tokens", 0)
    cache_create = last_usage.get("cache_creation_input_tokens", 0)
    total_input = input_tokens + cache_read + cache_create

    context_window = CONTEXT_WINDOWS.get(model or "", CONTEXT_WINDOWS["default"])
    percentage = (total_input / context_window) * 100

    print(json.dumps({
        "percentage": round(percentage, 1),
        "tokens_used": total_input,
        "context_window": context_window,
        "model": model or "unknown",
        "error": None,
    }))


if __name__ == "__main__":
    main()
