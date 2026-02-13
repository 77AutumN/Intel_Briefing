import argparse
import json
import logging
import requests
from bs4 import BeautifulSoup
import sys
import time
import re
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Headers for scraping to avoid basic bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Constants
CONTENT_TRUNCATE_LIMIT = 3000


def _validate_url(url: str) -> bool:
    """Validate that a URL is well-formed."""
    return bool(url and url.startswith(('http://', 'https://')))


def filter_items(items: List[Dict], keyword: Optional[str] = None) -> List[Dict]:
    if not keyword:
        return items
    keywords = [k.strip() for k in keyword.split(',') if k.strip()]
    pattern = '|'.join([r'\b' + re.escape(k) + r'\b' for k in keywords])
    regex = r'(?i)(' + pattern + r')'
    return [item for item in items if re.search(regex, item.get('title', ''))]


def fetch_url_content(url: str) -> str:
    """
    Fetches the content of a URL and extracts text from paragraphs.
    Truncates to CONTENT_TRUNCATE_LIMIT characters.
    """
    if not _validate_url(url):
        return ""
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        text = soup.get_text(separator=' ', strip=True)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text[:CONTENT_TRUNCATE_LIMIT]
    except (requests.RequestException, ValueError, AttributeError) as e:
        logger.debug(f"Failed to fetch content from {url}: {e}")
        return ""


def enrich_items_with_content(items: List[Dict], max_workers: int = 10) -> List[Dict]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {executor.submit(fetch_url_content, item['url']): item for item in items}
        for future in concurrent.futures.as_completed(future_to_item):
            item = future_to_item[future]
            try:
                content = future.result()
                if content:
                    item['content'] = content
            except (requests.RequestException, ValueError) as e:
                logger.debug(f"Enrich failed for {item.get('url', '?')}: {e}")
                item['content'] = ""
    return items

# --- Source Fetchers ---

