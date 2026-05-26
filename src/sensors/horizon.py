#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Horizon Sensor - Cross-Domain Cognitive Radar
Fetches signals from outside the tech vertical to break information cocoons

Domains:
  Science (Nature, Quanta Magazine)
  Philosophy & Humanities (Aeon Essays, Aeon Philosophy)
  Geopolitics & Economics (Reuters, Geopolitical Futures)
  Cross-Disciplinary (Nautilus, Aeon Science)
  Design & Aesthetics (Dezeen)

Protocol: RSS/Atom (public, free, legal)
Update: Daily
"""

import re
import html
import urllib.request
import xml.etree.ElementTree as ET
import ssl
import socket
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

# Global TCP timeout
socket.setdefaulttimeout(15.0)

FETCH_TIMEOUT = 10
MAX_ARTICLES_PER_FEED = 3


def _safe_print(msg: str):
    """Windows GBK-safe print for emoji-containing messages."""
    try:
        print(msg)
    except UnicodeEncodeError:
        # Fallback: strip problematic characters
        safe_msg = msg.encode('ascii', errors='replace').decode('ascii')
        print(safe_msg)


# === Horizon Data Sources ===
# Curated for maximum cognitive diversity, zero overlap with existing tech sensors
HORIZON_FEEDS = [
    # --- Science Frontier ---
    {
        "title": "Nature (Current Issue)",
        "rss": "https://feeds.nature.com/nature/rss/current",
        "domain": "science",
        "icon": "[SCI]"
    },
    {
        "title": "Quanta Magazine",
        "rss": "https://www.quantamagazine.org/feed/",
        "domain": "science",
        "icon": "[SCI]"
    },
    # --- Philosophy & Humanities ---
    {
        "title": "Aeon (Essays)",
        "rss": "https://aeon.co/feed.rss",
        "domain": "philosophy",
        "icon": "[PHI]"
    },
    {
        "title": "Aeon (Philosophy)",
        "rss": "https://aeon.co/philosophy.rss",
        "domain": "philosophy",
        "icon": "[PHI]"
    },
    # --- Geopolitics & Economics ---
    {
        "title": "Reuters Top News",
        "rss": "https://feeds.reuters.com/reuters/topNews",
        "domain": "geopolitics",
        "icon": "[GEO]"
    },
    {
        "title": "Geopolitical Futures",
        "rss": "https://geopoliticalfutures.com/feed",
        "domain": "geopolitics",
        "icon": "[GEO]"
    },
    # --- Cross-Disciplinary ---
    {
        "title": "Nautilus",
        "rss": "https://nautil.us/feed/",
        "domain": "crossdisciplinary",
        "icon": "[XD]"
    },
    {
        "title": "Aeon (Science)",
        "rss": "https://aeon.co/science.rss",
        "domain": "science",
        "icon": "[XD]"
    },
    # --- Design & Aesthetics ---
    {
        "title": "Dezeen",
        "rss": "https://www.dezeen.com/feed/",
        "domain": "design",
        "icon": "[DSN]"
    },
]


@dataclass
class HorizonArticle:
    """Represents a cross-domain article from the Horizon sensor."""
    title: str
    url: str
    source: str
    domain: str       # science, philosophy, geopolitics, crossdisciplinary, design
    icon: str         # text tag for the domain
    pub_date: str = ""
    content: str = ""  # Article description/summary from RSS
    author: str = ""


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities from text."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = html.unescape(clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def _create_ssl_context():
    """Create SSL context with proper certificate verification."""
    return ssl.create_default_context()


def _fetch_url(url: str, timeout: int = FETCH_TIMEOUT) -> Optional[str]:
    """Fetch URL content with timeout and error handling."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; 7Brief-Horizon/1.0; +https://7brief.com)"
        })
        with urllib.request.urlopen(req, timeout=timeout, context=_create_ssl_context()) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        _safe_print(f"    [WARN] Horizon: Failed to fetch {url[:60]}...: {e}")
        return None


def _extract_author(entry, ns=None) -> str:
    """Extract author from RSS/Atom entry."""
    raw = None
    if ns:
        author_el = entry.find('atom:author/atom:name', ns)
        if author_el is None:
            author_el = entry.find('atom:author', ns)
        if author_el is not None and author_el.text:
            raw = author_el.text
    if raw is None:
        dc_ns = {'dc': 'http://purl.org/dc/elements/1.1/'}
        creator = entry.find('dc:creator', dc_ns)
        if creator is None:
            creator = entry.find('author')
        if creator is not None and creator.text:
            raw = creator.text
    if raw is None:
        return ""
    safe = html.unescape(str(raw)).replace('\n', ' ').replace('\r', '').strip()
    return safe[:60]


