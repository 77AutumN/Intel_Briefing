"""
RSS Sensor for HN Popular Blogs - Fetches and summarizes latest posts.
Uses OPML file for blog list, feedparser for RSS, and Grok for AI summaries.
"""

import os
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional
import xml.etree.ElementTree as ET

# Auto-install dependencies
try:
    import feedparser
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "feedparser", "-q"])
    import feedparser

try:
    import httpx
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

# Add local src for Grok sensor
LOCAL_SRC_PATH = os.path.join(os.path.dirname(__file__), '..', 'src')
if LOCAL_SRC_PATH not in sys.path:
    sys.path.insert(0, LOCAL_SRC_PATH)

try:
    from sensors.x_grok_sensor import fetch_grok_intel
    GROK_AVAILABLE = True
except ImportError:
    GROK_AVAILABLE = False
    print("[WARN] Grok sensor not available, summaries will be skipped.")


@dataclass
class BlogPost:
    """A single blog post from RSS feed."""
    title: str
    url: str
    blog_name: str
    published: str
    summary: Optional[str] = None
    ai_summary: Optional[str] = None


@dataclass  
class BlogFeed:
    """A blog feed parsed from OPML."""
    name: str
    rss_url: str
    html_url: str


def parse_opml(opml_path: str) -> List[BlogFeed]:
    """Parse OPML file and extract blog feeds."""
    feeds = []
    tree = ET.parse(opml_path)
    root = tree.getroot()
    
    for outline in root.findall(".//outline[@type='rss']"):
        name = outline.get('text', 'Unknown')
        rss_url = outline.get('xmlUrl', '')
        html_url = outline.get('htmlUrl', '')
        
        if rss_url:
            feeds.append(BlogFeed(name=name, rss_url=rss_url, html_url=html_url))
    
    return feeds


def fetch_recent_posts(feeds: List[BlogFeed], days: int = 3, max_per_blog: int = 2) -> List[BlogPost]:
    """Fetch recent posts from all feeds."""
    posts = []
    cutoff = datetime.now() - timedelta(days=days)
    
    for feed in feeds:
        try:
            print(f"  → Fetching {feed.name}...")
            parsed = feedparser.parse(feed.rss_url)
            
            if parsed.bozo and not parsed.entries:
                print(f"    ⚠️ Failed to parse {feed.name}")
                continue
            
            count = 0
            for entry in parsed.entries:
                if count >= max_per_blog:
                    break
                
                # Parse date
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6])
                    except:
                        pass
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    try:
                        published = datetime(*entry.updated_parsed[:6])
                    except:
                        pass
                
                # Skip old posts
                if published and published < cutoff:
                    continue
                
                # Extract summary
                summary = None
                if hasattr(entry, 'summary'):
                    summary = entry.summary[:500] if len(entry.summary) > 500 else entry.summary
                
                posts.append(BlogPost(
                    title=entry.get('title', 'No Title'),
                    url=entry.get('link', ''),
                    blog_name=feed.name,
                    published=published.strftime("%Y-%m-%d") if published else "Unknown",
                    summary=summary
                ))
                count += 1
                
        except Exception as e:
            print(f"    ❌ Error fetching {feed.name}: {e}")
    
    return posts


def summarize_posts_with_grok(posts: List[BlogPost], max_posts: int = 10) -> str:
    """Use Grok to generate a digest summary of the posts."""
    if not GROK_AVAILABLE:
        return None
    
    if not posts:
        return None
    
    # Prepare post list for Grok
    posts_text = "\n".join([
        f"{i+1}. [{post.blog_name}] {post.title}\n   URL: {post.url}\n   Published: {post.published}"
        for i, post in enumerate(posts[:max_posts])
    ])
    
    prompt = f"""你是一个技术情报分析师。以下是过去几天来自 Hacker News 最热门个人博客的最新文章列表：

{posts_text}

请用简体中文生成一份简洁的情报摘要：
1. 总结这些文章的主要主题和趋势（1-2 句话）
2. 挑出 3-5 篇最值得阅读的文章，说明为什么值得读
3. 如果发现任何有商业价值或可以变现的技术趋势，请特别指出

保持简洁，不超过 300 字。"""

    try:
        summary = fetch_grok_intel("HN Blogs Digest", override_prompt=prompt)
        return summary if summary and "Error" not in summary else None
    except Exception as e:
        print(f"  ⚠️ Grok summarization failed: {e}")
        return None


