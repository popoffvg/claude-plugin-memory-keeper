---
name: context-check
description: This skill should be used when the user says "context check", "check for insights", "anything worth saving", "review session", or wants to analyze the current conversation for valuable learnings worth persisting — debugging discoveries, architectural decisions, corrections, workflow patterns.
---

# Context Check

Analyze the recent conversation to detect facts worth persisting.

## Usage

`/context check`

## What to extract

Scan the last 10 human/assistant messages for concrete facts in these categories:

**insight** — completed work:
- Code changes with context (what was done + why)
- Patterns applied or techniques used
- Gotchas, pitfalls, or surprising behaviors discovered
- Decisions made with reasoning

**agent_edit** — AI behavior changes:
- Agent guards, skill descriptions, hook logic edits
- Prompt template changes
- CLAUDE.md or plugin config updates
- Directives that control how the assistant works

**task** — ONLY unstarted intentions:
- "I need to refactor X", "TODO: add Y"
- Work the user plans but has NOT begun

## Fact quality

Good facts (concise, high-level, with WHY):
- "ContextDomain is a new field for matching block outputs by domain context"
- "guard findSessionJsonl against undefined sessionId — was matching real files"
- "skills should describe pure workflow steps — moved delegation details to agent frontmatter"

Bad facts (skip these):
- Too granular: "added field to BObjectSpec" (what is it FOR?)
- Too vague: "fixed authentication issues"
- Routine: "ran tests", "committed code", "read a file"
- Reasoning: "this is because...", "the issue stems from..."

## Process

1. Read the current session transcript
2. Extract facts grouped by topic and classification
3. Save immediately using the `context-save` skill — do NOT ask for confirmation

## Configuration

Read `insights_root` from `~/.claude/memory-keeper.local.md` YAML frontmatter.

## Output

If no facts found, return "nothing worth saving".
If facts found, save them immediately and report what was saved (topic + classification + file).
