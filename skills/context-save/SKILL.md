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

## Storage

- Root: `<insights_root>/`
- Per project: `<insights_root>/<project>/`
