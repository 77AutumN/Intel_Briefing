#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Intel Briefing CLI - 命令行入口
Unified Intelligence Fetcher V2

从 fetch_unified_intel.py 重构而来
"""

import sys
import os
import argparse
from datetime import datetime

# Add src to path for modular imports
SRC_PATH = os.path.join(os.path.dirname(__file__), 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from src.intel_collector import fetch_all_sources
from src.report_generator import generate_report


def main():
    parser = argparse.ArgumentParser(description="Unified Intel Fetcher V2")
    parser.add_argument("--limit", type=int, default=10, help="Items per source")
    parser.add_argument("--test", action="store_true", help="Test mode (1 item per source)")
    parser.add_argument("--output", type=str, help="Custom output path")
    args = parser.parse_args()
    
    limit = 1 if args.test else args.limit
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n{'='*50}")
    print(f"  Unified Intelligence Fetcher V2")
    print(f"  Date: {date_str} | Limit: {limit}/source")
    print(f"  Sources: HN, GitHub, 36Kr, WS, V2EX, PH, ArXiv, X, XHS")
    print(f"{'='*50}\n")
    
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
    
    print(f"\n[SUCCESS] Report saved to: {output_path}")
    
    print(f"\n--- Preview (first 40 lines) ---\n")
    for line in report.split("\n")[:40]:
        print(line)


if __name__ == "__main__":
    main()
