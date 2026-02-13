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

# Jina Reader API endpoint
JINA_READER_URL = "https://r.jina.ai/"

# Config
FETCH_TIMEOUT = 30  # seconds
MAX_CONTENT_CHARS = 15000


def fetch_full_content(url: str, timeout: int = FETCH_TIMEOUT) -> Optional[str]:
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

                if len(content) > MAX_CONTENT_CHARS:
                    content = content[:MAX_CONTENT_CHARS] + "\n\n[...内容已截断...]"
                    logger.debug(f"Jina truncated to {MAX_CONTENT_CHARS} chars")
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
