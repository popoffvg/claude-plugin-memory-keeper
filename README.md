# memory-keeper

Persistent knowledge management plugin for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Automatically extracts insights from sessions, injects relevant context on startup, and provides search/save commands for cross-session memory.

## Features

- **Auto-capture**: Session end hook classifies conversation into insights, tasks, or behavior corrections and saves them automatically
- **Context injection**: Session start hook loads project-specific knowledge based on your working directory
- **Dual search**: Keyword-first, then semantic search across your knowledge base (via QMD)
- **Web research**: Falls back to web search when local memory is insufficient, then persists findings

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
1. Reads config from `~/.claude/memory-keeper.local.md`
2. Matches current directory to a project in `~/ctx/insights/`
3. Loads `_summary.md` (or `INDEX.md` fallback) into session context

### Session End
1. Extracts last messages from conversation
2. Sends to Haiku for classification: `insight` | `task` | `agent_edit` | `none`
3. Saves to the appropriate location:
   - **Insights** -> `~/ctx/insights/<project>/insights.md`
   - **Tasks** -> `~/ctx/insights/_tasks/pending.md`
   - **Agent edits** -> `~/ctx/insights/claude-config/behavior.md`

### Knowledge Search
1. `mcp__qmd__search` (keyword) on `ctx` collection
2. `mcp__qmd__deep_search` (semantic) if results are sparse
3. Fallback to `z-core` collection (Obsidian vault)

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [QMD MCP server](https://github.com/nicobailey/qmd) — local search engine over markdown documents
- `ANTHROPIC_API_KEY` env var — used by the stop hook for Haiku classification
- (Optional) [Firecrawl MCP](https://github.com/mendableai/firecrawl) — for web research fallback

## Configuration

Create `~/.claude/memory-keeper.local.md` with YAML frontmatter:

```yaml
---
insights_root: ~/ctx/insights
log_level: DEBUG
---
```

| Field | Default | Description |
|-------|---------|-------------|
| `insights_root` | `~/ctx/insights` | Root directory for all saved knowledge |
| `log_level` | `DEBUG` | Logging verbosity for the stop hook |

## Knowledge Structure

```
~/ctx/insights/
  INDEX.md              # Global knowledge index
  <project>/
    _summary.md         # Project summary (loaded on session start)
    insights.md         # Auto-captured insights
  _tasks/
    pending.md          # Extracted task items
  claude-config/
    behavior.md         # Agent behavior corrections
```

## Installation

```bash
claude plugin install popoffvg/claude-plugin-memory-keeper
```

## License

MIT
