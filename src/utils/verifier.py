
import httpx
import time

def verify_link(url: str, timeout: float = 5.0) -> bool:
    """
    Verifies if a link is valid (returns 200 OK).
    Handles basic anti-bot headers.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Trusted/Special domains that might block HEAD requests or need special handling can be skipped or handled here.
    # For now, we focus on GitHub 404s which are the main issue.
    
    try:
        # Try HEAD first for speed
        response = httpx.head(url, headers=headers, timeout=timeout, follow_redirects=True)
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
            
        # If HEAD fails (e.g. 405 Method Not Allowed), try GET with stream to avoid downloading big files
        response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        return response.status_code == 200
        
    except Exception as e:
        print(f"  ⚠️ Link Verification Error ({url}): {e}")
        return False
