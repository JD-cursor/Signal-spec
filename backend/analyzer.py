"""Claude analysis pipeline — batch triage then deep analysis on winners."""

import json
import time
import anthropic
from database import get_connection, init_db
from config import ANTHROPIC_API_KEY

TRIAGE_BATCH_SIZE = 20

TRIAGE_SYSTEM = "You quickly assess Reddit posts to identify which ones contain real pain points that could be solved with software. Respond ONLY with valid JSON."

TRIAGE_PROMPT_TEMPLATE = """Below are Reddit posts. For each, decide if it contains a genuine pain point worth analyzing further.

{posts_block}

Respond with a JSON array of post IDs that ARE worth analyzing (contain a real pain point, frustration, or unmet need):
{{"worth_analyzing": ["id1", "id2", ...]}}

Be selective — only include posts with clear, specific pain points. Skip generic questions, memes, or vague complaints."""

ANALYSIS_SYSTEM = """You are analyzing a Reddit post to identify whether it contains a real pain point that could be solved with a software product.

Respond ONLY with valid JSON, no markdown formatting."""

ANALYSIS_PROMPT_TEMPLATE = """Post title: {title}
Post body: {selftext}
Subreddit: r/{subreddit}

Respond in JSON:
{{
  "summary": "One-sentence plain-language description of the pain point",
  "category": "tooling_gap | workflow_friction | missing_product | price_complaint | integration_gap | other",
  "severity": "low | medium | high",
  "has_existing_solution": true/false,
  "existing_solution_notes": "If yes, what exists and why isn't it enough",
  "willingness_to_pay": "unlikely | possible | likely",
  "relevance_tags": ["tag1", "tag2"]
}}

If the post doesn't contain a meaningful pain point, return:
{{
  "summary": null,
  "category": "not_relevant"
}}"""


def get_unanalyzed_posts(conn) -> list[dict]:
    rows = conn.execute(
        """SELECT p.id, p.title, p.selftext, p.subreddit
           FROM posts p
           LEFT JOIN analysis a ON p.id = a.post_id
           WHERE a.id IS NULL"""
    ).fetchall()
    return [dict(row) for row in rows]


def triage_batch(client: anthropic.Anthropic, posts: list[dict]) -> set[str]:
    """Send a batch of posts to Claude for quick triage. Returns set of IDs worth analyzing."""
    posts_block = "\n\n".join(
        f"[{p['id']}] r/{p['subreddit']}: {p['title']}\n{p['selftext'][:200]}"
        for p in posts
    )
    prompt = TRIAGE_PROMPT_TEMPLATE.format(posts_block=posts_block)

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=TRIAGE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        result = json.loads(text)
        return set(result.get("worth_analyzing", []))
    except (json.JSONDecodeError, IndexError, KeyError, anthropic.APIError) as e:
        print(f"  Triage error: {e} — falling back to analyzing all in batch")
        return {p["id"] for p in posts}


def analyze_post(client: anthropic.Anthropic, post: dict) -> dict | None:
    """Send a single post to Claude for deep analysis. Returns parsed JSON or None."""
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        title=post["title"],
        selftext=post["selftext"][:2000],
        subreddit=post["subreddit"],
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=ANALYSIS_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        return json.loads(text)
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        print(f"  Parse error for {post['id']}: {e}")
        return None
    except anthropic.APIError as e:
        print(f"  API error for {post['id']}: {e}")
        return None


def store_analysis(conn, post_id: str, result: dict):
    now = int(time.time())

    category = result.get("category", "other")
    if category == "not_relevant":
        conn.execute(
            """INSERT INTO analysis (post_id, summary, category, analyzed_at)
               VALUES (?, ?, ?, ?)""",
            (post_id, None, "not_relevant", now),
        )
    else:
        relevance_tags = result.get("relevance_tags", [])
        conn.execute(
            """INSERT INTO analysis (post_id, summary, category, severity,
               has_existing_solution, existing_solution_notes, willingness_to_pay,
               relevance_tags, analyzed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                post_id,
                result.get("summary"),
                category,
                result.get("severity"),
                result.get("has_existing_solution", False),
                result.get("existing_solution_notes"),
                result.get("willingness_to_pay"),
                json.dumps(relevance_tags) if relevance_tags else "[]",
                now,
            ),
        )


def mark_not_relevant(conn, post_id: str):
    now = int(time.time())
    conn.execute(
        "INSERT INTO analysis (post_id, summary, category, analyzed_at) VALUES (?, ?, ?, ?)",
        (post_id, None, "not_relevant", now),
    )


def analyze_all():
    """Batch triage, then deep-analyze only the promising posts."""
    init_db()
    conn = get_connection()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    posts = get_unanalyzed_posts(conn)
    print(f"Found {len(posts)} unanalyzed posts.")

    if not posts:
        conn.close()
        return

    # Stage 1: Batch triage
    worth_analyzing: set[str] = set()
    for i in range(0, len(posts), TRIAGE_BATCH_SIZE):
        batch = posts[i : i + TRIAGE_BATCH_SIZE]
        print(f"Triaging batch {i // TRIAGE_BATCH_SIZE + 1} ({len(batch)} posts)...")
        winners = triage_batch(client, batch)
        worth_analyzing.update(winners)

        # Mark losers as not_relevant
        for post in batch:
            if post["id"] not in winners:
                mark_not_relevant(conn, post["id"])
        conn.commit()

    print(f"Triage complete: {len(worth_analyzing)} posts worth deep analysis.")

    # Stage 2: Deep analysis on winners only
    to_analyze = [p for p in posts if p["id"] in worth_analyzing]
    for i, post in enumerate(to_analyze, 1):
        print(f"[{i}/{len(to_analyze)}] Analyzing {post['id']}: {post['title'][:60]}...")
        result = analyze_post(client, post)
        if result:
            store_analysis(conn, post["id"], result)
            conn.commit()

    conn.close()
    print("Analysis complete.")


if __name__ == "__main__":
    analyze_all()
