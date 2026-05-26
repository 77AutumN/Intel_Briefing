"""recurrence_scan.py — Scan Mission Plans for recurring signal tags.
Usage: python scripts/recurrence_scan.py [--days 7] [--vault D:\\Intel_Briefing]
Output: A markdown block suitable for injection into the ToT prompt.
"""
import re
import sys
import glob
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def scan(vault: Path, days: int = 7):
    cutoff = datetime.now() - timedelta(days=days)
    plans = sorted(vault.glob("reports/opportunities/*_Mission_Plan.md"))

    signal_dates = defaultdict(list)  # tag -> [dates]
    yesterday_top1 = None
    yesterday_date = None

    for plan in plans:
        match = re.match(r"(\d{4}-\d{2}-\d{2})", plan.name)
        if not match:
            continue
        plan_date = datetime.strptime(match.group(1), "%Y-%m-%d")
        if plan_date < cutoff:
            continue

        text = plan.read_text(encoding="utf-8")

        # Extract signal tags
        tags = re.findall(r"#signal/([\w-]+)", text)
        for tag in set(tags):
            signal_dates[tag].append(match.group(1))

        # Track the most recent plan's top_signal for yesterday reference
        yesterday_top1_match = re.search(r"top_signal:\s*\"?([^\"\n]+)\"?", text)
        if yesterday_top1_match:
            yesterday_top1 = yesterday_top1_match.group(1).strip()
            yesterday_date = match.group(1)

    # Sort by frequency descending
    streaks = [(tag, sorted(dates)) for tag, dates in signal_dates.items()]
    streaks.sort(key=lambda x: -len(x[1]))

    # Build output lines
    lines = []
    lines.append("<!-- RECURRENCE CONTEXT (auto-generated, do not edit) -->")

    if yesterday_top1 and yesterday_date:
        lines.append(f"前日 Top1: {yesterday_top1} (from {yesterday_date}_Mission_Plan)")
    else:
        lines.append("前日 Top1: 无历史数据")

    hot = [s for s in streaks if len(s[1]) >= 3]
    warm = [s for s in streaks if len(s[1]) == 2]

    if hot:
        lines.append("\n以下信号连续多天出现，可能存在窗口期：")
        for tag, dates in hot:
            lines.append(f"  - 🔥 #signal/{tag} — {len(dates)}天 (首次: {dates[0]})")
    if warm:
        lines.append("\n以下信号出现2次，值得留意：")
        for tag, dates in warm:
            lines.append(f"  - 📈 #signal/{tag} — {len(dates)}天")
    if not hot and not warm:
        lines.append("\n过去7天无明显信号复现。")
    lines.append("<!-- END RECURRENCE CONTEXT -->")

    return "\n".join(lines)


if __name__ == "__main__":
    vault = (
        Path(sys.argv[sys.argv.index("--vault") + 1])
        if "--vault" in sys.argv
        else Path("D:/Intel_Briefing")
    )
    days = (
        int(sys.argv[sys.argv.index("--days") + 1])
        if "--days" in sys.argv
        else 7
    )
    output_path = (
        Path(sys.argv[sys.argv.index("--output") + 1])
        if "--output" in sys.argv
        else None
    )
    result = scan(vault, days)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding="utf-8")
    else:
        print(result)
