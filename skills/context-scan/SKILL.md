---
name: context-scan
description: Scan recent Claude session logs for missed insights (fallback when Stop hook fails). This skill should be used when the user says "context scan", "scan sessions", "check old sessions", "find missed insights", or wants to recover insights from sessions where the Stop hook did not fire. Also used by hourly cron to automatically sweep for uncaptured knowledge.
---

# Context Scan

Scan recent Claude Code session logs for insights that the Stop hook may have missed.

## Usage

`/context scan` — scan sessions from the last hour
`/context scan 3h` — scan sessions from the last 3 hours
`/context scan 1d` — scan sessions from the last day

## Configuration

Read `insights_root` from `~/.claude/memory-keeper.local.md` YAML frontmatter. If the file is missing, stop and ask the user to create it with the required settings (see plugin README).

## Procedure

### Step 1: Find recent sessions

1. List all `~/.claude/projects/` subdirectories
2. In each, find `*.jsonl` files modified within the requested time window (default: 1 hour)
3. Skip the **current** session file (match by `sessionId` from the first record)
4. Read the marker file `<insights_root>/.scanned_sessions` to skip already-processed sessions

### Step 2: Extract conversations

For each unscanned session JSONL file:

1. Read lines where `type` is `"user"` or `"assistant"`
2. For `user` messages: extract `message.content` (string), skip lines starting with `<command`, `<system`, `<local`
3. For `assistant` messages: extract text blocks from `message.content` array (where `block.type == "text"`)
4. Build a conversation transcript (max 4000 chars per session, take last N messages that fit)

### Step 3: Classify and extract

For each session transcript, classify it into one of:

- **insight** — valuable debugging pattern, architectural decision, gotcha, workflow optimization
- **task** — development task intention (implement, fix, refactor)
- **agent_edit** — user correcting AI behavior
- **none** — routine, nothing worth recording

Only flag genuinely useful knowledge. Look for:
- Non-obvious debugging patterns or root causes
- Architectural decisions with reasoning
- Gotchas, pitfalls, or surprising behaviors
- Workflow optimizations discovered through practice

If classification is **none**, skip that session.

### Step 4: Save insights

For each non-none session, use the `context-save` skill procedure:

- **insight** → append to `<insights_root>/<project>/insights.md`
- **task** → append to `<insights_root>/_tasks/pending.md`
- **agent_edit** → append to `<insights_root>/claude-config/behavior.md`

Derive `<project>` from the session's `cwd` field (basename of the working directory).

### Step 5: Mark as scanned

Append each processed session filename to `<insights_root>/.scanned_sessions` (one UUID per line) to avoid re-processing.

## Output

Report:
- Number of sessions scanned
- Number of insights found and saved
- Brief list of what was saved (topic + type)
- "No new insights" if nothing found
