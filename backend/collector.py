"""Reddit collection script — fetches posts matching search signals via PRAW."""

import time
import praw
from database import get_connection, init_db
from config import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    SUBREDDITS,
    SEARCH_SIGNALS,
)


def create_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )


def get_existing_post_ids(conn) -> set[str]:
    rows = conn.execute("SELECT id FROM posts").fetchall()
    return {row["id"] for row in rows}


def collect_posts(limit_per_query: int = 50):
    """Run a full collection pass across all subreddits and search signals."""
    init_db()
    reddit = create_reddit_client()
    conn = get_connection()
    existing_ids = get_existing_post_ids(conn)

    new_count = 0
    skipped = 0
    now = int(time.time())

    total_queries = len(SUBREDDITS) * len(SEARCH_SIGNALS)
    current_query = 0

    for sub_name in SUBREDDITS:
        subreddit = reddit.subreddit(sub_name)

        for signal in SEARCH_SIGNALS:
            current_query += 1
            print(f"[{current_query}/{total_queries}] r/{sub_name}: \"{signal}\"")

            try:
                results = subreddit.search(signal, sort="new", limit=limit_per_query)

                for post in results:
                    post_id = f"t3_{post.id}"

                    if post_id in existing_ids:
                        skipped += 1
                        continue

                    conn.execute(
                        """INSERT INTO posts (id, subreddit, title, selftext, author, score,
                           num_comments, url, created_utc, collected_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            post_id,
                            post.subreddit.display_name,
                            post.title,
                            post.selftext or "",
                            str(post.author) if post.author else "[deleted]",
                            post.score,
                            post.num_comments,
                            f"https://reddit.com{post.permalink}",
                            int(post.created_utc),
                            now,
                        ),
                    )
                    existing_ids.add(post_id)
                    new_count += 1

                conn.commit()

            except Exception as e:
                print(f"  Error: {e}")
                continue

    conn.close()
    print(f"\nDone. New posts: {new_count}, Skipped (dupes): {skipped}")
    return new_count


if __name__ == "__main__":
    collect_posts()
