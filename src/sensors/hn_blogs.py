#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HN Top Blogs Sensor
从 OPML 列表抓取 HN 社区精选技术博客 RSS

数据源: https://gist.github.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b
协议: RSS/Atom (公开、免费、合法)
"""

import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import ssl

# OPML Source
OPML_URL = "https://gist.githubusercontent.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b/raw/hn-popular-blogs-2025.opml"

# Fallback feeds if OPML fails
FALLBACK_FEEDS = [
    {"title": "Simon Willison", "rss": "https://simonwillison.net/atom/everything/", "html": "https://simonwillison.net"},
    {"title": "Mitchell Hashimoto", "rss": "https://mitchellh.com/feed.xml", "html": "https://mitchellh.com"},
    {"title": "antirez", "rss": "http://antirez.com/rss", "html": "http://antirez.com"},
    {"title": "Paul Graham", "rss": "http://www.aaronsw.com/2002/feeds/pgessays.rss", "html": "http://paulgraham.com"},
    {"title": "Pluralistic", "rss": "https://pluralistic.net/feed/", "html": "https://pluralistic.net"},
]

# Config
FETCH_TIMEOUT = 10
MAX_BLOGS_TO_FETCH = 20  # Only fetch from top N blogs for speed
MAX_ARTICLES_PER_BLOG = 2


@dataclass
class BlogArticle:
    """Represents a blog article from HN Top Blogs."""
    title: str
    url: str
    source: str
    pub_date: str = ""
    content: str = ""  # Article description/summary from RSS


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities from text."""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Decode common HTML entities
    clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    clean = clean.replace('&quot;', '"').replace('&#39;', "'")
    clean = clean.replace('&nbsp;', ' ')
    # Clean up whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def _create_ssl_context():
    """Create SSL context that ignores certificate errors (for some blogs)."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _fetch_url(url: str, timeout: int = FETCH_TIMEOUT) -> Optional[str]:
    """Fetch URL content with timeout and error handling."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Intel-Briefing-RSS-Reader/1.0"
        })
        with urllib.request.urlopen(req, timeout=timeout, context=_create_ssl_context()) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"    [WARN] Failed to fetch {url[:50]}...: {e}")
        return None


def parse_opml(opml_content: str) -> List[dict]:
    """Parse OPML content to extract blog feeds."""
    blogs = []
    # Match <outline type="rss" ... />
    pattern = r'<outline[^>]+type="rss"[^>]*>'
    for match in re.finditer(pattern, opml_content):
        outline = match.group(0)
        text_match = re.search(r'text="([^"]+)"', outline)
        xml_url_match = re.search(r'xmlUrl="([^"]+)"', outline)
        html_url_match = re.search(r'htmlUrl="([^"]+)"', outline)
        
        if text_match and xml_url_match:
            blogs.append({
                "title": text_match.group(1),
                "rss": xml_url_match.group(1),
                "html": html_url_match.group(1) if html_url_match else ""
            })
    return blogs


def parse_rss_feed(feed_content: str, source_title: str) -> List[BlogArticle]:
    """Parse RSS/Atom feed content to extract articles."""
    articles = []
    try:
        root = ET.fromstring(feed_content)
        
        # Handle Atom feeds
        if 'atom' in root.tag.lower() or root.tag == '{http://www.w3.org/2005/Atom}feed':
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('.//atom:entry', ns) or root.findall('.//entry')
            for entry in entries[:MAX_ARTICLES_PER_BLOG]:
                title = entry.find('atom:title', ns) or entry.find('title')
                link = entry.find('atom:link[@rel="alternate"]', ns) or entry.find('atom:link', ns) or entry.find('link')
                published = entry.find('atom:published', ns) or entry.find('atom:updated', ns) or entry.find('published') or entry.find('updated')
                # Extract content/summary for Atom feeds
                summary = entry.find('atom:summary', ns) or entry.find('atom:content', ns) or entry.find('summary') or entry.find('content')
                
                title_text = title.text if title is not None and title.text else "Untitled"
                link_href = link.get('href', '') if link is not None else ""
                pub_text = published.text[:10] if published is not None and published.text else ""
                content_text = _strip_html(summary.text) if summary is not None and summary.text else ""
                
                if title_text and link_href:
                    articles.append(BlogArticle(
                        title=title_text,
                        url=link_href,
                        source=source_title,
                        pub_date=pub_text,
                        content=content_text
                    ))
        
        # Handle RSS 2.0 feeds
        else:
            items = root.findall('.//item')
            for item in items[:MAX_ARTICLES_PER_BLOG]:
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                # Extract description for RSS 2.0 feeds
                description = item.find('description')
                
                title_text = title.text if title is not None and title.text else "Untitled"
                link_text = link.text if link is not None and link.text else ""
                pub_text = pub_date.text[:16] if pub_date is not None and pub_date.text else ""
                content_text = _strip_html(description.text) if description is not None and description.text else ""
                
                if title_text and link_text:
                    articles.append(BlogArticle(
                        title=title_text,
                        url=link_text,
                        source=source_title,
                        pub_date=pub_text,
                        content=content_text
                    ))
    except ET.ParseError as e:
        print(f"    [WARN] XML parse error for {source_title}: {e}")
    except Exception as e:
        print(f"    [WARN] Error parsing feed from {source_title}: {e}")
    
    return articles


def fetch_hn_blogs(limit: int = 5) -> List[BlogArticle]:
    """
    Fetch latest articles from HN Top Blogs OPML.
    
    Args:
        limit: Maximum number of articles to return
        
    Returns:
        List of BlogArticle objects, sorted by recency
    """
    print(f"[*] Fetching HN Top Blogs (OPML)...")
    
    # 1. Fetch OPML
    opml_content = _fetch_url(OPML_URL)
    if opml_content:
        blogs = parse_opml(opml_content)
        print(f"    Found {len(blogs)} blogs in OPML")
    else:
        print("    [WARN] OPML fetch failed, using fallback feeds")
        blogs = FALLBACK_FEEDS
    
    if not blogs:
        print("    [ERROR] No blogs available")
        return []
    
    # 2. Fetch RSS from top N blogs
    all_articles = []
    blogs_to_fetch = blogs[:MAX_BLOGS_TO_FETCH]
    
    for i, blog in enumerate(blogs_to_fetch):
        feed_content = _fetch_url(blog["rss"])
        if feed_content:
            articles = parse_rss_feed(feed_content, blog["title"])
            all_articles.extend(articles)
            if articles:
                print(f"    [{i+1}/{len(blogs_to_fetch)}] {blog['title']}: {len(articles)} articles")
        else:
            print(f"    [{i+1}/{len(blogs_to_fetch)}] {blog['title']}: failed")
    
    # 3. Sort by date and return top N
    # Note: Date parsing is best-effort
    def parse_date(article):
        try:
            if article.pub_date:
                return datetime.fromisoformat(article.pub_date.replace('Z', '+00:00'))
        except:
            pass
        return datetime.min
    
    all_articles.sort(key=parse_date, reverse=True)
    result = all_articles[:limit]
    
    print(f"    Collected {len(result)} articles total")
    return result


# CLI test
if __name__ == "__main__":
    articles = fetch_hn_blogs(limit=5)
    print("\n--- Top 5 HN Blog Articles ---")
    for i, a in enumerate(articles, 1):
        print(f"{i}. [{a.source}] {a.title}")
        print(f"   {a.url}")
        print()
