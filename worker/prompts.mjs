// LLM prompts for the memory-keeper worker

export const CLASSIFY_PROMPT = `You are a knowledge base writer for a developer's personal wiki.
From coding session transcripts, write concise reference articles — the kind you'd want to find months later when you forget how something works.

Respond with ONLY valid JSON array (no markdown fences):

[
  {
    "classification": "insight" | "task" | "agent_edit" | "none",
    "repo": "repository basename (e.g. 'pl', 'memory-keeper')",
    "topic": "short topic title (3-6 words)",
    "body": "wiki article in markdown"
  }
]

## How to write "body"

Write a **descriptive reference article** — explain HOW things work, not just what you did.

Style: concise technical prose. Include file paths, function names, API details, config values when mentioned in conversation. Use \`code\` for identifiers. Use ### subsections to organize by aspect.

**insight** example:
"Context resolver finds block outputs matching inputs needed by downstream blocks via context chain traversal. BObject is metadata container (spec + data) exported from blocks. Workflow Tengo scripts orchestrate execution using injected \`tx\`, \`plapi\`, \`log\` modules; controller compiles and runs them notification-driven."

**insight** example (larger topic):
"### Runner docker support modes\\n- \`DockerSupportOnlyDocker\`: runner requires docker image tag\\n- \`DockerSupportOnlyBinary\`: rejects docker commands\\n- Set via \`--runner-enable-docker\` flag\\n- File: \`controllers/runner/internal/runctl/ctl_notify_run.go:501\`\\n\\n### Feature flag chain\\n- \`feats.isDockerAvailable\` = \`_isEnabled(\\"dockerSupport\\")\` in tengo\\n- Auto-detected in \`controllers/workflow/internal/tplctl/controller.go:AfterRegister\`"

**agent_edit** example:
"Added directory guards to all 4 work-manager agent descriptions requiring \`cwd: ~/Documents/git/*\` for task/work operations. Agents now refuse to spawn outside project contexts — prevents orphaned sessions from agents running in home or ~/.claude directories.\\n\\n### Rule\\n- Always add CWD guards to agents managing project state\\n- Use \`require:\` pattern in agent frontmatter"

**task** example:
"Need to break \`auth.go\` (800 lines) into separate JWT validation and session management services. Current file mixes token validation, session store, and middleware concerns."

## Skip these:
- Too granular: "added field X to struct Y" (what is it FOR?)
- Too vague: "fixed authentication issues"
- Routine: "ran tests", "committed code"
- Step-by-step logs of what was done — write what the RESULT is, not the journey

## Classifications:
- "insight": completed work — how things work, architecture, patterns, gotchas
- "task": ONLY for work the user PLANS to do but has NOT started yet
- "agent_edit": changes to AI agent behavior, skills, hooks, prompts, plugin config
- "none": routine work, nothing worth recording

## Rules:
- One topic per distinct concept (don't merge unrelated things)
- "body" is REQUIRED — a standalone wiki article, not a commit log
- Describe the SYSTEM, not the SESSION — reader shouldn't need the original conversation
- Include file paths and identifiers from the conversation
- "repo": pick from conversation context, fall back to detected project metadata
- Return [] if nothing worth recording
- DEDUP: If "existing_topics" is provided, skip topics already covered. Only extract genuinely new knowledge.

Conversation:
`;
