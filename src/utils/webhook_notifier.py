"""
Webhook Notifier - 推送报告到企业微信/飞书/Slack
支持多种 Webhook 格式，自动适配不同平台
"""
import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

# 从环境变量读取 Webhook URL
WECOM_WEBHOOK_URL = os.getenv("WECOM_WEBHOOK_URL", "")  # 企业微信
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")  # 飞书
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")  # Slack
DINGTALK_WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK_URL", "")  # 钉钉

WEBHOOK_TIMEOUT = 30


def send_to_wecom(content: str, title: str = "📊 今日情报简报") -> bool:
    """发送到企业微信群机器人"""
    if not WECOM_WEBHOOK_URL:
        logger.debug("WECOM_WEBHOOK_URL 未配置，跳过企业微信推送")
        return False

    # 企业微信 markdown 消息格式
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"## {title}\n\n{content}"
        }
    }

    try:
        response = httpx.post(WECOM_WEBHOOK_URL, json=payload, timeout=WEBHOOK_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("errcode") == 0:
                logger.info("✅ 企业微信推送成功")
                return True
            else:
                logger.warning(f"企业微信推送失败: {data.get('errmsg')}")
                return False
        else:
            logger.warning(f"企业微信推送失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"企业微信推送异常: {e}")
        return False


def send_to_feishu(content: str, title: str = "📊 今日情报简报") -> bool:
    """发送到飞书群机器人"""
    if not FEISHU_WEBHOOK_URL:
        logger.debug("FEISHU_WEBHOOK_URL 未配置，跳过飞书推送")
        return False

    # 飞书富文本消息格式
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": content
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
            else:
                logger.warning(f"飞书推送失败: {data.get('msg')}")
                return False
        else:
            logger.warning(f"飞书推送失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"飞书推送异常: {e}")
        return False


def send_to_slack(content: str, title: str = "📊 Today's Intel Briefing") -> bool:
    """发送到 Slack Webhook"""
    if not SLACK_WEBHOOK_URL:
        logger.debug("SLACK_WEBHOOK_URL 未配置，跳过 Slack 推送")
        return False

    # Slack Block Kit 格式
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": content
                }
            }
        ]
    }

    try:
        response = httpx.post(SLACK_WEBHOOK_URL, json=payload, timeout=WEBHOOK_TIMEOUT)
        if response.status_code == 200:
            logger.info("✅ Slack 推送成功")
            return True
        else:
            logger.warning(f"Slack 推送失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Slack 推送异常: {e}")
        return False


def send_to_dingtalk(content: str, title: str = "📊 今日情报简报") -> bool:
    """发送到钉钉群机器人"""
    if not DINGTALK_WEBHOOK_URL:
        logger.debug("DINGTALK_WEBHOOK_URL 未配置，跳过钉钉推送")
        return False

    # 钉钉 markdown 消息格式
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": f"## {title}\n\n{content}"
        }
    }

    try:
        response = httpx.post(DINGTALK_WEBHOOK_URL, json=payload, timeout=WEBHOOK_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get("errcode") == 0:
                logger.info("✅ 钉钉推送成功")
                return True
            else:
                logger.warning(f"钉钉推送失败: {data.get('errmsg')}")
                return False
        else:
            logger.warning(f"钉钉推送失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"钉钉推送异常: {e}")
        return False


def extract_summary_for_webhook(report_content: str, max_length: int = 2000) -> str:
    """
    从完整报告中提取适合 Webhook 推送的摘要。
    保留 Executive Summary + 各板块前2条。
    """
    lines = report_content.split("\n")
    summary_lines = []
    current_section = None
    section_item_count = 0
    in_executive_summary = False

    for line in lines:
        # 保留标题和日期
        if line.startswith("# ") or line.startswith("**日期"):
            summary_lines.append(line)
            continue

        # Executive Summary 全部保留
        if "今日要点" in line or "Executive Summary" in line:
            in_executive_summary = True
            summary_lines.append(line)
            continue

        if in_executive_summary:
            if line.startswith("## "):
                in_executive_summary = False
            else:
                summary_lines.append(line)
                continue

        # 各板块只保留标题和前2条
        if line.startswith("## "):
            current_section = line
            section_item_count = 0
            summary_lines.append("")
            summary_lines.append(line)
            continue

        if line.startswith("### ") and current_section:
            section_item_count += 1
            if section_item_count <= 2:
                summary_lines.append(line)

        # 保留条目的元信息行（📍开头）
        if line.startswith("📍") and section_item_count <= 2:
            summary_lines.append(line)

    result = "\n".join(summary_lines)

    # 截断过长内容
    if len(result) > max_length:
        result = result[:max_length] + "\n\n... [查看完整报告]"

    return result


def notify_all(report_content: str, date_str: str) -> dict:
    """
    推送报告到所有已配置的 Webhook。

    Args:
        report_content: 完整的 Markdown 报告内容
        date_str: 日期字符串

    Returns:
        各平台推送结果 {"wecom": True/False, "feishu": True/False, ...}
    """
    title = f"📊 情报简报 {date_str}"
    summary = extract_summary_for_webhook(report_content)

    results = {
        "wecom": send_to_wecom(summary, title),
        "feishu": send_to_feishu(summary, title),
        "slack": send_to_slack(summary, title),
        "dingtalk": send_to_dingtalk(summary, title),
    }

    success_count = sum(1 for v in results.values() if v)
    if success_count > 0:
        logger.info(f"Webhook 推送完成: {success_count} 个平台成功")
    else:
        logger.debug("未配置任何 Webhook，跳过推送")

    return results


__all__ = [
    'send_to_wecom',
    'send_to_feishu',
    'send_to_slack',
    'send_to_dingtalk',
    'notify_all',
]
