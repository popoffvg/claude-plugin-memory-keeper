#!/usr/bin/env python3
"""
Stop hook: Reads the session transcript, sends the last N messages
to Haiku to detect insights, tasks, or agent behavior corrections,
then writes them directly to ~/ctx/insights/ without blocking Claude.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime

LOG_DIR = os.path.expanduser("~/.claude/debug")
os.makedirs(LOG_DIR, exist_ok=True)


def load_config() -> dict:
    """Parse YAML frontmatter from ~/.claude/memory-keeper.local.md (no PyYAML)."""
    config_path = os.path.expanduser("~/.claude/memory-keeper.local.md")
    config = {}
    if not os.path.isfile(config_path):
        return config
    try:
        with open(config_path, "r") as f:
            lines = f.readlines()
    except Exception:
        return config
    in_frontmatter = False
    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            if in_frontmatter:
                break
            in_frontmatter = True
            continue
        if in_frontmatter and ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if key and value:
                config[key] = value
    return config


_config = load_config()
if "insights_root" not in _config:
    # No settings file or missing insights_root — skip silently
    # User must create ~/.claude/memory-keeper.local.md with insights_root setting
    pass
INSIGHTS_ROOT = os.path.expanduser(_config.get("insights_root", ""))

from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "stop-hook.log"),
    maxBytes=512_000,  # 500KB
    backupCount=3,
)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
log = logging.getLogger(__name__)
log.setLevel(getattr(logging, _config.get("log_level", "DEBUG").upper(), logging.DEBUG))
log.addHandler(handler)

MAX_TAIL_MESSAGES = 10
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def read_transcript(path: str) -> list[dict]:
    """Read JSONL transcript and return message list."""
    messages = []
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    messages.append(json.loads(line))
    except Exception as e:
        log.error("Failed to read transcript %s: %s", path, e)
        return []
    log.debug("Read %d messages from transcript", len(messages))
    return messages


def extract_recent_text(messages: list[dict], max_messages: int) -> str:
    """Extract recent human/assistant text from transcript."""
    texts = []
    count = 0
    for msg in reversed(messages):
        if count >= max_messages:
            break
        msg_type = msg.get("type", "")
        if msg_type not in ("user", "assistant"):
            continue

        inner = msg.get("message", {})
        if not isinstance(inner, dict):
            continue
        role = inner.get("role", msg_type)
        content = inner.get("content", "")

        # Skip tool-result-only user messages (no human text)
        if msg_type == "user" and msg.get("toolUseResult"):
            continue

        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block["text"])
            content = "\n".join(parts)
        if isinstance(content, str) and content.strip():
            texts.append(f"[{role}]: {content[:2000]}")
            count += 1

    texts.reverse()
    return "\n\n".join(texts)


def _load_prompt(filename: str) -> str:
    with open(os.path.join(PROMPTS_DIR, filename)) as f:
        return f.read()


def ask_haiku(conversation_text: str) -> dict | None:
    """Classify the conversation into insight/task/agent_edit/none."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set in environment")
        return None

    try:
        user_template = _load_prompt("check-insights-user.txt")
    except Exception as e:
        log.error("Failed to load prompt template: %s", e)
        return None

    prompt = user_template.replace("{conversation_text}", conversation_text)

    try:
        result = subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                "https://api.anthropic.com/v1/messages",
                "-H", f"x-api-key: {api_key}",
                "-H", "anthropic-version: 2023-06-01",
                "-H", "content-type: application/json",
                "-d", json.dumps({
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                })
            ],
            capture_output=True, text=True, timeout=15
        )
        log.debug("curl returncode=%d", result.returncode)
        if result.returncode != 0:
            log.error("curl failed: stderr=%s", result.stderr)
            return None

        if not result.stdout.strip():
            log.error("curl returned empty body")
            return None

        log.debug("API response: %s", result.stdout[:500])
        response = json.loads(result.stdout)

        if "error" in response:
            log.error("API error: %s", response["error"])
            return None

        text = response.get("content", [{}])[0].get("text", "").strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:])
        if text.endswith("```"):
            text = "\n".join(text.split("\n")[:-1])
        text = text.strip()

        data = json.loads(text)
        log.info("Haiku classification: %s", data)
        return data
    except Exception as e:
        log.error("Classification failed: %s", e, exc_info=True)
        return None


