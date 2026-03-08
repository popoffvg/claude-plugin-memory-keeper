# memory-keeper

Persistent knowledge management plugin for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Automatically extracts insights from sessions, injects relevant context on startup, and provides search/save commands for cross-session memory.

## Features

- **Auto-capture**: Session end hook classifies conversation into insights, tasks, or behavior corrections and saves them automatically
- **Context injection**: Session start hook loads project-specific knowledge based on your working directory
- **Dual search**: Keyword-first, then semantic search across your knowledge base (via QMD)
- **Web research**: Falls back to web search when local memory is insufficient, then persists findings

## Setup

### 1. Install the plugin

```bash
claude plugin install popoffvg/claude-plugin-memory-keeper
```

### 2. Create the settings file

Create `~/.claude/memory-keeper.local.md` with your configuration:

```yaml
---
insights_root: ~/my/insights/path
log_level: DEBUG
---
```

**This file is required.** The plugin will not function without it — hooks will skip and skills will prompt you to create it.

### 3. Create the insights directory

```bash
mkdir -p ~/my/insights/path
```

### 4. Verify

Start a new Claude Code session. The SessionStart hook should load without errors. Run `/context find` — it should read your insights root.

| Setting | Required | Description |
|---------|----------|-------------|
| `insights_root` | **Yes** | Root directory for all saved knowledge (e.g. `~/ctx/insights`) |
| `log_level` | No | Logging verbosity for SessionStart hook (`DEBUG`, `INFO`, `WARN`). Default: `DEBUG` |

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [QMD MCP server](https://github.com/nicobailey/qmd) — local search engine over markdown documents
- (Optional) [Firecrawl MCP](https://github.com/mendableai/firecrawl) — for web research fallback

## Commands

| Command | Description |
|---------|-------------|
| `/context find <query>` | Search saved knowledge by keyword or topic |
| `/context find` | Show full knowledge index |
| `/context save <note>` | Persist a specific insight or fact |
| `/context check` | Analyze current session for insights worth saving |
| `/context research <topic>` | Search memory + web, then persist results |

## How It Works

### Session Start
1. Reads `insights_root` from `~/.claude/memory-keeper.local.md`
2. If not configured — skips silently
3. Matches current directory to a project in `<insights_root>/`
4. Loads `_summary.md` (or `INDEX.md` fallback) into session context

### Session End
1. Reads `insights_root` from settings — skips if not configured
2. Agent analyzes the conversation and classifies it: `insight` | `task` | `agent_edit` | `none`
3. Saves to the appropriate location:
   - **Insights** -> `<insights_root>/<project>/insights.md`
   - **Tasks** -> `<insights_root>/_tasks/pending.md`
   - **Agent edits** -> `<insights_root>/claude-config/behavior.md`

### Knowledge Search
1. `mcp__qmd__search` (keyword) on `ctx` collection
2. `mcp__qmd__deep_search` (semantic) if results are sparse
3. Fallback to `z-core` collection (Obsidian vault)

## Knowledge Structure

```
<insights_root>/
  INDEX.md              # Global knowledge index
  <project>/
    _summary.md         # Project summary (loaded on session start)
    insights.md         # Auto-captured insights
  _tasks/
    pending.md          # Extracted task items
  claude-config/
    behavior.md         # Agent behavior corrections
```

## License

MIT
