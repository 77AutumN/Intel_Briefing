"""
Generate AI Summaries - 为所有文章生成预烘焙 AI 摘要
在 Engine 端生成，随日报一起推送到 PWA

输出格式: { "articleId": "summaryText" }
articleId 格式: {dateNoHyphens}-{category}-{index}
与配套的 PWA 前端摘要逻辑保持一致
"""

import os
import sys
import json
import time
import httpx

from src.config import cfg

# --- Config (from unified config layer) ---
GEMINI_API_KEY = cfg.gemini_api_key
GEMINI_API_URL = cfg.gemini_api_url
MODEL_NAME = "gemini-2.5-flash-lite"  # summaries use lite model for cost

# Jina Reader for fetching article content
JINA_TIMEOUT = 12  # seconds

# Domains to skip when fetching content
SKIP_DOMAINS = [
    "xiaohongshu.com", "v2ex.com", "36kr.com", "wallstreetcn.com",
    "weibo.com", "twitter.com", "x.com"
]

# Category mapping (Engine key -> PWA category)
CATEGORY_MAP = {
    "tech_trends": "tech",
    "capital_flow": "capital",
    "research": "research",
    "product_gems": "product",
    "insights": "insights",
}

# Slice limits per category (must match generate_report)
CATEGORY_LIMITS = {
    "tech_trends": 10,
    "capital_flow": 10,
    "research": 5,
    "product_gems": 8,
    "insights": 5,
}


def _call_gemini(prompt: str, max_tokens: int = 256) -> str:
    """Call Gemini API to generate text."""
    if not GEMINI_API_KEY:
        return ""

    url = f"{GEMINI_API_URL}/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": max_tokens
        }
    }

    try:
        response = httpx.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            result = (data.get("candidates", [{}])[0]
                      .get("content", {})
                      .get("parts", [{}])[0]
                      .get("text", ""))
            return result.strip() if result else ""
        else:
            print(f"    ⚠️ Gemini API error: {response.status_code}")
            return ""
    except Exception as e:
        print(f"    ⚠️ Gemini call failed: {e}")
        return ""


def _fetch_via_jina(url: str) -> str:
    """Fetch article content via Jina Reader API."""
    if not url:
        return ""

    # Skip known-bad domains
    for domain in SKIP_DOMAINS:
        if domain in url:
            return ""

    try:
        jina_url = f"https://r.jina.ai/{url}"
        response = httpx.get(
            jina_url,
            headers={"Accept": "text/plain", "X-No-Cache": "true"},
            timeout=JINA_TIMEOUT
        )
        if response.status_code == 200:
            text = response.text
            if text and len(text) > 100:
                return text[:3000]
        return ""
    except Exception as e:
        print(f"    ⚠️ Jina fetch failed: {e}")
        return ""


def _is_garbage_content(text: str) -> bool:
    """Check if fetched content is garbage (Cloudflare block, paywall, etc.)."""
    garbage_keywords = [
        "checking your browser", "security service", "Ray ID",
        "enable JavaScript", "access denied", "subscribe to read",
        "sign in to continue", "cloudflare", "captcha",
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in garbage_keywords)


def _summarize_content(content: str, title: str = "") -> str:
    """Generate a Chinese summary from content using Gemini."""
    if not content or len(content.strip()) < 20:
        return ""

    prompt = f"""请用简洁的中文为以下内容生成一段50字以内的摘要。

要求：
1. 直接输出摘要，不要任何前缀
2. 突出核心信息和价值
3. 语言简洁有力

内容：
{content[:3000]}"""

    return _call_gemini(prompt, max_tokens=128)


def _translate_tagline(tagline: str, title: str = "") -> str:
    """Translate an English product tagline to natural Chinese."""
    if not tagline:
        return f"📰 快讯：{title}"

    prompt = f"""将以下产品标语翻译为简洁自然的中文（15字以内），保留核心卖点。

要求：
1. 直接输出翻译结果，不要任何前缀或解释
2. 语言要通顺自然，像中文母语者写的
3. 不要直译，要意译出产品价值

产品名：{title}
标语：{tagline}"""

    result = _call_gemini(prompt, max_tokens=64)
    if result:
        # Clean up any quotes or prefixes the model might add
        result = result.strip().strip('"').strip("'").strip("⚡").strip()
        return f"⚡ {result}"
    else:
        return f"⚡ {tagline}"  # Fallback: keep English