def save_insight(insight: str, topic: str, project: str, cwd: str,
                 rationale: str = "", workflow: str = "") -> str:
    """Append insight to ~/ctx/insights/<project>/insights.md. Returns file path."""
    insights_dir = os.path.join(INSIGHTS_ROOT, project)
    os.makedirs(insights_dir, exist_ok=True)
    path = os.path.join(insights_dir, "insights.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## {topic} — {timestamp}\n- **type**: insight\n{insight}\n"
    if rationale:
        entry += f"- **Why**: {rationale}\n"
    if workflow:
        entry += f"- **Workflow**: {workflow}\n"
    entry += f"_(cwd: {cwd})_\n"
    with open(path, "a") as f:
        f.write(entry)
    log.info("Insight saved to %s", path)
    return path


def save_task(title: str, description: str, project: str, cwd: str,
              rationale: str = "", workflow: str = "") -> str:
    """Append task to ~/ctx/insights/_tasks/pending.md. Returns file path."""
    tasks_dir = os.path.join(INSIGHTS_ROOT, "_tasks")
    os.makedirs(tasks_dir, exist_ok=True)
    path = os.path.join(tasks_dir, "pending.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = (
        f"\n## {title}\n"
        f"- **Description**: {description}\n"
        f"- **Project**: {project}\n"
    )
    if rationale:
        entry += f"- **Why**: {rationale}\n"
    if workflow:
        entry += f"- **Workflow**: {workflow}\n"
    entry += f"- **CWD**: {cwd}\n- **Captured**: {timestamp}\n"
    with open(path, "a") as f:
        f.write(entry)
    log.info("Task saved to %s", path)
    return path


def save_agent_edit(insight: str, topic: str, cwd: str,
                    improvement: str = "", rationale: str = "", workflow: str = "") -> str:
    """Append agent behavior correction to ~/ctx/insights/claude-config/behavior.md."""
    config_dir = os.path.join(INSIGHTS_ROOT, "claude-config")
    os.makedirs(config_dir, exist_ok=True)
    path = os.path.join(config_dir, "behavior.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## {topic} — {timestamp}\n{insight}\n"
    if improvement:
        entry += f"- **Improvement**: {improvement}\n"
    if rationale:
        entry += f"- **Why**: {rationale}\n"
    if workflow:
        entry += f"- **Workflow**: {workflow}\n"
    entry += f"_(cwd: {cwd})_\n"
    with open(path, "a") as f:
        f.write(entry)
    log.info("Agent edit saved to %s", path)
    return path


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        log.error("Failed to parse stdin: %s", e)
        sys.exit(0)

    log.info("Stop hook triggered. Input keys: %s", list(input_data.keys()))

    if input_data.get("stop_hook_active"):
        log.info("stop_hook_active set, skipping")
        sys.exit(0)

    transcript_path = input_data.get("transcript_path", "")
    if not transcript_path or not os.path.exists(transcript_path):
        log.error("Missing or nonexistent transcript_path: %s", transcript_path)
        sys.exit(0)

    messages = read_transcript(transcript_path)
    if not messages:
        log.warning("No messages in transcript")
        sys.exit(0)

    conversation_text = extract_recent_text(messages, MAX_TAIL_MESSAGES)
    log.debug("Extracted text:\n%s", conversation_text[:3000])
    if not conversation_text or len(conversation_text) < 50:
        log.info("Conversation too short (%d chars), skipping", len(conversation_text or ""))
        sys.exit(0)

    if not INSIGHTS_ROOT:
        log.warning("insights_root not configured in ~/.claude/memory-keeper.local.md, skipping")
        sys.exit(0)

    log.info("Analyzing %d chars of conversation", len(conversation_text))
    result = ask_haiku(conversation_text)
    if not result or result.get("kind") == "none":
        log.info("Nothing worth saving, allowing stop")
        sys.exit(0)

    cwd = input_data.get("cwd", "")
    kind = result.get("kind")

    if kind == "insight":
        saved = save_insight(
            insight=result.get("insight", ""),
            topic=result.get("topic", "general"),
            project=result.get("project", "general"),
            cwd=cwd,
            rationale=result.get("rationale", ""),
            workflow=result.get("workflow", ""),
        )
        print(json.dumps({
            "type": "system_reminder",
            "content": f"Insight saved to `{saved}`:\n**Topic**: {result.get('topic')}\n**Insight**: {result.get('insight')}"
        }))

    elif kind == "task":
        saved = save_task(
            title=result.get("title", "Untitled"),
            description=result.get("description", ""),
            project=result.get("project", "general"),
            cwd=cwd,
            rationale=result.get("rationale", ""),
            workflow=result.get("workflow", ""),
        )
        print(json.dumps({
            "type": "system_reminder",
            "content": f"Task captured to `{saved}`:\n**Task**: {result.get('title')}\n**Description**: {result.get('description')}"
        }))

    elif kind == "agent_edit":
        saved = save_agent_edit(
            insight=result.get("insight", ""),
            topic=result.get("topic", "agent-behavior"),
            cwd=cwd,
            improvement=result.get("improvement", ""),
            rationale=result.get("rationale", ""),
            workflow=result.get("workflow", ""),
        )
        print(json.dumps({
            "type": "system_reminder",
            "content": f"Agent behavior correction saved to `{saved}`:\n**Topic**: {result.get('topic')}\n**Insight**: {result.get('insight')}\n**Improvement**: {result.get('improvement', '')}"
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()
