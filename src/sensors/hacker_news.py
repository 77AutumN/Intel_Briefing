"""
Hacker News Sensor - Fetches top stories from Hacker News.
Uses the official Firebase API (no auth required).
"""
import sys
import json
from dataclasses import dataclass
from typing import List, Optional

try:
    import httpx
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

@dataclass
class HNStory:
    """A Hacker News story."""
    id: int
    title: str
    url: Optional[str]
    score: int
    by: str
    descendants: int  # comment count
    
    @property
    def hn_url(self) -> str:
        return f"https://news.ycombinator.com/item?id={self.id}"

def fetch_top_stories(limit: int = 10) -> List[HNStory]:
    """Fetch top stories from Hacker News."""
    print(f"  → Fetching top {limit} stories from Hacker News...")
    
    # Get top story IDs
    resp = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=15)
    story_ids = resp.json()[:limit]
    
    stories = []
    for sid in story_ids:
        item_resp = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=10)
        item = item_resp.json()
        if item and item.get("type") == "story":
            stories.append(HNStory(
                id=item["id"],
                title=item.get("title", ""),
                url=item.get("url"),
                score=item.get("score", 0),
                by=item.get("by", "unknown"),
                descendants=item.get("descendants", 0)
            ))
    
    return stories

def print_stories(stories: List[HNStory]):
    """Print stories in a readable format."""
    print(f"\n{'='*60}")
    print(f"  📰 Hacker News Top Stories")
    print(f"{'='*60}\n")
    
    for i, s in enumerate(stories, 1):
        print(f"{i}. {s.title}")
        print(f"   ⬆️ {s.score} points | 💬 {s.descendants} comments | by {s.by}")
        print(f"   🔗 {s.url or s.hn_url}")
        print()

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    stories = fetch_top_stories(limit)
    if stories:
        print_stories(stories)
    else:
        print("No stories found.")
