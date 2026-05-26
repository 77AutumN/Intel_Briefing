"""
Monthly Data Condensation Script
Usage: python condense_month.py [YYYY-MM]
  If no argument provided, defaults to current month.

Pipeline: daily_briefings/*.md → YYYY-MM_Condensed.txt
Note: Mission Plans are EXCLUDED per pipeline isolation policy.
      Monthly report = daily reports + weekly reports only.

Key feature: Every extracted signal line carries [MM-DD][Source] metadata tags
so the downstream ToT engine can compute signal frequency and cross-source correlation.

Real daily report structure:
  ## 🛠️ 技术趋势 (Tech Trends)    ← section header (sets source context)
  > Hacker News + GitHub Trending   ← section sub-source hint
  ### 1. [Title](url)               ← signal title (KEY: extract)
  > ⚡ one-liner summary            ← signal brief (KEY: extract)  
  📍 Hacker News | 🔥 99 points    ← source + engagement (KEY: extract)
  **详情:** long analysis...        ← detail block (SKIP: too verbose)
"""
import glob
import os
import re
import sys
from datetime import datetime

# Maps inline source markers to short tags
SOURCE_MARKERS = {
    'Hacker News': 'HN',
    'Product Hunt': 'PH',
    'arXiv': 'arXiv',
    'TechCrunch': 'TC',
    'MIT Technology Review': 'MIT',
    'MIT Tech': 'MIT',
    'GitHub': 'GitHub',
    'Grok': 'X/Grok',
    'X (Twitter)': 'X',
    'X/Twitter': 'X',
    'V2EX': 'V2EX',
    '小红书': 'XHS',
    'XHS': 'XHS',
    'Crunchbase': 'CB',
    '华尔街': 'WSJ',
    'WallStreetCN': 'WSJ',
    '36Kr': '36Kr',
    'Blog': 'Blog',
    'HN Top Blogs': 'Blog',
    '学术': 'Research',
    'Research': 'Research',
    'ArXiv': 'arXiv',
    '融资': 'Finance',
    'Finance': 'Finance',
    '社区': 'Community',
    'Community': 'Community',
}

# Section header emoji patterns → source context
SECTION_SOURCE_MAP = {
    '技术趋势': 'HN',
    'Tech Trends': 'HN',
    '资本动向': 'CB',
    'Capital Flow': 'CB',
    '学术前沿': 'arXiv',
    'Research': 'arXiv',
    '产品精选': 'PH',
    'Product Gems': 'PH',
    '社交热议': 'X',
    'Social': 'X',
    '社区热点': 'V2EX',
    'Community': 'V2EX',
    '小红书雷达': 'XHS',
    'XHS Radar': 'XHS',
    '深度洞察': 'Blog',
    'Insights': 'Blog',
}


def detect_source_from_section(line: str) -> str:
    """Detect source from a ## section header."""
    for marker, tag in SECTION_SOURCE_MAP.items():
        if marker in line:
            return tag
    return ''


def detect_source_inline(line: str) -> str:
    """Detect source from a 📍 source indicator line."""
    for marker, tag in SOURCE_MARKERS.items():
        if marker in line:
            return tag
    return ''


def get_target_month():
    if len(sys.argv) > 1:
        try:
            datetime.strptime(sys.argv[1], "%Y-%m")
            return sys.argv[1]
        except ValueError:
            print(f"Error: Invalid format '{sys.argv[1]}'. Use YYYY-MM.")
            sys.exit(1)
    else:
        return datetime.now().strftime("%Y-%m")


