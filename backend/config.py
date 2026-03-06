import os
from dotenv import load_dotenv

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "signal-scanner/1.0")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

DB_PATH = os.path.join(os.path.dirname(__file__), "signal_scanner.db")

SUBREDDITS = [
    "SaaS", "startups", "Entrepreneur",
    "sales", "salesforce",
    "smallbusiness",
    "productivity", "selfhosted",
    "daddit", "predaddit",
    "running", "HybridAthletes", "trailrunning",
]

SEARCH_SIGNALS = [
    # "I wish" signals
    "I wish there was",
    "why isn't there",
    "someone should build",
    "does anyone know a tool",
    # Frustration signals
    "I'm sick of",
    "switched from",
    "is broken",
    "can't believe there's no",
    # Workaround signals
    "my current hack",
    "I use a spreadsheet",
    "cobbled together",
    "janky solution",
    "workaround",
    # Buying signals
    "willing to pay",
    "I'd pay for",
    "take my money",
    "shut up and take my money",
    # Comparison signals
    "alternative to",
    "looking for something like",
    "vs",
]
