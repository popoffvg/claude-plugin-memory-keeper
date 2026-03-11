---
name: context-save
description: This skill should be used when the user says "context save", "remember this", "save this", "note this for later", "keep this", or wants to persist any knowledge, pattern, decision, or learning from the current session to persistent memory.
---

# Context Save

## Usage

`/context save <what to remember>`

Examples:
- `/context save the auth service uses JWT with RS256 keys rotated weekly`
- `/context save debugging k8s CrashLoopBackOff — always check resource limits first`
- `/context save` (will ask what to save)

## Note Types

Every note has a `type:` field in frontmatter:

| Type | When to use | Who sets it |
|------|------------|-------------|
| `insight` | Per-project learning from a conversation (default) | Manual `/context save`, Stop hook |
| `common` | Global/cross-project knowledge from research or web | `context-research` skill, or when user says "common knowledge", "general fact" |
| `task` | Active task context (use `task` skill instead) | `task` skill |

## Configuration

Read `insights_root` from `~/.claude/memory-keeper.local.md` YAML frontmatter. If the file is missing, stop and ask the user to create it with the required settings (see plugin README).

## Project Detection

Derive `<project>` by running `git -C <cwd> rev-parse --show-toplevel 2>/dev/null` and taking the basename. If not a git repo, use the basename of cwd.

## Active Task Awareness

Before saving, check `<insights_root>/_tasks/pending.md` for an active task (status: active).

- **If active task exists and type is `insight`**: save to `<insights_root>/_tasks/<task-slug>/notes.md` instead of the project folder. Add `_(repo: <project>)_` to the entry. Also add `<project>` to the task's `Repos` list in `pending.md` if not already there.
- **If no active task**: save to `<insights_root>/<project>/insights.md` as usual.

## Deduplication

Before appending any entry, **read the target file** and check for duplicates:

1. **Exact match**: skip if the same topic heading (`## <topic>`) already exists
2. **Semantic overlap**: skip if an existing entry covers the same fact — even with different wording. Compare the core claim, not the phrasing.
3. **Superset**: if the new insight is a broader version of an existing one, **replace** the old entry instead of appending
4. **Subset**: if an existing entry already covers a broader version of the new insight, skip

When in doubt, prefer skipping over creating a near-duplicate. One precise entry is better than two fuzzy ones.

## Storage

- Root: `<insights_root>/`
- Per project: `<insights_root>/<project>/`
- Per task: `<insights_root>/_tasks/<task-slug>/notes.md`