def _parse_feed(feed_content: str, source_title: str, domain: str, icon: str) -> List[HorizonArticle]:
    """Parse RSS/Atom feed content to extract Horizon articles."""
    articles = []
    try:
        root = ET.fromstring(feed_content)

        # Handle Atom feeds
        if 'atom' in root.tag.lower() or root.tag == '{http://www.w3.org/2005/Atom}feed':
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('.//atom:entry', ns) or root.findall('.//entry')
            for entry in entries[:MAX_ARTICLES_PER_FEED]:
                title = entry.find('atom:title', ns) or entry.find('title')
                link = entry.find('atom:link[@rel="alternate"]', ns) or entry.find('atom:link', ns) or entry.find('link')
                published = entry.find('atom:published', ns) or entry.find('atom:updated', ns) or entry.find('published') or entry.find('updated')
                summary = entry.find('atom:summary', ns) or entry.find('atom:content', ns) or entry.find('summary') or entry.find('content')

                title_text = title.text if title is not None and title.text else "Untitled"
                link_href = link.get('href', '') if link is not None else ""
                pub_text = published.text[:10] if published is not None and published.text else ""
                content_text = _strip_html(summary.text) if summary is not None and summary.text else ""
                author_text = _extract_author(entry, ns)

                if title_text and link_href:
                    articles.append(HorizonArticle(
                        title=title_text,
                        url=link_href,
                        source=source_title,
                        domain=domain,
                        icon=icon,
                        pub_date=pub_text,
                        content=content_text[:500],
                        author=author_text
                    ))

        # Handle RSS 2.0 feeds
        else:
            items = root.findall('.//item')
            for item in items[:MAX_ARTICLES_PER_FEED]:
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                description = item.find('description')

                title_text = title.text if title is not None and title.text else "Untitled"
                link_text = link.text if link is not None and link.text else ""
                pub_text = pub_date.text[:16] if pub_date is not None and pub_date.text else ""
                content_text = _strip_html(description.text) if description is not None and description.text else ""
                author_text = _extract_author(item)

                if title_text and link_text:
                    articles.append(HorizonArticle(
                        title=title_text,
                        url=link_text,
                        source=source_title,
                        domain=domain,
                        icon=icon,
                        pub_date=pub_text,
                        content=content_text[:500],
                        author=author_text
                    ))
    except ET.ParseError as e:
        _safe_print(f"    [WARN] Horizon XML parse error for {source_title}: {e}")
    except Exception as e:
        _safe_print(f"    [WARN] Horizon parse error for {source_title}: {e}")

    return articles


def fetch_horizon(limit: int = 10) -> List[HorizonArticle]:
    """
    Fetch latest cross-domain articles from Horizon feeds.

    Args:
        limit: Maximum total number of articles to return

    Returns:
        List of HorizonArticle objects, sorted by recency, with domain diversity
    """
    _safe_print(f"[*] Fetching Horizon feeds ({len(HORIZON_FEEDS)} sources)...")

    all_articles = []

    for i, feed in enumerate(HORIZON_FEEDS):
        feed_content = _fetch_url(feed["rss"])
        if feed_content:
            articles = _parse_feed(feed_content, feed["title"], feed["domain"], feed["icon"])
            all_articles.extend(articles)
            if articles:
                _safe_print(f"    [{i+1}/{len(HORIZON_FEEDS)}] {feed['icon']} {feed['title']}: {len(articles)} articles")
        else:
            _safe_print(f"    [{i+1}/{len(HORIZON_FEEDS)}] {feed['icon']} {feed['title']}: failed")

    # Sort by date (best-effort)
    def parse_date(article):
        if not article.pub_date:
            return datetime.min
        try:
            return datetime.fromisoformat(article.pub_date.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            pass
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(article.pub_date)
        except Exception:
            pass
        return datetime.min

    all_articles.sort(key=parse_date, reverse=True)

    # Ensure domain diversity: at least 1 article from each domain that returned results
    domains_seen = {}
    diverse_result = []
    remaining = []

    for article in all_articles:
        if article.domain not in domains_seen:
            domains_seen[article.domain] = True
            diverse_result.append(article)
        else:
            remaining.append(article)

    # Fill up to limit with remaining articles
    diverse_result.extend(remaining)
    result = diverse_result[:limit]

    # Stats
    domain_counts = {}
    for a in result:
        domain_counts[a.domain] = domain_counts.get(a.domain, 0) + 1

    domain_summary = ", ".join(f"{d}: {c}" for d, c in sorted(domain_counts.items()))
    _safe_print(f"    Horizon total: {len(result)} articles ({domain_summary})")
    return result


# CLI test
if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    articles = fetch_horizon(limit)
    _safe_print(f"\n{'='*60}")
    _safe_print(f"  Horizon Sensor -- Top {limit}")
    _safe_print(f"{'='*60}\n")
    for i, a in enumerate(articles, 1):
        _safe_print(f"{i}. {a.icon} [{a.source}] {a.title}")
        if a.author:
            _safe_print(f"   Author: {a.author}")
        _safe_print(f"   {a.content[:120]}...")
        _safe_print(f"   -> {a.url}")
        _safe_print("")
