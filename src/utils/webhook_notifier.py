"""
Webhook Notifier - 多渠道消息推送模块
支持: 企业微信、飞书、钉钉、Slack、Telegram、Discord、Bark、Pushover、邮件、自定义Webhook
参考 OpenClaw 设计，注重用户阅读体验
"""
import os
import re
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, List
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# ============================================
# 配置项 - 从环境变量读取
# ============================================

# 国内办公平台
WECOM_WEBHOOK_URL = os.getenv("WECOM_WEBHOOK_URL", "")
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")
DINGTALK_WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK_URL", "")

# 国际平台
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# 个人推送
BARK_URL = os.getenv("BARK_URL", "")  # 格式: https://api.day.app/your_key
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY", "")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN", "")

# 邮件推送
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")
SMTP_TO = os.getenv("SMTP_TO", "")  # 多个收件人用逗号分隔

# 自定义 Webhook (通用 POST JSON)
CUSTOM_WEBHOOK_URL = os.getenv("CUSTOM_WEBHOOK_URL", "")
CUSTOM_WEBHOOK_HEADERS = os.getenv("CUSTOM_WEBHOOK_HEADERS", "")  # JSON 格式

# 报告完整链接（可选，用于在推送中附带"查看完整报告"链接）
REPORT_BASE_URL = os.getenv("REPORT_BASE_URL", "")

WEBHOOK_TIMEOUT = 30


# ============================================
# 内容格式化 - 针对不同平台优化阅读体验
# ============================================

@dataclass
class FormattedContent:
    """格式化后的推送内容"""
    title: str
    summary: str  # 纯文本摘要（用于通知预览）
    markdown: str  # Markdown 格式（用于支持富文本的平台）
    html: str  # HTML 格式（用于邮件）
    plain: str  # 纯文本格式（用于不支持富文本的平台）


def extract_executive_summary(report_content: str) -> str:
    """提取 Executive Summary 部分"""
    lines = report_content.split("\n")
    in_summary = False
    summary_lines = []

    for line in lines:
        if "今日要点" in line or "Executive Summary" in line:
            in_summary = True
            continue
        if in_summary:
            if line.startswith("## ") or line.startswith("---"):
                break
            if line.strip():
                summary_lines.append(line.strip())

    return " ".join(summary_lines)


def extract_top_items(report_content: str, items_per_section: int = 2) -> Dict[str, List[dict]]:
    """提取各板块的头条"""
    sections = {}
    current_section = None
    current_items = []

    lines = report_content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("## "):
            if current_section and current_items:
                sections[current_section] = current_items[:items_per_section]
            # 提取板块名称（去掉 emoji）
            section_name = re.sub(r'[^\w\s\u4e00-\u9fff()]', '', line).strip()
            current_section = section_name
            current_items = []
        elif line.startswith("### ") and current_section:
            # 提取标题和链接
            match = re.match(r'### \d+\. \[(.+?)\]\((.+?)\)', line)
            if match:
                title, url = match.groups()
                current_items.append({"title": title, "url": url})

    if current_section and current_items:
        sections[current_section] = current_items[:items_per_section]

    return sections