def generate_report(posts: List[BlogPost], ai_summary: Optional[str], date_str: str) -> str:
    """Generate markdown report."""
    lines = [
        f"# 📰 HN 博客精选 (Blog Digest)",
        f"**日期:** {date_str}",
        f"**来源:** HN Popularity Contest 2025 (Top 30 Blogs)",
        f"**文章数:** {len(posts)} 篇",
        "",
        "---",
        ""
    ]
    
    # AI Summary section
    if ai_summary:
        lines.append("## 🧠 AI 情报摘要")
        lines.append("")
        lines.append(ai_summary)
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Posts list
    lines.append("## 📚 最新文章")
    lines.append("")
    
    if posts:
        for i, post in enumerate(posts, 1):
            lines.append(f"### {i}. [{post.title}]({post.url})")
            lines.append(f"📍 {post.blog_name} | 📅 {post.published}")
            if post.summary:
                # Clean HTML from summary
                clean_summary = post.summary.replace('<p>', '').replace('</p>', '').strip()
                if len(clean_summary) > 200:
                    clean_summary = clean_summary[:200] + "..."
                lines.append(f"> {clean_summary}")
            lines.append("")
    else:
        lines.append("*过去 3 天没有新文章*")
        lines.append("")
    
    lines.append("---")
    lines.append("*报告由 RSS Sensor 自动生成*")
    
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="RSS Sensor for HN Popular Blogs")
    parser.add_argument("--days", type=int, default=3, help="Fetch posts from last N days")
    parser.add_argument("--no-summary", action="store_true", help="Skip AI summary")
    parser.add_argument("--output", type=str, help="Custom output path")
    args = parser.parse_args()
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n{'='*50}")
    print(f"  RSS Sensor - HN Popular Blogs")
    print(f"  Date: {date_str} | Days: {args.days}")
    print(f"{'='*50}\n")
    
    # Find OPML file
    script_dir = os.path.dirname(__file__)
    opml_path = os.path.join(script_dir, "hn_popular_blogs_2025.opml")
    
    if not os.path.exists(opml_path):
        print(f"[ERROR] OPML file not found: {opml_path}")
        return
    
    # Parse feeds
    print("[*] Parsing OPML file...")
    feeds = parse_opml(opml_path)
    print(f"  Found {len(feeds)} blogs")
    
    # Fetch posts
    print(f"\n[*] Fetching posts from last {args.days} days...")
    posts = fetch_recent_posts(feeds, days=args.days)
    print(f"  Found {len(posts)} recent posts")
    
    # AI Summary
    ai_summary = None
    if not args.no_summary and posts:
        print("\n[*] Generating AI summary with Grok...")
        ai_summary = summarize_posts_with_grok(posts)
        if ai_summary:
            print("  ✅ AI summary generated")
        else:
            print("  ⚠️ AI summary skipped")
    
    # Generate report
    report = generate_report(posts, ai_summary, date_str)
    
    # Save
    if args.output:
        output_path = args.output
    else:
        reports_dir = os.path.join(script_dir, "..", "reports", "daily_briefings")
        os.makedirs(reports_dir, exist_ok=True)
        output_path = os.path.join(reports_dir, f"Blog_Digest_{date_str}.md")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n[SUCCESS] Report saved to: {output_path}")
    print(f"\n--- Preview ---\n")
    for line in report.split("\n")[:30]:
        print(line)


if __name__ == "__main__":
    main()
