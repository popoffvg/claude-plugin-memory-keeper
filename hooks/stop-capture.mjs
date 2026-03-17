#!/usr/bin/env node
// Stop hook: captures session metadata + conversation to SQLite, spawns background worker.
// Designed to be fast and never fail — all heavy lifting is in the worker.

import { readFileSync, readdirSync, statSync } from "fs";
import { join, basename } from "path";
import { homedir } from "os";
import { spawn, execSync } from "child_process";
import { getDb } from "../lib/db.mjs";
import { loadConfig } from "../lib/config.mjs";

export const MAX_CONVERSATION_CHARS = 8000;

export function findSessionJsonl(sessionId) {
  if (!sessionId) return null;
  const projectsDir = join(homedir(), ".claude", "projects");
  try {
    const dirs = readdirSync(projectsDir);
    const candidates = [];

    for (const dir of dirs) {
      const fullDir = join(projectsDir, dir);
      try {
        const stat = statSync(fullDir);
        if (!stat.isDirectory()) continue;
        const files = readdirSync(fullDir).filter((f) => f.endsWith(".jsonl"));
        for (const f of files) {
          const fp = join(fullDir, f);
          const fstat = statSync(fp);
          candidates.push({ path: fp, mtime: fstat.mtimeMs });
        }
      } catch {}
    }

    candidates.sort((a, b) => b.mtime - a.mtime);

    for (const c of candidates.slice(0, 30)) {
      try {
        const firstLine = readFileSync(c.path, "utf8").split("\n")[0];
        const first = JSON.parse(firstLine);
        if (
          first.sessionId === sessionId ||
          first.session_id === sessionId
        ) {
          return c.path;
        }
      } catch {}
    }
  } catch {}
  return null;
}

export function extractConversation(jsonlPath) {
  const content = readFileSync(jsonlPath, "utf8");
  const lines = content.split("\n").filter(Boolean);

  const messages = [];
  for (const line of lines) {
    try {
      const record = JSON.parse(line);

      if (record.type === "user" || record.type === "human") {
        const text =
          typeof record.message?.content === "string"
            ? record.message.content
            : "";
        if (
          text &&
          !text.startsWith("<command") &&
          !text.startsWith("<system") &&
          !text.startsWith("<local")
        ) {
          messages.push(`User: ${text}`);
        }
      } else if (record.type === "assistant") {
        const blocks = record.message?.content || [];
        const texts = Array.isArray(blocks)
          ? blocks
              .filter((b) => b.type === "text")
              .map((b) => b.text)
              .join("\n")
          : typeof blocks === "string"
            ? blocks
            : "";
        if (texts) {
          messages.push(`Assistant: ${texts}`);
        }
      }
    } catch {}
  }

  // Take last N messages that fit within budget
  let total = 0;
  const selected = [];
  for (let i = messages.length - 1; i >= 0; i--) {
    if (total + messages[i].length > MAX_CONVERSATION_CHARS) break;
    selected.unshift(messages[i]);
    total += messages[i].length;
  }

  return selected.join("\n\n");
}

export function projectFromJsonlPath(jsonlPath) {
  // Path: ~/.claude/projects/-Users-popoffvg-Documents-git-mil-pl/session.jsonl
  // Dir name encodes the cwd with / → -
  const dir = basename(join(jsonlPath, ".."));
  // Last segment of the decoded path is the project name
  const parts = dir.split("-").filter(Boolean);
  return parts[parts.length - 1] || "unknown";
}

export function detectProject(cwd) {
  if (!cwd) return "unknown";
  try {
    const root = execSync(`git -C "${cwd}" rev-parse --show-toplevel 2>/dev/null`, {
      encoding: "utf8",
    }).trim();
    return basename(root);
  } catch {
    return basename(cwd);
  }
}

function run() {
  const config = loadConfig();
  if (!config.insights_root) process.exit(0);

  const raw = readFileSync("/dev/stdin", "utf8");
  if (!raw.trim()) process.exit(0);
  const input = JSON.parse(raw);
  const sessionId = input.session_id || input.sessionId;
  const cwd = input.cwd || "";

  if (!sessionId) process.exit(0);

  const jsonlPath = findSessionJsonl(sessionId);
  const conversation = jsonlPath ? extractConversation(jsonlPath) : "";

  if (!conversation || conversation.length < 50) process.exit(0);

  // Extract project from Claude projects path: -Users-popoffvg-Documents-git-mil-pl → pl
  const project = jsonlPath ? projectFromJsonlPath(jsonlPath) : detectProject(cwd);

  // Store in SQLite
  const db = getDb();
  try {
    db.prepare(
      `INSERT OR IGNORE INTO sessions (session_id, cwd, project, conversation, status)
       VALUES (?, ?, ?, ?, 'pending')`
    ).run(sessionId, cwd, project, conversation);
  } finally {
    db.close();
  }

  // Spawn background worker (detached, won't block session exit)
  const workerPath = join(import.meta.dirname, "..", "worker", "process-sessions.mjs");
  const child = spawn("node", [workerPath], {
    detached: true,
    stdio: "ignore",
    env: { ...process.env },
  });
  child.unref();
}

// Only run when executed directly, not when imported for tests
const isMain = process.argv[1] && import.meta.url.endsWith(process.argv[1].replace(/\\/g, "/"));
if (isMain) {
  run();
}