def format_for_push(report_content: str, date_str: str) -> FormattedContent:
    """
    将报告内容格式化为适合推送的多种格式。
    核心原则：简洁、易读、突出重点。
    """
    exec_summary = extract_executive_summary(report_content)
    top_items = extract_top_items(report_content, items_per_section=2)

    title = f"📊 情报简报 {date_str}"

    # 纯文本摘要（用于通知预览，限制长度）
    summary = exec_summary[:150] + "..." if len(exec_summary) > 150 else exec_summary
    if not summary:
        summary = f"{date_str} 情报简报已生成"

    # Markdown 格式 - 适合企业微信、飞书、Slack、Discord、Telegram
    md_lines = [f"## {title}", ""]

    if exec_summary:
        md_lines.append("**📌 今日要点**")
        md_lines.append(exec_summary)
        md_lines.append("")

    for section, items in top_items.items():
        if items:
            md_lines.append(f"**{section}**")
            for item in items:
                md_lines.append(f"• [{item['title']}]({item['url']})")
            md_lines.append("")

    if REPORT_BASE_URL:
        md_lines.append(f"[📖 查看完整报告]({REPORT_BASE_URL})")

    markdown = "\n".join(md_lines)

    # HTML 格式 - 适合邮件
    html_lines = [
        f"<h2>{title}</h2>",
    ]

    if exec_summary:
        html_lines.append("<h3>📌 今日要点</h3>")
        html_lines.append(f"<p>{exec_summary}</p>")

    for section, items in top_items.items():
        if items:
            html_lines.append(f"<h3>{section}</h3>")
            html_lines.append("<ul>")
            for item in items:
                html_lines.append(f'<li><a href="{item["url"]}">{item["title"]}</a></li>')
            html_lines.append("</ul>")

    if REPORT_BASE_URL:
        html_lines.append(f'<p><a href="{REPORT_BASE_URL}">📖 查看完整报告</a></p>')

    html = "\n".join(html_lines)

    # 纯文本格式 - 适合 Bark、Pushover 等
    plain_lines = [title, ""]

    if exec_summary:
        plain_lines.append("📌 今日要点:")
        plain_lines.append(exec_summary)
        plain_lines.append("")

    for section, items in top_items.items():
        if items:
            plain_lines.append(f"{section}:")
            for item in items:
                plain_lines.append(f"  • {item['title']}")
            plain_lines.append("")

    plain = "\n".join(plain_lines)

    return FormattedContent(
        title=title,
        summary=summary,
        markdown=markdown,
        html=html,
        plain=plain
    )


# ============================================
# 国内办公平台
# ============================================

