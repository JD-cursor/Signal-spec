# Signal Scanner — Project Spec

Personal tool for discovering real-world pain points by scanning Reddit for complaints, workarounds, and unmet needs. Collects posts, analyzes them with Claude, scores and clusters them, and surfaces the best signals in a clean dashboard UI.

---

## Stack

- **Backend:** Python + FastAPI
- **Database:** SQLite (single local file)
- **Reddit:** PRAW (Python Reddit API Wrapper)
- **Analysis:** Anthropic Python SDK (Claude Haiku for cost-efficiency)
- **Frontend:** React + Vite
- **UI:** shadcn/ui + Tailwind CSS
- **Charts:** Recharts
- **Kanban drag-and-drop:** dnd-kit

Everything runs locally. No cloud, no Docker, no deployment.

---

## Architecture Overview

```
[Cron / Manual Trigger]
        │
        ▼
[Reddit Collector]  ──►  PRAW fetches posts via search + listing endpoints
        │
        ▼
[SQLite DB]  ──►  Raw posts stored with metadata
        │
        ▼
[Claude Analyzer]  ──►  Scores, categorizes, and summarizes each post
        │
        ▼
[SQLite DB]  ──►  Analysis results stored alongside raw data
        │
        ▼
[FastAPI Backend]  ──►  Serves data to frontend via REST endpoints
        │
        ▼
[React Frontend]  ──►  Dashboard / Feed / Kanban views
```

---

## SQLite Schema

### `posts`
| Column | Type | Description |
|---|---|---|
| id | TEXT PRIMARY KEY | Reddit post ID (e.g. `t3_abc123`) |
| subreddit | TEXT | Source subreddit |
| title | TEXT | Post title |
| selftext | TEXT | Post body (if text post) |
| author | TEXT | Reddit username |
| score | INTEGER | Reddit upvotes |
| num_comments | INTEGER | Comment count |
| url | TEXT | Reddit permalink |
| created_utc | INTEGER | Unix timestamp of post creation |
| collected_at | INTEGER | Unix timestamp of when we scraped it |

### `analysis`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PRIMARY KEY AUTOINCREMENT | |
| post_id | TEXT REFERENCES posts(id) | Link to raw post |
| summary | TEXT | Claude's plain-language summary of the pain point |
| category | TEXT | Category tag (e.g. "tooling_gap", "workflow_friction", "missing_product") |
| severity | TEXT | "low" / "medium" / "high" — how painful is this? |
| has_existing_solution | BOOLEAN | Does Claude think a solution already exists? |
| existing_solution_notes | TEXT | If yes, what is it and why isn't it working? |
| willingness_to_pay | TEXT | "unlikely" / "possible" / "likely" — based on language cues |
| relevance_tags | TEXT | JSON array of tags like ["sales", "productivity", "parenting"] |
| analyzed_at | INTEGER | Unix timestamp |

### `favorites`
| Column | Type | Description |
|---|---|---|
| id | INTEGER PRIMARY KEY AUTOINCREMENT | |
| post_id | TEXT REFERENCES posts(id) | |
| kanban_status | TEXT | "new" / "researching" / "has_potential" / "parked" |
| notes | TEXT | Your personal notes |
| favorited_at | INTEGER | Unix timestamp |
| updated_at | INTEGER | Unix timestamp |

---

## Reddit Collection

### Target Subreddits (starting set)

**Builder/SaaS:** r/SaaS, r/startups, r/Entrepreneur
**Sales/Enterprise:** r/sales, r/salesforce
**Small business:** r/smallbusiness
**Productivity/Self-hosted:** r/productivity, r/selfhosted
**Parenting:** r/daddit, r/predaddit
**Fitness:** r/running, r/HybridAthletes, r/trailrunning

### Search Signals

These keyword patterns are used as search queries against each subreddit:

**"I wish" signals:**
- "I wish there was"
- "why isn't there"
- "someone should build"
- "does anyone know a tool"

**Frustration signals:**
- "I'm sick of"
- "switched from"
- "is broken"
- "can't believe there's no"

**Workaround signals:**
- "my current hack"
- "I use a spreadsheet"
- "cobbled together"
- "janky solution"
- "workaround"

**Buying signals:**
- "willing to pay"
- "I'd pay for"
- "take my money"
- "shut up and take my money"

**Comparison signals:**
- "alternative to"
- "looking for something like"
- "vs"

### Collection Logic

- Run as a batch job (manual trigger or cron, 1-2x per week)
- For each subreddit, run each search signal as a query via PRAW's `subreddit.search()`
- Deduplicate against existing post IDs in the DB
- Store raw post data immediately
- Queue new posts for Claude analysis
- Target: stay under 10,000 API requests/month (free tier)

### API Budget Estimate

