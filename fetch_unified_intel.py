#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unified Intelligence Fetcher - Operation Wide-Net V2
薄封装层：复用 intel_collector 和 report_generator 模块。

Sources:
- External (news-aggregator): HN, GitHub, 36Kr, WallStreetCN, V2EX
- Local: Product Hunt, ArXiv, X (Grok), XHS, HN Blogs
"""

import sys
import os
import logging
from datetime import datetime

# --- Path Setup ---
LOCAL_SRC_PATH = os.path.join(os.path.dirname(__file__), 'src')
if LOCAL_SRC_PATH not in sys.path:
    sys.path.insert(0, LOCAL_SRC_PATH)

from src.intel_collector import fetch_all_sources
from src.report_generator import generate_report
from src.config import setup_logging

logger = logging.getLogger(__name__)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Unified Intel Fetcher V2")
    parser.add_argument("--limit", type=int, default=10, help="Items per source")
    parser.add_argument("--test", action="store_true", help="Test mode (1 item per source)")
    parser.add_argument("--output", type=str, help="Custom output path")
    parser.add_argument("--log-level", type=str, default="INFO", help="Log level (DEBUG/INFO/WARNING)")
    args = parser.parse_args()

    setup_logging(level=args.log_level)

    limit = 1 if args.test else args.limit
    date_str = datetime.now().strftime("%Y-%m-%d")

    logger.info(f"Unified Intelligence Fetcher V2 | Date: {date_str} | Limit: {limit}/source")

    # Fetch
    intel = fetch_all_sources(limit_per_source=limit)

    # Generate report
    report = generate_report(intel, date_str)

    # Save
    if args.output:
        output_path = args.output
    else:
        reports_dir = os.path.join(os.path.dirname(__file__), "reports", "daily_briefings")
        os.makedirs(reports_dir, exist_ok=True)
        if args.test:
            output_path = os.path.join(reports_dir, "Morning_Report_TEST.md")
        else:
            output_path = os.path.join(reports_dir, f"Morning_Report_{date_str}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info(f"Report saved to: {output_path}")

    print(f"\n--- Preview (first 40 lines) ---\n")
    for line in report.split("\n")[:40]:
        print(line)


if __name__ == "__main__":
    main()