def send_to_wecom(content: FormattedContent) -> bool:
    """发送到企业微信群机器人"""
    if not WECOM_WEBHOOK_URL:
        return False

    # 企业微信 Markdown 有长度限制，需要截断
    md_content = content.markdown
    if len(md_content) > 4096:
        md_content = md_content[:4000] + "\n\n... [内容过长已截断]"

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": md_content
        }
    }

    try:
        response = httpx.post(WECOM_WEBHOOK_URL, json=payload, timeout=WEBHOOK_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("errcode") == 0:
                logger.info("✅ 企业微信推送成功")
                return True
            logger.warning(f"企业微信推送失败: {data.get('errmsg')}")
        else:
            logger.warning(f"企业微信推送失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"企业微信推送异常: {e}")
    return False


def send_to_feishu(content: FormattedContent) -> bool:
    """发送到飞书群机器人 - 使用卡片消息提升阅读体验"""
    if not FEISHU_WEBHOOK_URL:
        return False

    # 飞书卡片消息，视觉效果更好
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": content.title
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": content.markdown[:2000]  # 飞书有长度限制
                }
            ]
        }
    }

    try:
        response = httpx.post(FEISHU_WEBHOOK_URL, json=payload, timeout=WEBHOOK_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0 or data.get("StatusCode") == 0:
                logger.info("✅ 飞书推送成功")
                return True
            logger.warning(f"飞书推送失败: {data.get('msg')}")
        else:
            logger.warning(f"飞书推送失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"飞书推送异常: {e}")
    return False


def send_to_dingtalk(content: FormattedContent) -> bool:
    """发送到钉钉群机器人"""
    if not DINGTALK_WEBHOOK_URL:
        return False

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": content.title,
            "text": content.markdown[:6000]  # 钉钉限制
        }
    }

    try:
        response = httpx.post(DINGTALK_WEBHOOK_URL, json=payload, timeout=WEBHOOK_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("errcode") == 0:
                logger.info("✅ 钉钉推送成功")
                return True
            logger.warning(f"钉钉推送失败: {data.get('errmsg')}")
        else:
            logger.warning(f"钉钉推送失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"钉钉推送异常: {e}")
    return False


# ============================================
# 国际平台
# ============================================

def send_to_slack(content: FormattedContent) -> bool:
    """发送到 Slack - 使用 Block Kit 提升阅读体验"""
    if not SLACK_WEBHOOK_URL:
        return False

    # Slack Block Kit 格式，支持更丰富的排版
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": content.title}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": content.markdown[:3000]}
        }
    ]

    payload = {"blocks": blocks}

    try:
        response = httpx.post(SLACK_WEBHOOK_URL, json=payload, timeout=WEBHOOK_TIMEOUT)
        if response.status_code == 200:
            logger.info("✅ Slack 推送成功")
            return True
        logger.warning(f"Slack 推送失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"Slack 推送异常: {e}")
    return False


def send_to_discord(content: FormattedContent) -> bool:
    """发送到 Discord - 使用 Embed 提升阅读体验"""
    if not DISCORD_WEBHOOK_URL:
        return False

    # Discord Embed 格式，视觉效果更好
    payload = {
        "embeds": [{
            "title": content.title,
            "description": content.markdown[:4096],  # Discord 限制
            "color": 3447003,  # 蓝色
        }]
    }

    try:
        response = httpx.post(DISCORD_WEBHOOK_URL, json=payload, timeout=WEBHOOK_TIMEOUT)
        if response.status_code in (200, 204):
            logger.info("✅ Discord 推送成功")
            return True
        logger.warning(f"Discord 推送失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"Discord 推送异常: {e}")
    return False


def send_to_telegram(content: FormattedContent) -> bool:
    """发送到 Telegram Bot"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Telegram 支持 Markdown，但语法略有不同
    # 转换链接格式: [text](url) -> [text](url) (相同)
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": content.markdown[:4096],
        "parse_mode": "Markdown",
        "disable_web_page_preview": True  # 避免链接预览干扰阅读
    }

    try:
        response = httpx.post(url, json=payload, timeout=WEBHOOK_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                logger.info("✅ Telegram 推送成功")
                return True
            logger.warning(f"Telegram 推送失败: {data.get('description')}")
        else:
            logger.warning(f"Telegram 推送失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"Telegram 推送异常: {e}")
    return False


# ============================================
# 个人推送
# ============================================

def send_to_bark(content: FormattedContent) -> bool:
    """发送到 Bark (iOS 推送)"""
    if not BARK_URL:
        return False

    # Bark URL 格式: https://api.day.app/your_key/title/body
    # 或者使用 POST JSON
    url = BARK_URL.rstrip("/")

    payload = {
        "title": content.title,
        "body": content.plain[:1000],  # Bark 推送内容不宜过长
        "group": "情报简报",
        "sound": "minuet"  # 通知声音
    }

    try:
        response = httpx.post(url, json=payload, timeout=WEBHOOK_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                logger.info("✅ Bark 推送成功")
                return True
            logger.warning(f"Bark 推送失败: {data.get('message')}")
        else:
            logger.warning(f"Bark 推送失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"Bark 推送异常: {e}")
    return False


def send_to_pushover(content: FormattedContent) -> bool:
    """发送到 Pushover"""
    if not PUSHOVER_USER_KEY or not PUSHOVER_API_TOKEN:
        return False

    url = "https://api.pushover.net/1/messages.json"

    payload = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "title": content.title,
        "message": content.plain[:1024],  # Pushover 限制
        "html": 1,  # 支持 HTML
        "priority": 0  # 正常优先级
    }

    try:
        response = httpx.post(url, data=payload, timeout=WEBHOOK_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                logger.info("✅ Pushover 推送成功")
                return True
            logger.warning(f"Pushover 推送失败: {data.get('errors')}")
        else:
            logger.warning(f"Pushover 推送失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"Pushover 推送异常: {e}")
    return False


# ============================================
# 邮件推送
# ============================================

def send_to_email(content: FormattedContent) -> bool:
    """发送邮件通知"""
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_TO]):
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = content.title
        msg["From"] = SMTP_FROM or SMTP_USER
        msg["To"] = SMTP_TO

        # 纯文本版本
        part1 = MIMEText(content.plain, "plain", "utf-8")
        # HTML 版本
        part2 = MIMEText(content.html, "html", "utf-8")

        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            recipients = [addr.strip() for addr in SMTP_TO.split(",")]
            server.sendmail(SMTP_FROM or SMTP_USER, recipients, msg.as_string())

        logger.info("✅ 邮件推送成功")
        return True
    except Exception as e:
        logger.error(f"邮件推送异常: {e}")
        return False


# ============================================
# 自定义 Webhook
# ============================================

def send_to_custom_webhook(content: FormattedContent) -> bool:
    """发送到自定义 Webhook (通用 POST JSON)"""
    if not CUSTOM_WEBHOOK_URL:
        return False

    headers = {"Content-Type": "application/json"}

    # 解析自定义 headers
    if CUSTOM_WEBHOOK_HEADERS:
        try:
            import json
            custom_headers = json.loads(CUSTOM_WEBHOOK_HEADERS)
            headers.update(custom_headers)
        except Exception:
            pass

    payload = {
        "title": content.title,
        "summary": content.summary,
        "markdown": content.markdown,
        "html": content.html,
        "plain": content.plain
    }

    try:
        response = httpx.post(
            CUSTOM_WEBHOOK_URL,
            json=payload,
            headers=headers,
            timeout=WEBHOOK_TIMEOUT
        )
        if response.status_code in (200, 201, 204):
            logger.info("✅ 自定义 Webhook 推送成功")
            return True
        logger.warning(f"自定义 Webhook 推送失败: HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"自定义 Webhook 推送异常: {e}")
    return False


# ============================================
# 统一推送入口
# ============================================

def notify_all(report_content: str, date_str: str) -> Dict[str, bool]:
    """
    推送报告到所有已配置的渠道。

    Args:
        report_content: 完整的 Markdown 报告内容
        date_str: 日期字符串

    Returns:
        各渠道推送结果
    """
    content = format_for_push(report_content, date_str)

    # 所有推送渠道
    channels = {
        "wecom": send_to_wecom,
        "feishu": send_to_feishu,
        "dingtalk": send_to_dingtalk,
        "slack": send_to_slack,
        "discord": send_to_discord,
        "telegram": send_to_telegram,
        "bark": send_to_bark,
        "pushover": send_to_pushover,
        "email": send_to_email,
        "custom": send_to_custom_webhook,
    }

    results = {}
    for name, send_func in channels.items():
        try:
            results[name] = send_func(content)
        except Exception as e:
            logger.error(f"{name} 推送异常: {e}")
            results[name] = False

    success_count = sum(1 for v in results.values() if v)
    configured_count = sum(1 for name, result in results.items() if result or _is_configured(name))

    if success_count > 0:
        logger.info(f"📤 Webhook 推送完成: {success_count}/{configured_count} 个渠道成功")
    elif configured_count == 0:
        logger.debug("未配置任何推送渠道，跳过推送")

    return results


def _is_configured(channel: str) -> bool:
    """检查渠道是否已配置"""
    config_map = {
        "wecom": bool(WECOM_WEBHOOK_URL),
        "feishu": bool(FEISHU_WEBHOOK_URL),
        "dingtalk": bool(DINGTALK_WEBHOOK_URL),
        "slack": bool(SLACK_WEBHOOK_URL),
        "discord": bool(DISCORD_WEBHOOK_URL),
        "telegram": bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
        "bark": bool(BARK_URL),
        "pushover": bool(PUSHOVER_USER_KEY and PUSHOVER_API_TOKEN),
        "email": bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD and SMTP_TO),
        "custom": bool(CUSTOM_WEBHOOK_URL),
    }
    return config_map.get(channel, False)


def get_configured_channels() -> List[str]:
    """获取已配置的推送渠道列表"""
    return [name for name in [
        "wecom", "feishu", "dingtalk", "slack", "discord",
        "telegram", "bark", "pushover", "email", "custom"
    ] if _is_configured(name)]


__all__ = [
    'notify_all',
    'get_configured_channels',
    'send_to_wecom',
    'send_to_feishu',
    'send_to_dingtalk',
    'send_to_slack',
    'send_to_discord',
    'send_to_telegram',
    'send_to_bark',
    'send_to_pushover',
    'send_to_email',
    'send_to_custom_webhook',
]
