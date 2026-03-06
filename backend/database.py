import sqlite3
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            subreddit TEXT NOT NULL,
            title TEXT NOT NULL,
            selftext TEXT,
            author TEXT,
            score INTEGER DEFAULT 0,
            num_comments INTEGER DEFAULT 0,
            url TEXT,
            created_utc INTEGER NOT NULL,
            collected_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT NOT NULL REFERENCES posts(id),
            summary TEXT,
            category TEXT,
            severity TEXT,
            has_existing_solution BOOLEAN,
            existing_solution_notes TEXT,
            willingness_to_pay TEXT,
            relevance_tags TEXT,
            analyzed_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT NOT NULL REFERENCES posts(id),
            kanban_status TEXT DEFAULT 'new',
            notes TEXT,
            favorited_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit);
        CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_utc);
        CREATE INDEX IF NOT EXISTS idx_analysis_post_id ON analysis(post_id);
        CREATE INDEX IF NOT EXISTS idx_analysis_category ON analysis(category);
        CREATE INDEX IF NOT EXISTS idx_favorites_post_id ON favorites(post_id);
    """)
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