def fetch_hackernews(limit: int = 5, keyword: Optional[str] = None) -> List[Dict]:
    base_url = "https://news.ycombinator.com"
    news_items = []
    page = 1
    max_pages = 5

    while len(news_items) < limit and page <= max_pages:
        url = f"{base_url}/news?p={page}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                break
        except requests.RequestException as e:
            logger.warning(f"HN page {page} fetch failed: {e}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('.athing')
        if not rows:
            break

        page_items = []
        for row in rows:
            try:
                id_ = row.get('id')
                title_line = row.select_one('.titleline a')
                if not title_line:
                    continue
                title = title_line.get_text()
                link = title_line.get('href')

                score_span = soup.select_one(f'#score_{id_}')
                score = score_span.get_text() if score_span else "0 points"

                age_span = soup.select_one(f'.age a[href="item?id={id_}"]')
                time_str = age_span.get_text() if age_span else ""

                if link and link.startswith('item?id='):
                    link = f"{base_url}/{link}"

                page_items.append({
                    "source": "Hacker News",
                    "title": title,
                    "url": link,
                    "heat": score,
                    "time": time_str
                })
            except (AttributeError, KeyError, TypeError) as e:
                logger.debug(f"Failed to parse HN row: {e}")
                continue

        news_items.extend(filter_items(page_items, keyword))
        if len(news_items) >= limit:
            break
        page += 1
        time.sleep(0.5)

    return news_items[:limit]


def fetch_weibo(limit: int = 5, keyword: Optional[str] = None) -> List[Dict]:
    url = "https://weibo.com/ajax/side/hotSearch"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://weibo.com/"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        items = data.get('data', {}).get('realtime', [])

        all_items = []
        for item in items:
            title = item.get('note', '') or item.get('word', '')
            if not title:
                continue

            heat = item.get('num', 0)
            full_url = f"https://s.weibo.com/weibo?q={quote(title)}&Refer=top"

            all_items.append({
                "source": "Weibo Hot Search",
                "title": title,
                "url": full_url,
                "heat": f"{heat}",
                "time": "Real-time"
            })

        return filter_items(all_items, keyword)[:limit]
    except (requests.RequestException, ValueError, KeyError) as e:
        logger.warning(f"Weibo fetch failed: {e}")
        return []


def fetch_github(limit: int = 5, keyword: Optional[str] = None) -> List[Dict]:
    try:
        response = requests.get("https://github.com/trending", headers=HEADERS, timeout=10)
    except requests.RequestException as e:
        logger.warning(f"GitHub trending fetch failed: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    items = []
    for article in soup.select('article.Box-row'):
        try:
            h2 = article.select_one('h2 a')
            if not h2:
                continue
            title = h2.get_text(strip=True).replace('\n', '').replace(' ', '')
            link = "https://github.com" + h2['href']

            desc = article.select_one('p')
            desc_text = desc.get_text(strip=True) if desc else ""

            stars_tag = article.select_one('a[href$="/stargazers"]')
            stars = stars_tag.get_text(strip=True) if stars_tag else ""

            items.append({
                "source": "GitHub Trending",
                "title": f"{title} - {desc_text}",
                "url": link,
                "heat": f"{stars} stars",
                "time": "Today"
            })
        except (AttributeError, KeyError, TypeError) as e:
            logger.debug(f"Failed to parse GitHub row: {e}")
            continue
    return filter_items(items, keyword)[:limit]


def fetch_36kr(limit: int = 5, keyword: Optional[str] = None) -> List[Dict]:
    try:
        response = requests.get("https://36kr.com/newsflashes", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = []
        for item in soup.select('.newsflash-item'):
            title = item.select_one('.item-title').get_text(strip=True)
            href = item.select_one('.item-title')['href']
            time_tag = item.select_one('.time')
            time_str = time_tag.get_text(strip=True) if time_tag else ""

            items.append({
                "source": "36Kr",
                "title": title,
                "url": f"https://36kr.com{href}" if not href.startswith('http') else href,
                "time": time_str,
                "heat": ""
            })
        return filter_items(items, keyword)[:limit]
    except (requests.RequestException, AttributeError, KeyError, TypeError) as e:
        logger.warning(f"36Kr fetch failed: {e}")
        return []


def fetch_v2ex(limit: int = 5, keyword: Optional[str] = None) -> List[Dict]:
    try:
        data = requests.get("https://www.v2ex.com/api/topics/hot.json", headers=HEADERS, timeout=10).json()
        items = []
        for t in data:
            replies = t.get('replies', 0)
            items.append({
                "source": "V2EX",
                "title": t['title'],
                "url": t['url'],
                "heat": f"{replies} replies",
                "time": "Hot"
            })
        return filter_items(items, keyword)[:limit]
    except (requests.RequestException, ValueError, KeyError) as e:
        logger.warning(f"V2EX fetch failed: {e}")
        return []


def fetch_tencent(limit: int = 5, keyword: Optional[str] = None) -> List[Dict]:
    try:
        url = "https://i.news.qq.com/web_backend/v2/getTagInfo?tagId=aEWqxLtdgmQ%3D"
        data = requests.get(url, headers={"Referer": "https://news.qq.com/"}, timeout=10).json()
        items = []
        for news in data['data']['tabs'][0]['articleList']:
            items.append({
                "source": "Tencent News",
                "title": news['title'],
                "url": news.get('url') or news.get('link_info', {}).get('url'),
                "time": news.get('pub_time', '') or news.get('publish_time', '')
            })
        return filter_items(items, keyword)[:limit]
    except (requests.RequestException, ValueError, KeyError, IndexError) as e:
        logger.warning(f"Tencent News fetch failed: {e}")
        return []


def fetch_wallstreetcn(limit: int = 5, keyword: Optional[str] = None) -> List[Dict]:
    try:
        url = "https://api-one.wallstcn.com/apiv1/content/information-flow?channel=global-channel&accept=article&limit=30"
        data = requests.get(url, timeout=10).json()
        items = []
        for item in data['data']['items']:
            res = item.get('resource')
            if res and (res.get('title') or res.get('content_short')):
                ts = res.get('display_time', 0)
                time_str = datetime.fromtimestamp(ts).strftime('%H:%M') if ts else ""
                items.append({
                    "source": "Wall Street CN",
                    "title": res.get('title') or res.get('content_short'),
                    "url": res.get('uri'),
                    "time": time_str
                })
        return filter_items(items, keyword)[:limit]
    except (requests.RequestException, ValueError, KeyError) as e:
        logger.warning(f"WallStreetCN fetch failed: {e}")
        return []


def fetch_producthunt(limit: int = 5, keyword: Optional[str] = None) -> List[Dict]:
    try:
        response = requests.get("https://www.producthunt.com/feed", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'xml')
        if not soup.find('item'):
            soup = BeautifulSoup(response.text, 'html.parser')

        items = []
        for entry in soup.find_all(['item', 'entry']):
            title = entry.find('title').get_text(strip=True)
            link_tag = entry.find('link')
            url = link_tag.get('href') or link_tag.get_text(strip=True) if link_tag else ""

            pubBox = entry.find('pubDate') or entry.find('published')
            pub = pubBox.get_text(strip=True) if pubBox else ""

            items.append({
                "source": "Product Hunt",
                "title": title,
                "url": url,
                "time": pub,
                "heat": "Top Product"
            })
        return filter_items(items, keyword)[:limit]
    except (requests.RequestException, AttributeError, ValueError) as e:
        logger.warning(f"Product Hunt fetch failed: {e}")
        return []


def main():
    parser = argparse.ArgumentParser()
    sources_map = {
        'hackernews': fetch_hackernews, 'weibo': fetch_weibo, 'github': fetch_github,
        '36kr': fetch_36kr, 'v2ex': fetch_v2ex, 'tencent': fetch_tencent,
        'wallstreetcn': fetch_wallstreetcn, 'producthunt': fetch_producthunt
    }

    parser.add_argument('--source', default='all', help='Source(s) to fetch from (comma-separated)')
    parser.add_argument('--limit', type=int, default=10, help='Limit per source. Default 10')
    parser.add_argument('--keyword', help='Comma-sep keyword filter')
    parser.add_argument('--deep', action='store_true', help='Download article content for detailed summarization')

    args = parser.parse_args()

    to_run = []
    if args.source == 'all':
        to_run = list(sources_map.values())
    else:
        requested_sources = [s.strip() for s in args.source.split(',')]
        for s in requested_sources:
            if s in sources_map:
                to_run.append(sources_map[s])

    results = []
    for func in to_run:
        try:
            results.extend(func(args.limit, args.keyword))
        except Exception as e:
            logger.warning(f"Source {func.__name__} failed: {e}")

    if args.deep and results:
        sys.stderr.write(f"Deep fetching content for {len(results)} items...\n")
        results = enrich_items_with_content(results)

    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
