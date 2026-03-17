---
name: context-save
description: This skill should be used when the user says "context save", "remember this", "save this", "note this for later", "keep this", or wants to persist any knowledge, pattern, decision, or learning from the current session to persistent memory.
---

# Context Save

## Usage

`/context save <what to remember>`

Examples:
- `/context save ContextDomain is a new field for matching block outputs by domain context`
- `/context save guard findSessionJsonl against undefined sessionId — was matching real files`
- `/context save` (will ask what to save)

## Configuration

Read `insights_root` from `~/.claude/memory-keeper.local.md` YAML frontmatter. If the file is missing, stop and ask the user to create it with the required settings (see plugin README).

## Classifications

Each entry gets one classification that determines where it's saved:

| Classification | What it is | Saved to |
|---|---|---|
| `insight` | Completed work — code changes, patterns applied, decisions made, gotchas | `<insights_root>/<repo>/insights.md` |
| `agent_edit` | Changes to AI behavior — agent guards, skill descriptions, hook logic, prompts, CLAUDE.md, plugin config | `<insights_root>/claude-config/behavior.md` |
| `task` | ONLY unstarted intentions — "I need to refactor X", "TODO: add Y" | `<insights_root>/_tasks/pending.md` |

One save invocation may produce multiple entries with different classifications.

## Fact Format

Each entry is a topic heading + bullet-pointed facts. Each fact = WHAT changed + WHY/FOR WHAT.

```
## <topic> — <YYYY-MM-DD HH:MM>
- <fact 1: what was done + why it matters>
- <fact 2: what was done + why it matters>
```

Good facts (concise, high-level, with WHY):
- "ContextDomain is a new field for matching block outputs by domain context"
- "dependency injection for generateText — makes processSession unit-testable without LLM"
- "guard findSessionJsonl against undefined sessionId — was matching real files"

Bad facts (too granular or vague):
- "added ContextDomain field to BObjectSpec" (what is it FOR?)
- "fixed authentication issues" (too vague)

## Repo Detection

Derive `<repo>` by running `git -C <cwd> rev-parse --show-toplevel 2>/dev/null` and taking the basename. If not a git repo, use the basename of cwd. The user or context may override (e.g. if the conversation clearly refers to a different project).

## Active Task Awareness

Before saving an `insight`, check `<insights_root>/_tasks/pending.md` for an active task (status: active).

- **If active task exists**: save to `<insights_root>/_tasks/<task-slug>/notes.md` instead of the project folder.
- **If no active task**: save to `<insights_root>/<repo>/insights.md` as usual.

`agent_edit` and `task` entries always go to their fixed locations regardless of active task.

## Deduplication

Before appending any entry, **read the target file** and check for duplicates:

1. **Exact match**: skip if the same topic heading (`## <topic>`) already exists
2. **Semantic overlap**: skip if an existing entry covers the same fact in different words
3. **Superset**: if the new insight is broader, **replace** the old entry
4. **Subset**: if an existing entry is already broader, skip

One precise entry is better than two fuzzy ones.

## Storage

- Insights: `<insights_root>/<repo>/insights.md`
- Agent edits: `<insights_root>/claude-config/behavior.md`
- Tasks: `<insights_root>/_tasks/pending.md`
- Task notes: `<insights_root>/_tasks/<task-slug>/notes.md`
