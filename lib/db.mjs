import Database from "better-sqlite3";
import { join } from "path";
import { homedir } from "os";
import { mkdirSync } from "fs";

const DB_DIR = join(homedir(), ".claude", "debug");
const DB_PATH = join(DB_DIR, "memory-keeper.db");

export function getDb() {
  mkdirSync(DB_DIR, { recursive: true });
  const db = new Database(DB_PATH);
  db.pragma("journal_mode = WAL");

  // TODO: add migration
  db.exec(`
    CREATE TABLE IF NOT EXISTS sessions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT UNIQUE NOT NULL,
      cwd TEXT,
      project TEXT,
      conversation TEXT,
      status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'done', 'skipped', 'error', 'dropped')),
      classification TEXT,
      insight_text TEXT,
      error_message TEXT,
      retry_count INTEGER DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now')),
      processed_at TEXT
    )
  `);

  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)
  `);

  // Migration: add retry_count if missing (existing DBs)
  try {
    db.prepare("SELECT retry_count FROM sessions LIMIT 0").run();
  } catch {
    db.exec("ALTER TABLE sessions ADD COLUMN retry_count INTEGER DEFAULT 0");
  }

  return db;
}