def generate_summaries(intel: dict, date_str: str) -> dict:
    """
    Generate pre-baked AI summaries from intel data.

    Args:
        intel: The intelligence dict from fetch_all_sources()
        date_str: Date string like "2026-02-11"

    Returns:
        Dict of { "articleId": "summaryText" }
    """
    date_prefix = date_str.replace("-", "")
    summaries = {}
    total = 0
    generated = 0
    failed = 0

    print(f"\n{'='*50}")
    print(f"  📝 Generating AI Summaries")
    print(f"  Date: {date_str} | Prefix: {date_prefix}")
    print(f"{'='*50}\n")

    # ========== TECH TRENDS ==========
    tech_items = intel.get("tech_trends", [])[:CATEGORY_LIMITS["tech_trends"]]
    if tech_items:
        print(f"[*] Tech Trends ({len(tech_items)} items)...")
        for i, item in enumerate(tech_items):
            article_id = f"{date_prefix}-tech-{i}"
            title = item.get("title", "")
            url = item.get("url", "")
            total += 1

            # Try Jina Reader to fetch real content
            print(f"  [{i+1}] Fetching: {title[:40]}...")
            content = _fetch_via_jina(url)

            if content and not _is_garbage_content(content):
                summary = _summarize_content(content, title)
                if summary:
                    summaries[article_id] = summary
                    generated += 1
                    print(f"      ✅ Generated summary ({len(summary)} chars)")
                else:
                    summaries[article_id] = f"📰 快讯：{title}"
                    failed += 1
                    print(f"      ⚠️ Gemini failed, using title")
            else:
                summaries[article_id] = f"📰 快讯：{title}"
                failed += 1
                print(f"      ⚠️ No content, using title")

            time.sleep(0.5)  # Rate limit

    # ========== CAPITAL FLOW ==========
    capital_items = intel.get("capital_flow", [])[:CATEGORY_LIMITS["capital_flow"]]
    if capital_items:
        print(f"\n[*] Capital Flow ({len(capital_items)} items)...")
        for i, item in enumerate(capital_items):
            article_id = f"{date_prefix}-capital-{i}"
            title = item.get("title", "")
            total += 1
            # 36Kr/WallStreetCN: title-only is expected (sites block scraping)
            summaries[article_id] = f"📰 快讯：{title}"
            generated += 1

    # ========== RESEARCH (ArXiv) ==========
    research_items = intel.get("research", [])[:CATEGORY_LIMITS["research"]]
    if research_items:
        print(f"\n[*] Research ({len(research_items)} items)...")
        for i, item in enumerate(research_items):
            article_id = f"{date_prefix}-research-{i}"
            title = item.get("title", "")
            summary = item.get("summary", "")
            total += 1

            if summary:
                # ArXiv has full abstract — translate and summarize
                cn_summary = _summarize_content(summary, title)
                if cn_summary:
                    summaries[article_id] = cn_summary
                    generated += 1
                    print(f"  [{i+1}] ✅ {title[:40]}...")
                else:
                    summaries[article_id] = f"📰 快讯：{title}"
                    failed += 1
            else:
                summaries[article_id] = f"📰 快讯：{title}"
                failed += 1

            time.sleep(0.5)

    # ========== PRODUCT GEMS ==========
    product_items = intel.get("product_gems", [])[:CATEGORY_LIMITS["product_gems"]]
    if product_items:
        print(f"\n[*] Product Gems ({len(product_items)} items)...")
        for i, item in enumerate(product_items):
            article_id = f"{date_prefix}-product-{i}"
            title = item.get("title", "")
            tagline = item.get("tagline", "")
            grok_review = item.get("grok_review", "")
            total += 1

            if grok_review:
                # Has Grok review → summarize to Chinese
                summary = _summarize_content(grok_review, title)
                if summary:
                    summaries[article_id] = summary
                    generated += 1
                    print(f"  [{i+1}] ✅ {title[:30]}... (from Grok)")
                elif tagline:
                    # Grok summarization failed, translate tagline
                    cn = _translate_tagline(tagline, title)
                    summaries[article_id] = cn
                    generated += 1
                else:
                    summaries[article_id] = f"📰 快讯：{title}"
                    failed += 1
            elif tagline:
                # No Grok but has tagline — translate to Chinese
                cn = _translate_tagline(tagline, title)
                summaries[article_id] = cn
                generated += 1
                print(f"  [{i+1}] ℹ️ {title[:30]}... (tagline→CN)")
            else:
                summaries[article_id] = f"📰 快讯：{title}"
                failed += 1

            time.sleep(0.3)

    # ========== INSIGHTS (HN Blogs) ==========
    insights_items = intel.get("insights", [])[:CATEGORY_LIMITS["insights"]]
    if insights_items:
        print(f"\n[*] Insights ({len(insights_items)} items)...")
        for i, item in enumerate(insights_items):
            article_id = f"{date_prefix}-insights-{i}"
            title = item.get("title", "")
            content = item.get("content", "")
            total += 1

            # Insights already have content from RSS/Jina (fetched in fetch_all_sources)
            if content and len(content) > 50:
                summary = _summarize_content(content, title)
                if summary:
                    summaries[article_id] = summary
                    generated += 1
                    print(f"  [{i+1}] ✅ {title[:40]}...")
                else:
                    summaries[article_id] = f"📰 快讯：{title}"
                    failed += 1
            else:
                summaries[article_id] = f"📰 快讯：{title}"
                failed += 1

            time.sleep(0.5)

    # ========== Summary ==========
    print(f"\n{'='*50}")
    print(f"  📊 Summary Generation Complete")
    print(f"  Total:     {total}")
    print(f"  Generated: {generated}")
    print(f"  Failed:    {failed}")
    print(f"  Output:    {len(summaries)} entries")
    print(f"{'='*50}\n")

    return summaries