def condense(month: str):
    pattern = f"D:/Intel_Briefing/reports/daily_briefings/Morning_Report_{month}-*.md"
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"No daily reports found for {month}.")
        print(f"Pattern: {pattern}")
        sys.exit(1)

    out_dir = "D:/Intel_Briefing/reports/condensed_data"
    os.makedirs(out_dir, exist_ok=True)

    output = []
    output.append(f"# {month} Condensed Intelligence Data\n")
    output.append(f"Source: {len(files)} daily reports")
    output.append(f"Generated: {datetime.now().isoformat()}")
    output.append(f"Pipeline: daily_briefings → condense_month.py (Mission Plans excluded)")
    output.append(f"Signal format: [MM-DD][Source] content\n")
    output.append("---\n")

    total_signals = 0

    for f in files:
        match = re.search(rf'{month}-(\d{{2}})', f)
        day = match.group(1) if match else "??"
        date_tag = f"{month.split('-')[1]}-{day}"  # e.g. "03-15"
        date_str = f"{month}-{day}"
        output.append(f"\n## {date_str}\n")

        current_source = ''
        in_detail_block = False  # Track **详情:** verbose blocks
        day_signals = 0

        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                stripped = line.strip()

                # Skip empty lines
                if not stripped:
                    in_detail_block = False  # End detail block on blank line break
                    continue

                # --- SECTION HEADERS (## level) → update source context ---
                if stripped.startswith('## '):
                    detected = detect_source_from_section(stripped)
                    if detected:
                        current_source = detected
                    output.append(stripped)
                    in_detail_block = False
                    continue

                # --- DETAIL BLOCKS → skip verbose analysis paragraphs ---
                if stripped.startswith('**详情:**') or stripped.startswith('**详情:'):
                    in_detail_block = True
                    continue
                if in_detail_block:
                    # Still inside a detail block, skip unless we hit a new signal
                    if not stripped.startswith('### '):
                        continue
                    else:
                        in_detail_block = False
                        # Fall through to signal title handling below

                # --- SIGNAL TITLES (### N. [Title](url)) → KEY EXTRACT ---
                if stripped.startswith('### '):
                    tag = f"[{date_tag}][{current_source}]" if current_source else f"[{date_tag}]"
                    # Extract just the title text, not the full markdown link
                    title_match = re.search(r'\[([^\]]+)\]', stripped)
                    if title_match:
                        title = title_match.group(1)
                        output.append(f"{tag} {title}")
                    else:
                        # No link, just plain ### title
                        clean = stripped.lstrip('#').strip()
                        if clean:
                            output.append(f"{tag} {clean}")
                    day_signals += 1
                    continue

                # --- ONE-LINER BRIEF (> ⚡ ...) → KEY EXTRACT ---
                if stripped.startswith('> ⚡'):
                    tag = f"[{date_tag}][{current_source}]" if current_source else f"[{date_tag}]"
                    brief = stripped[2:].strip()  # Remove "> " prefix
                    # Truncate to first sentence or 150 chars for conciseness
                    if len(brief) > 200:
                        # Find first period/。 to cut
                        cut = -1
                        for sep in ['。', '，这', '，并', '，简直', '！', '. ']:
                            idx = brief.find(sep, 20)
                            if idx > 0 and idx < 200:
                                cut = idx + len(sep)
                                break
                        if cut > 0:
                            brief = brief[:cut].rstrip('，、。') + '...'
                        else:
                            brief = brief[:200] + '...'
                    output.append(f"  {tag} → {brief}")
                    continue

                # --- SOURCE/ENGAGEMENT LINE (📍 Hacker News | 🔥 99 pts) ---
                if '📍' in stripped:
                    # Update source from inline marker
                    inline_src = detect_source_inline(stripped)
                    if inline_src:
                        current_source = inline_src
                    # Extract engagement metrics
                    points_match = re.search(r'🔥\s*(\d+)\s*(?:points?|votes?)', stripped)
                    replies_match = re.search(r'💬\s*(\d+)\s*replies?', stripped)
                    if points_match:
                        tag = f"[{date_tag}][{current_source}]" if current_source else f"[{date_tag}]"
                        pts = points_match.group(1)
                        output.append(f"  {tag} 📊 {pts} points")
                    elif replies_match:
                        tag = f"[{date_tag}][{current_source}]" if current_source else f"[{date_tag}]"
                        rpl = replies_match.group(1)
                        output.append(f"  {tag} 💬 {rpl} replies")
                    continue

                # --- VOTE COUNT for Product Hunt (🔥 1452 votes) ---
                if stripped.startswith('🔥') and 'votes' in stripped.lower():
                    votes_match = re.search(r'(\d+)\s*votes?', stripped)
                    if votes_match:
                        tag = f"[{date_tag}][{current_source}]" if current_source else f"[{date_tag}]"
                        votes = votes_match.group(1)
                        output.append(f"  {tag} 📊 {votes} votes")
                    continue

                # --- KEY INDICATOR LINES (funding, launches, etc.) ---
                if any(kw in stripped for kw in [
                    'funding', 'raised', 'launch', 'shutdown',
                    'billion', 'million', 'valuation',
                    '融资', '估值', '裁员', '发布', '开源', '关停',
                    'Series A', 'Series B', 'Series C', 'Series D',
                    'IPO', 'acquisition', '收购', 'unicorn',
                ]):
                    if len(stripped) < 200 and not stripped.startswith('**'):
                        tag = f"[{date_tag}][{current_source}]" if current_source else f"[{date_tag}]"
                        output.append(f"{tag} {stripped}")
                    continue

                # --- CROSS-SIGNAL SYNTHESIS & HUNT TAGS ---
                if stripped.startswith('**汇聚模式') or stripped.startswith('**['):
                    tag = f"[{date_tag}][{current_source}]" if current_source else f"[{date_tag}]"
                    output.append(f"{tag} {stripped}")
                    continue

        total_signals += day_signals

    # Write output
    out_path = f"{out_dir}/{month}_Condensed.txt"
    with open(out_path, "w", encoding="utf-8") as out:
        out.write('\n'.join(output))

    print(f"✅ Condensed {len(files)} daily reports → {out_path}")
    print(f"   Total output lines: {len(output)}")
    print(f"   Total signals extracted: {total_signals}")
    print(f"   Signal format: [MM-DD][Source] content")
    print(f"   Persistent path: {out_dir}/")


if __name__ == "__main__":
    month = get_target_month()
    print(f"Condensing data for: {month}")
    condense(month)