- 13 subreddits × ~20 search queries each = ~260 API calls per scan
- Each call returns up to 100 posts
- Running 2x/week = ~2,080 calls/month
- Leaves plenty of headroom for listing endpoints, error retries, etc.

---

## Claude Analysis Pipeline

For each new post, send to Claude Haiku with a structured prompt:

```
You are analyzing a Reddit post to identify whether it contains a real pain point
that could be solved with a software product.

Post title: {title}
Post body: {selftext}
Subreddit: r/{subreddit}

Respond in JSON:
{
  "summary": "One-sentence plain-language description of the pain point",
  "category": "tooling_gap | workflow_friction | missing_product | price_complaint | integration_gap | other",
  "severity": "low | medium | high",
  "has_existing_solution": true/false,
  "existing_solution_notes": "If yes, what exists and why isn't it enough",
  "willingness_to_pay": "unlikely | possible | likely",
  "relevance_tags": ["tag1", "tag2"]
}

If the post doesn't contain a meaningful pain point, return:
{
  "summary": null,
  "category": "not_relevant"
}
```

Posts where `category == "not_relevant"` are stored but hidden from the feed by default.

### Clustering (future enhancement)

Once enough data is collected, run a periodic job that asks Claude to cluster similar pain points together. This surfaces patterns like "12 different people across 3 subreddits are complaining about the same thing."

---

## Frontend — Three Views

### Design Direction

Inspired by soft, modern dashboard aesthetic:
- Light background with generous white space
- Rounded cards with subtle shadows (no hard borders)
- Soft gradient accents (peach-to-blue, pink-to-cyan)
- Clean typography hierarchy
- Muted color palette with selective bold accents for key metrics
- Glassmorphic touches on card surfaces

### View 1: Dashboard (home)

Top section:
- Welcome header with last scan timestamp
- Key stats in gradient accent cards: total pain points found, new since last scan, top category this week
- Small stat for API budget remaining (requests used / 10,000)

Middle section:
- Line chart showing pain points collected over time (by week)
- Horizontal bar chart showing top categories

Bottom section:
- "Top 10 this week" — ranked list of highest-severity, highest-willingness-to-pay posts

### View 2: Feed (discovery)

Scrollable card layout (single column, centered, max-width ~720px for readability).

Each card shows:
- Pain point summary (Claude-generated, prominent)
- Source subreddit badge + Reddit score
- Category tag (color-coded)
- Severity indicator (subtle dot or bar)
- Willingness-to-pay indicator
- "Has existing solution" flag if true
- Star/favorite button (heart icon) → sends to kanban
- Click to expand → shows original post title + body + link to Reddit

Filters (top bar):
- By subreddit
- By category
- By severity
- By date range
- Search within results

### View 3: Kanban (working board)

Four columns: **New → Researching → Has Potential → Parked**

Each card shows the pain point summary + subreddit source + your notes.
- Drag and drop between columns (dnd-kit)
- Click card to expand and add/edit notes
- Option to unfavorite (removes from kanban, back to feed only)

### Navigation

Simple sidebar or top nav with three items: Dashboard, Feed, Board.

---

## FastAPI Endpoints

```
GET  /api/stats              — Dashboard summary stats
GET  /api/trends             — Time-series data for charts
GET  /api/posts              — Feed data with filtering/pagination
GET  /api/posts/{id}         — Single post with full analysis
POST /api/posts/{id}/favorite    — Add to kanban
DELETE /api/posts/{id}/favorite  — Remove from kanban
PATCH /api/favorites/{id}        — Update kanban status or notes
GET  /api/favorites              — All kanban items grouped by status
POST /api/collect                — Trigger a new Reddit scan
GET  /api/budget                 — API usage stats
```

---

## Build Order

### Session 1: Data Pipeline
1. Set up Python project structure
2. Configure PRAW with Reddit OAuth credentials
3. Create SQLite schema
4. Build the collection script (iterate subreddits × search signals, dedupe, store)
5. Build the Claude analysis pipeline (process new posts, store results)
6. Test end-to-end: trigger collection → see analyzed results in DB

### Session 2: Backend API + Frontend Shell
1. Set up FastAPI with endpoints above
2. Scaffold React + Vite project with shadcn/ui + Tailwind
3. Build Dashboard view (stats + charts)
4. Build Feed view (cards + filtering)
5. Wire up to backend

### Session 3: Kanban + Polish
1. Build Kanban view with dnd-kit
2. Implement favorite/unfavorite flow
3. Add notes editing on kanban cards
4. Polish UI — gradients, shadows, typography, responsive behavior
5. Add the manual "trigger scan" button

### Future Enhancements (not in v1)
- Pain point clustering across posts
- Automated weekly digest (Claude summary of top findings)
- HackerNews and Indie Hackers as additional sources
- Browser extension to favorite posts directly from Reddit
- Export kanban items to Notion or markdown
