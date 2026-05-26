#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Jina Reader API Utility
Fetches clean, LLM-friendly text content from URLs.

API: https://r.jina.ai/{url}
Cost: Free tier (20 req/min without key, 500 req/min with free API key)
"""

import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

# Import from centralized config
from src.config import JINA_READER_URL, JINA_TIMEOUT, JINA_MAX_CHARS


def fetch_full_content(url: str, timeout: int = JINA_TIMEOUT) -> Optional[str]:
    """
    Fetch full article content from a URL using Jina Reader API.
    
    Args:
        url: The article URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Clean markdown text of the article, or None if failed
    """
    if not url or not url.startswith(("http://", "https://")):
        logger.warning(f"Invalid URL: {url}")
        return None
    
    jina_url = f"{JINA_READER_URL}{url}"
    
    try:
        logger.info(f"Jina fetching: {url[:60]}...")

        with httpx.Client(timeout=timeout) as client:
            response = client.get(
                jina_url,
                headers={
                    "User-Agent": "Intel-Briefing-Reader/1.0",
                    "Accept": "text/plain"
                }
            )
            
            if response.status_code == 200:
                content = response.text.strip()
                
                # Validate content
                if len(content) < 100:
                    logger.warning(f"Content too short ({len(content)} chars)")
                    return None

                if len(content) > JINA_MAX_CHARS:
                    content = content[:JINA_MAX_CHARS] + "\n\n[...内容已截断...]"
                    logger.debug(f"Jina truncated to {JINA_MAX_CHARS} chars")
                else:
                    logger.debug(f"Jina fetched {len(content)} chars")
                
                return content
            else:
                logger.warning(f"Jina returned status {response.status_code}")
                return None

    except httpx.TimeoutException:
        logger.warning(f"Jina timeout after {timeout}s")
        return None
    except (httpx.HTTPError, ValueError) as e:
        logger.warning(f"Jina error: {e}")
        return None


def is_junk_content(text: str) -> bool:
    """
    Detect junk/garbage content: Cloudflare challenges, 403 pages, CAPTCHAs, etc.
    Ported from the companion PWA frontend's JUNK_PATTERNS.
    """
    if not text:
        return True
    
    import re
    junk_patterns = [
        r'cloudflare', r'ray id', r'403 forbidden',
        r'access denied', r'captcha', r'security check',
        r'just a moment', r'enable javascript',
        r'please verify you are a human', r'challenge-platform',
    ]
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in junk_patterns)


def fetch_search_snippet(title: str, url: str, timeout: int = 8) -> Optional[str]:
    """
    Fetch article description from DuckDuckGo Lite search results.
    When Jina fails (Cloudflare/403), search engines usually have a cached snippet.
    Ported from the companion PWA frontend's summary-generation logic.

    Args:
        title: Article title
        url: Article URL (used to extract domain for site: filter)
        timeout: Request timeout in seconds
        
    Returns:
        Search snippet text, or None if failed
    """
    if not title:
        return None
    
    try:
        from urllib.parse import urlparse, quote
        domain = urlparse(url).hostname or ""
        query = quote(f"{title} site:{domain}")
        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        
        print(f"    [DDG] Searching snippet for: {title[:40]}...")
        
        with httpx.Client(timeout=timeout) as client:
            response = client.get(
                search_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; IntelBriefing/1.0)"}
            )
            
            if response.status_code != 200:
                return None
            
            html = response.text
            # DuckDuckGo Lite returns results in <a class="result__snippet"> elements
            import re
            snippet_match = re.search(r'class="result__snippet"[^>]*>([^<]+)', html)
            if snippet_match:
                snippet = snippet_match.group(1).strip()
                if len(snippet) > 30:
                    print(f"    [DDG] Got snippet ({len(snippet)} chars)")
                    return snippet[:1000]
        
        return None
    except Exception:
        logger.exception("DDG search failed")
        return None


def fetch_content_with_fallback(url: str, title: str = "") -> Optional[str]:
    """
    Fetch article content using a multi-tier fallback chain:
    1. Jina Reader (full content)
    2. DuckDuckGo search snippet (if Jina fails or returns junk)
    
    Args:
        url: Article URL
        title: Article title (for search snippet fallback)
        
    Returns:
        Article content text, or None if all methods failed
    """
    # Tier 1: Jina Reader
    content = fetch_full_content(url)
    
    # Check for junk content
    if content and is_junk_content(content):
        print(f"    [WARN] Jina returned junk content, trying DDG fallback...")
        content = None
    
    if content:
        return content
    
    # Tier 2: DuckDuckGo search snippet
    if title:
        snippet = fetch_search_snippet(title, url)
        if snippet:
            return snippet
    
    return None


# CLI test
if __name__ == "__main__":
    test_url = "https://www.jeffgeerling.com/blog/2026/ode-to-the-aa-battery/"
    print(f"Testing Jina Reader with: {test_url}\n")
    
    content = fetch_full_content(test_url)
    
    if content:
        print("\n--- Content Preview (first 500 chars) ---")
        print(content[:500])
        print(f"\n--- Total: {len(content)} chars ---")
    else:
        print("Failed to fetch content.")
