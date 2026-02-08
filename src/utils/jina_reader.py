#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Jina Reader API Utility
Fetches clean, LLM-friendly text content from URLs.

API: https://r.jina.ai/{url}
Cost: Free tier (20 req/min without key, 500 req/min with free API key)
"""

import httpx
from typing import Optional

# Jina Reader API endpoint
JINA_READER_URL = "https://r.jina.ai/"

# Config
FETCH_TIMEOUT = 30  # seconds


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
        print(f"    [WARN] Invalid URL: {url}")
        return None
    
    jina_url = f"{JINA_READER_URL}{url}"
    
    try:
        print(f"    [Jina] Fetching: {url[:60]}...")
        
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
                    print(f"    [WARN] Content too short ({len(content)} chars)")
                    return None
                
                # Truncate if too long (to save Gemini tokens)
                max_chars = 15000  # ~4k tokens
                if len(content) > max_chars:
                    content = content[:max_chars] + "\n\n[...内容已截断...]"
                    print(f"    [Jina] Truncated to {max_chars} chars")
                else:
                    print(f"    [Jina] Fetched {len(content)} chars")
                
                return content
            else:
                print(f"    [WARN] Jina returned status {response.status_code}")
                return None
                
    except httpx.TimeoutException:
        print(f"    [WARN] Jina timeout after {timeout}s")
        return None
    except Exception as e:
        print(f"    [WARN] Jina error: {e}")
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
