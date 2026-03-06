"""Claude analysis pipeline — analyzes unprocessed posts for pain points."""

import json
import time
import anthropic
from database import get_connection, init_db
from config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """You are analyzing a Reddit post to identify whether it contains a real pain point that could be solved with a software product.

Respond ONLY with valid JSON, no markdown formatting."""

USER_PROMPT_TEMPLATE = """Post title: {title}
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


def analyze_post(client: anthropic.Anthropic, post: dict) -> dict | None:
    """Send a single post to Claude for analysis. Returns parsed JSON or None."""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        title=post["title"],
        selftext=post["selftext"][:2000],  # truncate long posts
        subreddit=post["subreddit"],
    )

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text = response.content[0].text.strip()
        # Strip markdown code fences if present
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

    # Handle "not_relevant" short-form response
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


def analyze_all():
    """Process all unanalyzed posts through Claude."""
    init_db()
    conn = get_connection()
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    posts = get_unanalyzed_posts(conn)
    print(f"Found {len(posts)} unanalyzed posts.")

    for i, post in enumerate(posts, 1):
        print(f"[{i}/{len(posts)}] Analyzing {post['id']}: {post['title'][:60]}...")

        result = analyze_post(client, post)
        if result:
            store_analysis(conn, post["id"], result)
            conn.commit()

    conn.close()
    print("Analysis complete.")


if __name__ == "__main__":
    analyze_all()
