#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Horizon Report Generator (Local-Only)

Runs the Horizon sensor locally and outputs a Markdown report
for injection into the Mission Plan ToT pipeline.

This script is NOT part of the GitHub Actions cloud pipeline.
It runs on the commander's local machine as a separate input channel.

Usage:
    python scripts/horizon_report.py
    python scripts/horizon_report.py --limit 8
    python scripts/horizon_report.py --output reports/opportunities/.horizon_context.md
"""

import sys
import os
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sensors.horizon import fetch_horizon


def generate_horizon_report(limit: int = 10) -> str:
    """Generate a Markdown report from Horizon sensor data."""
    articles = fetch_horizon(limit=limit)

    if not articles:
        return "# Horizon Report\n\n*No data available from Horizon feeds.*\n"

    date_str = datetime.now().strftime("%Y-%m-%d")

    # Domain emoji mapping for the report (safe for UTF-8 files)
    domain_emoji = {
        "science": "\U0001f52c",        # microscope
        "philosophy": "\U0001f4d6",     # open book
        "geopolitics": "\U0001f3db\ufe0f",  # classical building
        "crossdisciplinary": "\U0001f9ec",  # dna
        "design": "\U0001f3a8",         # palette
    }

    lines = [
        f"# \U0001f52d Horizon Report ({date_str})",
        "",
        f"> Cross-domain cognitive radar | {len(articles)} signals from {len(set(a.source for a in articles))} sources",
        f"> Domains: {', '.join(sorted(set(a.domain for a in articles)))}",
        "",
        "---",
        "",
    ]

    # Group by domain
    by_domain = {}
    for a in articles:
        by_domain.setdefault(a.domain, []).append(a)

    for domain, items in by_domain.items():
        emoji = domain_emoji.get(domain, "\U0001f310")  # globe
        domain_title = {
            "science": "Science Frontier",
            "philosophy": "Philosophy & Humanities",
            "geopolitics": "Geopolitics & Economics",
            "crossdisciplinary": "Cross-Disciplinary",
            "design": "Design & Aesthetics",
        }.get(domain, domain.title())

        lines.append(f"## {emoji} {domain_title}")
        lines.append("")

        for item in items:
            lines.append(f"### [{item.title}]({item.url})")
            meta_parts = []
            if item.author:
                meta_parts.append(f"by {item.author}")
            meta_parts.append(f"via {item.source}")
            if item.pub_date:
                meta_parts.append(item.pub_date)
            lines.append(f"*{' | '.join(meta_parts)}*")
            if item.content:
                lines.append(f"\n> {item.content[:300]}")
            lines.append("")

    lines.append("---")
    lines.append(f"*Generated locally by Horizon Sensor | {datetime.now().strftime('%H:%M')}*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate local Horizon report")
    parser.add_argument("--limit", type=int, default=10, help="Max articles")
    parser.add_argument(
        "--output",
        default=os.path.join("reports", "opportunities", ".horizon_context.md"),
        help="Output file path"
    )
    args = parser.parse_args()

    report = generate_horizon_report(limit=args.limit)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    # Console-safe summary
    try:
        print(f"Horizon report saved to: {args.output}")
    except UnicodeEncodeError:
        print(f"Horizon report saved to: {args.output}")


if __name__ == "__main__":
    main()
