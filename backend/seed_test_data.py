"""Seed the database with realistic test posts for development."""

import time
from database import get_connection, init_db

TEST_POSTS = [
    {
        "id": "t3_test001",
        "subreddit": "SaaS",
        "title": "I wish there was a simple tool to track churn reasons",
        "selftext": "We're a small SaaS (about 200 customers) and every time someone cancels we send a manual email asking why. I wish there was a simple tool that auto-surveys churned users and categorizes the reasons. We've tried Typeform but it's not integrated with our billing at all. I'd honestly pay $50/mo for something that just works.",
        "author": "saas_founder_22",
        "score": 87,
        "num_comments": 34,
        "url": "https://reddit.com/r/SaaS/comments/test001",
        "created_utc": int(time.time()) - 86400 * 2,
    },
    {
        "id": "t3_test002",
        "subreddit": "startups",
        "title": "Can't believe there's no good competitor analysis tool for bootstrappers",
        "selftext": "Every competitor analysis tool I find is either $500/mo enterprise garbage or some AI wrapper that gives useless summaries. I just want something that tracks competitor pricing pages, feature lists, and changelog updates. I'm currently using a spreadsheet and checking manually every week. It's painful.",
        "author": "bootstrapper_mike",
        "score": 142,
        "num_comments": 56,
        "url": "https://reddit.com/r/startups/comments/test002",
        "created_utc": int(time.time()) - 86400 * 3,
    },
    {
        "id": "t3_test003",
        "subreddit": "sales",
        "title": "Switched from Salesforce to HubSpot and honestly both suck for small teams",
        "selftext": "We're a 5-person sales team. Salesforce was way too complex and expensive. HubSpot is cheaper but the free tier is so limited it's basically useless. We just need deal tracking, email sequences, and basic reporting. Why is this so hard? I'd pay for something simple that doesn't try to be everything.",
        "author": "sales_rep_jane",
        "score": 203,
        "num_comments": 89,
        "url": "https://reddit.com/r/sales/comments/test003",
        "created_utc": int(time.time()) - 86400 * 1,
    },
    {
        "id": "t3_test004",
        "subreddit": "smallbusiness",
        "title": "My janky solution for scheduling employees across multiple locations",
        "selftext": "I run 3 coffee shops and scheduling is a nightmare. I've cobbled together Google Sheets + Google Calendar + WhatsApp group messages. When someone calls in sick I have to manually text everyone. Tried When I Work but it's $4/employee/mo which adds up fast with 25 part-timers. Someone should build a simple free/cheap scheduler for small multi-location businesses.",
        "author": "coffee_shop_owner",
        "score": 67,
        "num_comments": 41,
        "url": "https://reddit.com/r/smallbusiness/comments/test004",
        "created_utc": int(time.time()) - 86400 * 5,
    },
    {
        "id": "t3_test005",
        "subreddit": "selfhosted",
        "title": "Looking for something like Notion but self-hosted and not electron garbage",
        "selftext": "I love Notion's flexibility but I hate that it's cloud-only, slow, and an Electron app. I've tried AppFlowy and it's promising but buggy. Obsidian is great for notes but doesn't do databases/tables well. Is there anything that combines wiki + database + kanban that I can self-host and that doesn't eat 2GB of RAM?",
        "author": "selfhost_enthusiast",
        "score": 312,
        "num_comments": 127,
        "url": "https://reddit.com/r/selfhosted/comments/test005",
        "created_utc": int(time.time()) - 86400 * 4,
    },
    {
        "id": "t3_test006",
        "subreddit": "daddit",
        "title": "I wish there was an app to coordinate parenting duties with my partner",
        "selftext": "We have a 2 year old and a newborn. My wife and I are constantly miscommunicating about who's doing pickup, who's making dinner, who handled the last diaper change at 3am. We tried shared calendars but they're not granular enough. We need something like a shared to-do list but specifically for parenting shifts and tasks. Anyone found anything good?",
        "author": "tired_dad_2024",
        "score": 156,
        "num_comments": 72,
        "url": "https://reddit.com/r/daddit/comments/test006",
        "created_utc": int(time.time()) - 86400 * 2,
    },
    {
        "id": "t3_test007",
        "subreddit": "running",
        "title": "Why isn't there a good app for finding running routes in new cities?",
        "selftext": "I travel for work a lot and every time I'm in a new city I spend 30 minutes on Google Maps trying to figure out a safe running route that's the right distance. Strava routes are hit or miss and often on busy roads. I just want to input my hotel address and desired distance and get a nice loop. Bonus if it avoids sketchy areas and prefers parks/trails.",
        "author": "road_warrior_runner",
        "score": 234,
        "num_comments": 93,
        "url": "https://reddit.com/r/running/comments/test007",
        "created_utc": int(time.time()) - 86400 * 1,
    },
    {
        "id": "t3_test008",
        "subreddit": "Entrepreneur",
        "title": "Take my money - I need a tool that monitors my competitors' job postings",
        "selftext": "Job postings reveal SO much about what a company is building next. If my competitor suddenly posts 5 ML engineer roles, that tells me something. I want a tool that tracks specific companies' job boards and alerts me when they post roles matching certain keywords. I'd easily pay $30/mo for this.",
        "author": "competitive_intel_guy",
        "score": 189,
        "num_comments": 45,
        "url": "https://reddit.com/r/Entrepreneur/comments/test008",
        "created_utc": int(time.time()) - 86400 * 3,
    },
    {
        "id": "t3_test009",
        "subreddit": "productivity",
        "title": "Does anyone have a good system for weekly reviews? Everything I've tried falls apart",
        "selftext": "I've tried Notion templates, Obsidian weekly reviews, even paper journals. The problem is none of them pull in data from my actual tools - what tasks did I complete in Todoist? How many hours did I track in Toggl? What meetings did I have? I end up spending 45 minutes just gathering info before I can even reflect. Someone should build an automated weekly review aggregator.",
        "author": "productivity_nerd",
        "score": 98,
        "num_comments": 37,
        "url": "https://reddit.com/r/productivity/comments/test009",
        "created_utc": int(time.time()) - 86400 * 6,
    },
    {
        "id": "t3_test010",
        "subreddit": "HybridAthletes",
        "title": "I'm sick of trying to balance running and lifting with no good planning tool",
        "selftext": "Every training app is either running-focused or lifting-focused. If you do both, you're on your own. I need something that understands fatigue across both modalities - like don't schedule heavy squats the day after a long run. I'm currently using two separate apps (Garmin for running, Strong for lifting) and a spreadsheet to plan the week. It's a mess.",
        "author": "hybrid_athlete_problems",
        "score": 76,
        "num_comments": 28,
        "url": "https://reddit.com/r/HybridAthletes/comments/test010",
        "created_utc": int(time.time()) - 86400 * 2,
    },
    {
        "id": "t3_test011",
        "subreddit": "salesforce",
        "title": "Workaround for Salesforce's terrible reporting on custom objects",
        "selftext": "Sharing my workaround since I know others struggle with this. SF reporting on custom objects is painfully limited. I ended up writing a Python script that pulls data via the API and generates reports in Google Sheets. It's ugly but it works. Would love if someone built a proper lightweight reporting layer for SF that doesn't cost $10k/year like Tableau.",
        "author": "sf_admin_pain",
        "score": 45,
        "num_comments": 19,
        "url": "https://reddit.com/r/salesforce/comments/test011",
        "created_utc": int(time.time()) - 86400 * 7,
    },
    {
        "id": "t3_test012",
        "subreddit": "predaddit",
        "title": "Best app for tracking pregnancy milestones and appointments?",
        "selftext": "Wife is 12 weeks pregnant and we want to track everything - appointments, symptoms, what to expect each week, etc. We downloaded like 5 apps and they're all either ad-infested garbage or pink-themed 'for mom only' stuff. Any good ones that are dad-friendly and not trying to sell me premium subscriptions every 5 seconds?",
        "author": "soon_to_be_dad",
        "score": 34,
        "num_comments": 22,
        "url": "https://reddit.com/r/predaddit/comments/test012",
        "created_utc": int(time.time()) - 86400 * 4,
    },
]


def seed():
    init_db()
    conn = get_connection()
    now = int(time.time())

    inserted = 0
    for post in TEST_POSTS:
        existing = conn.execute("SELECT id FROM posts WHERE id = ?", (post["id"],)).fetchone()
        if existing:
            continue

        conn.execute(
            """INSERT INTO posts (id, subreddit, title, selftext, author, score,
               num_comments, url, created_utc, collected_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                post["id"], post["subreddit"], post["title"], post["selftext"],
                post["author"], post["score"], post["num_comments"], post["url"],
                post["created_utc"], now,
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Seeded {inserted} test posts.")


if __name__ == "__main__":
    seed()
