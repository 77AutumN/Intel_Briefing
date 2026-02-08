"""
Gemini Translator - 使用 Gemini API 翻译文本为中文
用于将 ArXiv 论文摘要翻译成简体中文
"""
import os
import sys
import httpx
from dotenv import load_dotenv

# Force UTF-8 stdout for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
MODEL_NAME = "gemini-2.5-flash-lite"  # 轻量级模型，免费额度充足（有效期至2026年7月）

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
        print("    ⚠️ GEMINI_API_KEY 未配置，跳过翻译")
        return text[:max_chars] + "..." if len(text) > max_chars else text
    
    if not text or len(text) < 10:
        return text
    
    prompt = f"""请将以下学术论文摘要完整翻译成简体中文，要求：
1. 保持学术风格，用词精准
2. 完整翻译全部内容，不要省略任何信息
3. 只输出翻译结果，不要添加任何解释

原文：
{text}"""

    url = f"{GEMINI_API_URL}/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024  # 增加到1024以支持完整摘要翻译
        }
    }
    import time
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = httpx.post(url, json=payload, timeout=60)  # 增加到60秒
            response.raise_for_status()
            
            data = response.json()
            result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            
            if result:
                return result.strip()
            else:
                # API 返回空结果，重试
                if attempt < max_retries - 1:
                    print(f"    ⚠️ Gemini 返回空结果，重试 ({attempt + 1}/{max_retries})...")
                    time.sleep(2 ** attempt)  # 指数退避: 1s, 2s, 4s
                    continue
                return text[:max_chars] + "..." if len(text) > max_chars else text
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"    ⚠️ Gemini 翻译失败 ({attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)  # 指数退避
                continue
            print(f"    ❌ Gemini 翻译最终失败: {e}")
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
    
    url = f"{GEMINI_API_URL}/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": max_tokens
        }
    }
    
    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                result = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return result.strip() if result else ""
            else:
                print(f"    ⚠️ Gemini 摘要失败: HTTP {response.status_code}")
                return ""
    except Exception as e:
        print(f"    ⚠️ Gemini 摘要出错: {e}")
        return ""


if __name__ == "__main__":
    # Test translation
    test_text = "Adapting large pretrained models to new tasks efficiently and continually is crucial for real-world deployment but remains challenging due to catastrophic forgetting."
    print("原文:", test_text)
    print("翻译:", translate_to_chinese(test_text, 80))
