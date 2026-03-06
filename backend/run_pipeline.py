"""End-to-end pipeline: collect from Reddit, then analyze with Claude."""

from collector import collect_posts
from analyzer import analyze_all


def main():
    print("=" * 50)
    print("STEP 1: Collecting posts from Reddit")
    print("=" * 50)
    new_count = collect_posts()

    if new_count > 0:
        print()
        print("=" * 50)
        print("STEP 2: Analyzing posts with Claude")
        print("=" * 50)
        analyze_all()
    else:
        print("\nNo new posts to analyze.")

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
