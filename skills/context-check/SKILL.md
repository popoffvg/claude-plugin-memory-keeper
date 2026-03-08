---
name: context-check
description: This skill should be used when the user says "context check", "check for insights", "anything worth saving", "review session", or wants to analyze the current conversation for valuable learnings worth persisting — debugging discoveries, architectural decisions, corrections, workflow patterns.
---

# Context Check

Analyze the recent conversation transcript to detect valuable insights, learnings, patterns, debugging discoveries, architectural decisions, or corrections worth remembering for future sessions.

## Usage

`/context check`

## What to look for

Scan the last 10 human/assistant messages for:
- Non-obvious debugging patterns or root causes
- Architectural decisions with reasoning
- Gotchas, pitfalls, or surprising behaviors
- Workflow optimizations discovered through practice
- Corrections the user made that reveal preferences or conventions

Only flag genuinely useful knowledge — not routine code changes, simple fixes, or standard operations.

## Process

1. Read the current session transcript
2. Extract recent conversation text
3. Identify concrete facts only — do NOT include reasoning or analysis narrative. Report:
   - What the user did (tool call, code change, command run)
   - What the user corrected ("I did X, user said do Y instead")
   - Observed behavior or outcome (error message, test result, config that worked)
   - Keep each item as a single factual statement, no interpretation
4. If facts are found, present them as a flat list and ask the user whether to save
5. If user agrees, use the `context-save` skill to persist it

## Configuration

Read `insights_root` from `~/.claude/memory-keeper.local.md` YAML frontmatter. If the file is missing, stop and ask the user to create it with the required settings (see plugin README).

## Storage Location

All insights are stored in `<insights_root>/` using QMD MCP for indexing and search.

## Output

If no insights are found, return a simple confirmation.

If insights are found, present the insight and ask whether to save it to the insights knowledge base.
