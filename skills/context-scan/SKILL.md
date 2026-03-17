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

### Step 3: Classify and extract facts

For each session, extract entries grouped by topic. Each entry has:

- **classification**: `insight` | `agent_edit` | `task` | `none`
- **repo**: repository basename from the projects dir path (last segment of encoded path)
- **topic**: short title (3-6 words)
- **facts**: 1-3 bullet points, each = WHAT changed + WHY

Classifications:
- `insight`: completed work — code changes, patterns applied, decisions made, gotchas
- `agent_edit`: changes to AI behavior — agent guards, skill descriptions, hook logic, prompts, plugin config
- `task`: ONLY unstarted intentions (NOT completed work)
- `none`: routine, skip

One session may produce multiple entries with different classifications.

### Step 4: Deduplicate and save

Before saving, read the target file and check for duplicates:
- **Exact match**: skip if the same topic heading already exists
- **Semantic overlap**: skip if an existing entry covers the same fact in different words
- **Superset**: if the new insight is broader, replace the old entry
- **Subset**: if an existing entry is already broader, skip

Save locations:
- `insight` → `<insights_root>/<repo>/insights.md` (or `_tasks/<slug>/notes.md` if active task)
- `agent_edit` → `<insights_root>/claude-config/behavior.md`
- `task` → `<insights_root>/_tasks/pending.md`

Entry format:
```
## <topic> — <YYYY-MM-DD HH:MM>
- <fact with context>
```

### Step 5: Mark as scanned

Append each processed session filename to `<insights_root>/.scanned_sessions` (one UUID per line) to avoid re-processing.

## Output

Report:
- Number of sessions scanned
- Number of entries found and saved (by classification)
- Brief list of what was saved (topic + classification)
- "No new insights" if nothing found
