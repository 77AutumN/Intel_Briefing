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


def generate_brief(content: str, category: str = "general") -> str:
    """
    为内容生成编辑风格的中文摘要（80-120字）。
    替代旧的 translate+truncate 模式，输出更自然、有信息量。
    
    Args:
        content: 完整的原文内容（英文或中文）
        category: 栏目类型 (tech/research/product/insights/general)
    
    Returns:
        中文摘要（80-120字），失败则返回空字符串
    """
    if not GEMINI_API_KEY or not content or len(content) < 20:
        return ""
    
    prompt = f"""你是世界顶级的科技情报编辑。请用2-3句自然流畅的中文概括以下内容（80-120字）。

要求：
1. 第一句必须有「主角」——谁（人/公司/团队）做了什么
2. 第二句点明为什么重要、有什么影响
3. 语气像在跟同事分享一个有趣的发现，自然不机械
4. 专业术语保留英文（如 LLM, FPGA, CLI）
5. 禁止“本文介绍了”、“本研究提出了”等学术八股开头
6. 直接输出摘要，不要任何前缀

内容：
{content[:3000]}"""
    
    url = f"{GEMINI_API_URL}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 256
        }
    }
    
    try:
        response = httpx.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return result.strip() if result else ""
    except Exception:
        logger.exception("generate_brief 失败")
        return ""


def translate_summary_pair(summary: str) -> tuple[str, str]:
    """
    为 ArXiv 论文生成两层摘要（中文）。
    Brief 使用 generate_brief（编辑风格），Detail 使用完整翻译。
    
    Args:
        summary: 英文原始摘要
    
    Returns:
        (brief_cn, detail_cn) - 短摘要和详细摘要的中文版本
    """
    if not summary:
        return ("", "")
    
    # Brief: 编辑风格摘要（80-120字）
    brief_cn = generate_brief(summary, category="research")
    
    # Detail: 翻译完整摘要
    detail_cn = translate_to_chinese(summary, max_chars=2000)
    
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
        prompt = f"""你是世界顶级的科技情报编辑。请用2-3句自然的中文概括这篇文章的核心要点（80-120字）。

要求：
1. 第一句有「主角」——谁做了什么、发现了什么
2. 补充为什么值得关注
3. 语气像在跟同事分享有趣发现
4. 专业术语保留英文
5. 禁止“本文介绍了”等八股开头
6. 忽略作者信息、日期、URL 等元数据

文章内容：
{content[:3000]}"""
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


def generate_news_brief(title: str, content: str = "", category: str = "tech",
                        _depth: int = 0) -> str:
    """
    为 Tech/Capital 类新闻生成情报风格的中文短报（80-120字）。
    包含 [JUNK] 熔断协议：如果内容是垃圾，AI 返回 [JUNK] 时自动降级为标题推断。
    Ported from the companion PWA frontend's summary-generation logic.

    Args:
        title: 文章标题
        content: 文章全文或片段（可以为空，此时做标题推断）
        category: 栏目类型 (tech/capital)
        _depth: 内部递归计数器，防止 AI 持续返回 [JUNK] 时无限递归 + 烧 API

    Returns:
        中文短报（80-120字），失败则返回空字符串
    """
    if not GEMINI_API_KEY or not title:
        return ""
    
    # 无内容时做标题推断
    if not content or len(content.strip()) < 20:
        prompt = f"""根据标题推断内容，用1-2句中文描述（40-80字）。

标题：「{title}」

规则：
1. 第一句直接说「谁/哪家公司 + 做了什么」，如果标题有具体人名或公司名必须写出。
2. 绝对禁止用「这篇文章大概讲的是」「这篇文章大概在说」「本文介绍了」等废话开头。
3. 只推断大方向，不要编造具体数据。不要提及来源名称。
4. 语气自然，像跟同事聊天。直接输出。"""
        max_tokens = 128
    else:
        # 有内容时生成完整短报，含 [JUNK] 熔断
        prompt = f"""你是 7Brief 的首席科技情报特工。将以下长文本提炼为 100 字以内的高信息密度中文短报。

标题：{title}
正文：{content[:3000]}

规则（违背将被阻断）：
1. 垃圾熔断：如果正文包含 "Access Denied"、"Just a moment"、"Enable JavaScript"、"403 Forbidden"，或者是乱码，或者内容极短且与标题无关 → 你必须且只能输出 [JUNK]，绝不允许强行编造。
2. 禁止八股开头："本文介绍了"、"这篇文章讲述了"、"该文探讨了" 等一律禁止。
3. 第一句：直接点明「谁/哪家公司 + 做了什么」。尽可能写出具体人名/公司名，避免用「作者」「该团队」等模糊指代。
4. 第二句：说明「为什么重要/行业影响」。
5. 术语保留英文（Agent, LLM, API, FPGA, CLI）。
6. 直接输出摘要，不要前缀。"""
        max_tokens = 256
    
    url = f"{GEMINI_API_URL}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": max_tokens
        }
    }
    
    try:
        response = httpx.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        if not result:
            return ""
        
        result = result.strip()
        
        # [JUNK] 熔断：AI 自己检测到垃圾内容
        if "[JUNK]" in result:
            print(f"    🚧 [JUNK] AI 检测到垃圾内容: {title[:30]}...")
            if _depth >= 1:
                # 二次降级仍判 JUNK，放弃以免无限递归 + 烧 API
                return ""
            # 降级为标题推断（递归，无内容模式）
            return generate_news_brief(title, "", category, _depth=_depth + 1)

        return result
    except Exception:
        logger.exception("generate_news_brief 失败")
        return ""


def expand_product_tagline(name: str, tagline: str) -> str:
    """
    将 Product Hunt 英文 tagline 扩展为中文产品定位描述（30-60字）。
    Ported from the companion PWA frontend's product tagline expansion logic.
    
    Args:
        name: 产品名称
        tagline: 英文 tagline
    
    Returns:
        中文产品描述（30-60字），失败则返回空字符串
    """
    if not GEMINI_API_KEY or not name:
        return ""
    
    prompt = f"""这是一个新产品：
名称：{name}
标语：{tagline or '(无)'}

请用一句自然中文描述这个产品的定位和卖点（30-60字）。直接输出，不要前缀。"""
    
    url = f"{GEMINI_API_URL}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 128
        }
    }
    
    try:
        response = httpx.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return result.strip() if result else ""
    except Exception:
        logger.exception("expand_product_tagline 失败")
        return ""


if __name__ == "__main__":
    # Test translation
    test_text = "Adapting large pretrained models to new tasks efficiently and continually is crucial for real-world deployment but remains challenging due to catastrophic forgetting."
    print("原文:", test_text)
    print("翻译:", translate_to_chinese(test_text, 80))
