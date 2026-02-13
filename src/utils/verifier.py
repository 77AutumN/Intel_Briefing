
import logging
import httpx

logger = logging.getLogger(__name__)


def verify_link(url: str, timeout: float = 5.0) -> bool:
    """
    Verifies if a link is valid (returns 200 OK).
    """
    if not url or not url.startswith(("http://", "https://")):
        return False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = httpx.head(url, headers=headers, timeout=timeout, follow_redirects=True)
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False

        response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        return response.status_code == 200

    except httpx.TimeoutException:
        logger.debug(f"Link verification timeout: {url}")
        return False
    except (httpx.HTTPError, ValueError) as e:
        logger.debug(f"Link verification error ({url}): {e}")
        return False
