import json
import time
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from database import get_connection

app = FastAPI(title="Signal Scanner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


def parse_post_with_analysis(row):
    """Convert a joined post+analysis row into a response dict, parsing relevance_tags."""
    d = dict(row)
    if "relevance_tags" in d and d["relevance_tags"]:
        try:
            d["relevance_tags"] = json.loads(d["relevance_tags"])
        except (json.JSONDecodeError, TypeError):
            d["relevance_tags"] = []
    elif "relevance_tags" in d:
        d["relevance_tags"] = []
    return d


# ---------------------------------------------------------------------------
# GET /api/stats
# ---------------------------------------------------------------------------
@app.get("/api/stats")
def get_stats():
    conn = get_connection()
    try:
        total_posts = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        analyzed = conn.execute("SELECT COUNT(DISTINCT post_id) FROM analysis").fetchone()[0]

        # By category
        rows = conn.execute(
            "SELECT category, COUNT(*) as count FROM analysis GROUP BY category"
        ).fetchall()
        by_category = {r["category"]: r["count"] for r in rows}

        # By severity
        rows = conn.execute(
            "SELECT severity, COUNT(*) as count FROM analysis GROUP BY severity"
        ).fetchall()
        by_severity = {r["severity"]: r["count"] for r in rows}

        # By subreddit
        rows = conn.execute(
            "SELECT subreddit, COUNT(*) as count FROM posts GROUP BY subreddit"
        ).fetchall()
        by_subreddit = {r["subreddit"]: r["count"] for r in rows}

        return {
            "total_posts": total_posts,
            "analyzed": analyzed,
            "by_category": by_category,
            "by_severity": by_severity,
            "by_subreddit": by_subreddit,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# GET /api/trends
# ---------------------------------------------------------------------------
@app.get("/api/trends")
def get_trends():
    conn = get_connection()
    try:
        # Posts collected per week (using created_utc as unix timestamp)
        rows = conn.execute("""
            SELECT
                strftime('%Y-%W', datetime(created_utc, 'unixepoch')) as week,
                COUNT(*) as count
            FROM posts
            GROUP BY week
            ORDER BY week
        """).fetchall()
        posts_per_week = [{"week": r["week"], "count": r["count"]} for r in rows]

        # Categories over time (per week)
        rows = conn.execute("""
            SELECT
                strftime('%Y-%W', datetime(p.created_utc, 'unixepoch')) as week,
                a.category,
                COUNT(*) as count
            FROM posts p
            JOIN analysis a ON a.post_id = p.id
            GROUP BY week, a.category
            ORDER BY week, a.category
        """).fetchall()
        categories_over_time = [
            {"week": r["week"], "category": r["category"], "count": r["count"]}
            for r in rows
        ]

        return {
            "posts_per_week": posts_per_week,
            "categories_over_time": categories_over_time,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# GET /api/posts
# ---------------------------------------------------------------------------
@app.get("/api/posts")
def get_posts(
    subreddit: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    include_not_relevant: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    conn = get_connection()
    try:
        conditions = []
        params = []

        # Exclude not_relevant by default
        if not include_not_relevant:
            conditions.append("a.category != 'not_relevant'")

        if subreddit:
            conditions.append("p.subreddit = ?")
            params.append(subreddit)
        if category:
            conditions.append("a.category = ?")
            params.append(category)
        if severity:
            conditions.append("a.severity = ?")
            params.append(severity)
        if search:
            conditions.append("(p.title LIKE ? OR p.selftext LIKE ?)")
            params.append(f"%{search}%")
            params.append(f"%{search}%")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Count total matching
        count_sql = f"""
            SELECT COUNT(*) FROM posts p
            LEFT JOIN analysis a ON a.post_id = p.id
            WHERE {where_clause}
        """
        total = conn.execute(count_sql, params).fetchone()[0]

        # Fetch page
        offset = (page - 1) * per_page
        data_sql = f"""
            SELECT p.*, a.summary, a.category, a.severity,
                   a.has_existing_solution, a.existing_solution_notes,
                   a.willingness_to_pay, a.relevance_tags, a.analyzed_at
            FROM posts p
            LEFT JOIN analysis a ON a.post_id = p.id
            WHERE {where_clause}
            ORDER BY p.created_utc DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(data_sql, params + [per_page, offset]).fetchall()
        posts = [parse_post_with_analysis(r) for r in rows]

        return {
            "posts": posts,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# GET /api/posts/{id}
# ---------------------------------------------------------------------------
@app.get("/api/posts/{post_id}")
def get_post(post_id: str):
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT p.*, a.id as analysis_id, a.summary, a.category, a.severity,
                   a.has_existing_solution, a.existing_solution_notes,
                   a.willingness_to_pay, a.relevance_tags, a.analyzed_at
            FROM posts p
            LEFT JOIN analysis a ON a.post_id = p.id
            WHERE p.id = ?
        """, [post_id]).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Post not found")

        post = parse_post_with_analysis(row)

        # Check if favorited
        fav = conn.execute(
            "SELECT * FROM favorites WHERE post_id = ?", [post_id]
        ).fetchone()
        post["favorite"] = row_to_dict(fav) if fav else None

        return post
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# POST /api/posts/{id}/favorite
# ---------------------------------------------------------------------------
@app.post("/api/posts/{post_id}/favorite")
def add_favorite(post_id: str):
    conn = get_connection()
    try:
        # Check post exists
        post = conn.execute("SELECT id FROM posts WHERE id = ?", [post_id]).fetchone()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Check not already favorited
        existing = conn.execute(
            "SELECT id FROM favorites WHERE post_id = ?", [post_id]
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Post already favorited")

        now = int(time.time())
        conn.execute(
            "INSERT INTO favorites (post_id, kanban_status, notes, favorited_at, updated_at) VALUES (?, 'new', '', ?, ?)",
            [post_id, now, now],
        )
        conn.commit()

        fav = conn.execute(
            "SELECT * FROM favorites WHERE post_id = ?", [post_id]
        ).fetchone()
        return row_to_dict(fav)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# DELETE /api/posts/{id}/favorite
# ---------------------------------------------------------------------------
@app.delete("/api/posts/{post_id}/favorite")
def remove_favorite(post_id: str):
    conn = get_connection()
    try:
        result = conn.execute("DELETE FROM favorites WHERE post_id = ?", [post_id])
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Favorite not found")
        return {"detail": "Favorite removed"}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# PATCH /api/favorites/{id}
# ---------------------------------------------------------------------------
class FavoriteUpdate(BaseModel):
    kanban_status: Optional[str] = None
    notes: Optional[str] = None


@app.patch("/api/favorites/{favorite_id}")
def update_favorite(favorite_id: int, update: FavoriteUpdate):
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT * FROM favorites WHERE id = ?", [favorite_id]
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Favorite not found")

        updates = []
        params = []
        if update.kanban_status is not None:
            updates.append("kanban_status = ?")
            params.append(update.kanban_status)
        if update.notes is not None:
            updates.append("notes = ?")
            params.append(update.notes)

        if not updates:
            return row_to_dict(existing)

        updates.append("updated_at = ?")
        params.append(int(time.time()))
        params.append(favorite_id)

        conn.execute(
            f"UPDATE favorites SET {', '.join(updates)} WHERE id = ?", params
        )
        conn.commit()

        updated = conn.execute(
            "SELECT * FROM favorites WHERE id = ?", [favorite_id]
        ).fetchone()
        return row_to_dict(updated)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# GET /api/favorites
# ---------------------------------------------------------------------------
@app.get("/api/favorites")
def get_favorites():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT f.*, p.subreddit, p.title, p.selftext, p.author, p.score,
                   p.num_comments, p.url, p.created_utc,
                   a.summary, a.category, a.severity, a.relevance_tags
            FROM favorites f
            JOIN posts p ON p.id = f.post_id
            LEFT JOIN analysis a ON a.post_id = f.post_id
            ORDER BY f.updated_at DESC
        """).fetchall()

        grouped = {}
        for row in rows:
            item = parse_post_with_analysis(row)
            status = item.get("kanban_status", "new")
            grouped.setdefault(status, []).append(item)

        return grouped
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# POST /api/collect
# ---------------------------------------------------------------------------
@app.post("/api/collect")
def trigger_collect():
    return {
        "detail": "Collection not yet available. Reddit API credentials are not configured. "
                  "Once set up, this endpoint will trigger a new Reddit scan and analysis."
    }


# ---------------------------------------------------------------------------
# GET /api/budget
# ---------------------------------------------------------------------------
@app.get("/api/budget")
def get_budget():
    return {
        "anthropic_calls_today": 0,
        "anthropic_calls_total": 0,
        "reddit_calls_today": 0,
        "reddit_calls_total": 0,
        "detail": "Budget tracking is a placeholder. Will be implemented with actual API usage logging.",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
