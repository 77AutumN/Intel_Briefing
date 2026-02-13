import sys
import os
import argparse
import logging
import datetime

# Path setup
SRC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from src.intel_collector import fetch_all_sources
from src.report_generator import generate_report
from src.config import setup_logging

logger = logging.getLogger(__name__)

# Configuration
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "daily_briefings")


def generate_morning_report(days: int = 1):
    """
    Orchestrate the collection of intelligence using Unified Engine V2.
    Supports Daily (days=1) or Weekly/Custom (days>1) briefings.
    """
    setup_logging()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    if days == 1:
        report_title = f"每日商业情报简报: {date_str}"
        file_name = f"Morning_Report_{date_str}.md"
        limit = 15
    else:
        report_title = f"周期性情报简报 (过去 {days} 天): {date_str}"
        file_name = f"Weekly_Report_{days}Days_{date_str}.md"
        limit = 30

    report_file = os.path.join(REPORT_DIR, file_name)
    os.makedirs(REPORT_DIR, exist_ok=True)

    logger.info(f"开始生成情报简报 (Unified V2) - 周期: {days} 天, 目标: {file_name}")

    # 1. Fetch from all sources (parallelized)
    intel = fetch_all_sources(limit_per_source=limit)

    # 2. Generate Report
    body = generate_report(intel, date_str)
    final_content = f"# {report_title}\n\n" + body.replace("# 🌐 全球情报日报 (Global Intel Briefing)", "")

    # 3. Save
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(final_content)

    logger.info(f"简报已生成: {report_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成商业情报简报 (Unified V2)")
    parser.add_argument("days", nargs="?", type=int, default=1, help="分析天数 (默认: 1)")
    args = parser.parse_args()

    generate_morning_report(days=args.days)
