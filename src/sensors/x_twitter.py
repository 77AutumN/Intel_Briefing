"""
X (Twitter) Sensor - Fetches trending AI/Tech discussions.
Uses browser-based scraping since official API requires paid access.
IMPORTANT: This sensor requires the Antigravity browser subagent to run.
           It cannot be executed as a standalone Python script.
"""
import sys
import os
import json
from dataclasses import dataclass, asdict
from typing import List
from datetime import datetime

@dataclass
class XPost:
    """A post from X (Twitter)."""
    author: str
    handle: str
    content: str
    timestamp: str
    likes: int
    retweets: int
    url: str

# This sensor is designed to be triggered by the Agent, not run standalone.
# The Agent will use browser_subagent to scrape X and save results here.

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "x_cache.json")

def load_cached_posts() -> List[XPost]:
    """Load cached X posts from file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [XPost(**p) for p in data.get("posts", [])]
    return []

def save_posts_to_cache(posts: List[dict]):
    """Save scraped posts to cache file."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "scraped_at": datetime.now().isoformat(),
            "posts": posts
        }, f, ensure_ascii=False, indent=2)

def print_posts(posts: List[XPost]):
    """Print posts in a readable format."""
    print(f"\n{'='*60}")
    print(f"  🐦 X (Twitter) AI/Tech Discussions")
    print(f"{'='*60}\n")
    
    for i, p in enumerate(posts, 1):
        print(f"{i}. @{p.handle} ({p.author})")
        print(f"   {p.content[:200]}{'...' if len(p.content) > 200 else ''}")
        print(f"   ❤️ {p.likes} | 🔁 {p.retweets} | 📅 {p.timestamp}")
        print(f"   🔗 {p.url}")
        print()

# Agent-callable functions
def get_scrape_instructions(query: str = "AI agent automation") -> str:
    """Return instructions for the Agent to scrape X."""
    return f"""
    1. Navigate to: https://x.com/search?q={query.replace(' ', '%20')}&f=live
    2. Wait 5 seconds for timeline load.
    3. Open Console (F12) and run this extraction logic:
    
    ```javascript
    var posts = [];
    document.querySelectorAll('article[data-testid="tweet"]').forEach(art => {{
        try {{
            var txt = art.querySelector('div[data-testid="tweetText"]')?.innerText || "";
            var user = art.querySelector('div[data-testid="User-Name"]')?.innerText.split('\\n')[0] || "Unknown";
            var handle = art.querySelector('div[data-testid="User-Name"] a')?.getAttribute('href')?.replace('/', '') || "Unknown";
            var time = art.querySelector('time')?.getAttribute('datetime');
            var likes = art.querySelector('div[data-testid="like"]')?.getAttribute('aria-label')?.split(' ')[0] || "0";
            var url = "https://x.com" + art.querySelector('a[href*="/status/"]')?.getAttribute('href');
            
            posts.push({{
                author: user, handle: handle, content: txt, 
                timestamp: time, likes: String(likes), retweets: "0", url: url
            }});
        }} catch(e) {{}}
    }});
    console.log(JSON.stringify(posts, null, 2));
    ```
    
    4. Save the JSON array to: {CACHE_FILE}
    """

if __name__ == "__main__":
    # Try to load cached data
    posts = load_cached_posts()
    if posts:
        print(f"(Showing cached data from {CACHE_FILE})")
        print_posts(posts)
    else:
        print("No cached X data found.")
        print("This sensor requires the Antigravity Agent to run with browser access.")
        print(f"\nTo fetch fresh data, ask the Agent to scrape X with query parameters.")
        print(f"Instructions: {get_scrape_instructions()}")
