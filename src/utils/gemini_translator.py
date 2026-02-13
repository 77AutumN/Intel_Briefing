"""
Gemini Translator - 使用 Gemini API 翻译文本为中文
用于将 ArXiv 论文摘要翻译成简体中文
"""
import sys
import time
import logging
import httpx

logger = logging.getLogger(__name__)

# Force UTF-8 stdout for Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Import from centralized config
try:
    from config import GEMINI_API_KEY, GEMINI_API_URL, GEMINI_MODEL, GEMINI_TIMEOUT, GEMINI_MAX_RETRIES
except ImportError:
    from src.config import GEMINI_API_KEY, GEMINI_API_URL, GEMINI_MODEL, GEMINI_TIMEOUT, GEMINI_MAX_RETRIES

def translate_to_chinese(text: str, max_chars: int = 100) -> str:
    """
    将英文文本翻译成简体中文。
    
    Args:
        text: 要翻译的英文文本
        max_chars: 输出的最大字符数（用于 brief）
    
    Returns:
        翻译后的中文文本，如果失败则返回原文
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY 未配置，跳过翻译")
        return text[:max_chars] + "..." if len(text) > max_chars else text
    
    if not text or len(text) < 10:
        return text
    
    prompt = f"""请将以下学术论文摘要完整翻译成简体中文，要求：
1. 保持学术风格，用词精准
2. 完整翻译全部内容，不要省略任何信息
3. 只输出翻译结果，不要添加任何解释

原文：
{text}"""

    url = f"{GEMINI_API_URL}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024
        }
    }

    for attempt in range(GEMINI_MAX_RETRIES):
        try:
            response = httpx.post(url, json=payload, timeout=GEMINI_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            if result:
                return result.strip()
            else:
                # API 返回空结果，重试
                if attempt < GEMINI_MAX_RETRIES - 1:
                    logger.warning(f"Gemini 返回空结果，重试 ({attempt + 1}/{GEMINI_MAX_RETRIES})...")
                    time.sleep(2 ** attempt)
                    continue
                return text[:max_chars] + "..." if len(text) > max_chars else text

        except (httpx.HTTPError, httpx.TimeoutException, ValueError, KeyError) as e:
            if attempt < GEMINI_MAX_RETRIES - 1:
                logger.warning(f"Gemini 翻译失败 ({attempt + 1}/{GEMINI_MAX_RETRIES}): {e}")
                time.sleep(2 ** attempt)
                continue
            logger.error(f"Gemini 翻译最终失败: {e}")
            return text[:max_chars] + "..." if len(text) > max_chars else text
    
    return text[:max_chars] + "..." if len(text) > max_chars else text


def translate_summary_pair(summary: str) -> tuple[str, str]:
    """
    为 ArXiv 论文生成两层摘要（中文）。
    
    Args:
        summary: 英文原始摘要
    
    Returns:
        (brief_cn, detail_cn) - 短摘要和详细摘要的中文版本
    """
    if not summary:
        return ("", "")
    
    # Brief: 翻译前100字
    brief_cn = translate_to_chinese(summary[:200], max_chars=80)
    
    # Detail: 翻译完整摘要
    detail_cn = translate_to_chinese(summary, max_chars=500)
    
    return (brief_cn, detail_cn)


def summarize_blog_article(content: str, mode: str = "brief") -> str:
    """
    为技术博客文章生成情报简报风格的中文摘要。
    
    Args:
        content: 博客文章的完整内容（Markdown格式）
        mode: "brief" (一句话摘要) 或 "detail" (深度分析)
    
    Returns:
        中文摘要
    """
    if not GEMINI_API_KEY or not content or len(content) < 50:
        return ""
    
    if mode == "brief":
        prompt = f"""请阅读以下技术博客文章，用一句话中文概括核心观点（最多100字）。
要求：
- 直接说重点，不要"本文介绍了..."这种开头
- 忽略作者信息、日期、URL等元数据
- 突出技术洞察或实用价值

文章内容：
{content[:2000]}"""
        max_tokens = 256
    else:  # detail
        prompt = f"""请作为技术情报分析师，阅读以下博客文章并生成中文深度分析报告。

要求：
1. 忽略作者信息、URL、图片链接等元数据
2. 提取核心技术观点和实践经验
3. 用3-4个段落组织：背景、关键发现、技术细节、实用价值
4. 语言风格：专业但易懂，适合技术人士快速阅读
5. 总长度控制在300-500字

文章内容：
{content[:6000]}"""
        max_tokens = 1024
    
    url = f"{GEMINI_API_URL}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": max_tokens
        }
    }
    
    try:
        with httpx.Client(timeout=GEMINI_TIMEOUT) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return result.strip() if result else ""
            else:
                logger.warning(f"Gemini 摘要失败: HTTP {response.status_code}")
                return ""
    except (httpx.HTTPError, httpx.TimeoutException, ValueError, KeyError) as e:
        logger.warning(f"Gemini 摘要出错: {e}")
        return ""


def generate_executive_summary(intel: dict) -> str:
    """
    为整份情报报告生成 Executive Summary（3-5句话概括今日要点）。

    Args:
        intel: 完整的情报数据字典

    Returns:
        中文 Executive Summary，如果失败返回空字符串
    """
    if not GEMINI_API_KEY:
        logger.debug("GEMINI_API_KEY 未配置，跳过 Executive Summary 生成")
        return ""

    # 收集各板块的标题作为输入
    highlights = []

    # 技术趋势 - 取前3条
    for item in intel.get("tech_trends", [])[:3]:
        title = item.get("title", "")
        heat = item.get("heat", "")
        if title:
            highlights.append(f"[技术] {title} (热度: {heat})")

    # 资本动向 - 取前2条
    for item in intel.get("capital_flow", [])[:2]:
        title = item.get("title", "")
        if title:
            highlights.append(f"[资本] {title}")

    # 学术前沿 - 取前2条
    for item in intel.get("research", [])[:2]:
        title = item.get("title", "")
        if title:
            highlights.append(f"[论文] {title}")

    # 产品精选 - 取前2条
    for item in intel.get("product_gems", [])[:2]:
        title = item.get("title", "")
        tagline = item.get("tagline", "")
        if title:
            highlights.append(f"[产品] {title}: {tagline}")

    if not highlights:
        return ""

    prompt = f"""你是一位资深科技情报分析师。请根据以下今日热点，撰写一段 Executive Summary（执行摘要）。

要求：
1. 用 3-5 句中文概括今天最值得关注的动态
2. 突出重大事件、趋势变化、值得关注的信号
3. 语言简洁有力，像给 CEO 的晨间简报
4. 不要罗列，要有分析和洞察
5. 总长度 150-250 字

今日热点：
{chr(10).join(highlights)}"""

    url = f"{GEMINI_API_URL}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 512
        }
    }

    try:
        with httpx.Client(timeout=GEMINI_TIMEOUT) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return result.strip() if result else ""
            else:
                logger.warning(f"Executive Summary 生成失败: HTTP {response.status_code}")
                return ""
    except (httpx.HTTPError, httpx.TimeoutException, ValueError, KeyError) as e:
        logger.warning(f"Executive Summary 生成出错: {e}")
        return ""


if __name__ == "__main__":
    # Test translation
    test_text = "Adapting large pretrained models to new tasks efficiently and continually is crucial for real-world deployment but remains challenging due to catastrophic forgetting."
    print("原文:", test_text)
    print("翻译:", translate_to_chinese(test_text, 80))
