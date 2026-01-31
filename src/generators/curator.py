"""
Curator - The Intelligence Analyst.
Generates structured commercial insights from technical raw data.
"""
import os
import sys
import argparse
# import yaml # Config optional for now

def generate_analyst_prompt(repo_name: str, readme_text: str) -> str:
    """Construct the Analyst Prompt demanding Chinese output."""
    
    prompt = f"""
You are a **Senior Technology Intelligence Analyst** (高级技术情报分析师).
Your job is to read technical documentation and produce a **concise commercial briefing**.

# CORE MANDATE
**ALL OUTPUT MUST BE IN SIMPLIFIED CHINESE (简体中文).**

# THE SUBJECT
Repository: {repo_name}
Context: {readme_text[:3000]}... (truncated)

# ANALYSIS FRAMEWORK (Please fill this structure)

## 1. 核心价值 (Core Value)
用一句话概括：这个项目究竟解决了什么痛点？(What painful problem does it solve?)

## 2. 技术亮点 (Key Innovation)
它稍微详细一点的技术原理是什么？相比竞品有什么“护城河”？

## 3. 商业/应用潜力 (Opportunity)
哪些人会为了这个东西付费？或者它能被用在哪些商业场景里？
(e.g., SaaS集成, 企业提效, 独立开发者工具)

## 4. 风险提示 (Risks)
(e.g., 维护停滞, 依赖过于复杂, 法律版权风险)

## 5. 信息来源 (Sources)
列出你引用的主要信息来源，格式如下:
- **Repository**: https://github.com/{repo_name}
- **README 原文**: (摘录你引用的关键段落)

## 6. 社交验证 (Social Proof)
**Maker Reputation Check**:
- **Who made this?** (Identify the creator/team)
- **Track Record**: (Do they have previous successful projects?)
- **Social Momentum**: (Are key influencers discussing this? Mention specific names/handles if available in context)

# STYLE GUIDE
- Professional, objective, insightful.
- Use bullet points for readability.
- No marketing fluff.
- **CRITICAL**: Every claim must be traceable to the source material.
"""
    return prompt

def main():
    parser = argparse.ArgumentParser(description="Curator Intelligence Generator")
    parser.add_argument("--repo-name", required=True, help="Name of the repo")
    parser.add_argument("--readme", required=True, help="Path to README file")
    parser.add_argument("--output", default="briefing.md", help="Output filename")
    
    args = parser.parse_args()
    
    # 1. Target Directory (Intel Briefing Room)
    # Ideally should be passed in, but hardcoding for MVP alignment with new strategy
    STUDIO_PATH = r"D:\Intel_Briefing"
    
    # Check if we are physically in the right place, if not warn (or just run)
    
    # 2. Load Readme
    try:
        with open(args.readme, "r", encoding="utf-8") as f:
            readme_text = f.read()
    except Exception as e:
        print(f"Error reading readme: {e}")
        return

    # 3. Generate Prompt
    prompt = generate_analyst_prompt(args.repo_name, readme_text)
    
    # 4. Output
    # Ensure directory exists
    output_dir = os.path.join(STUDIO_PATH, "reports", "daily_briefings")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, args.output)
    print(f"🧐 Curator: Analyzing {args.repo_name}...")
    
    # Simulating LLM Call -> Save Prompt
    with open(output_path + ".prompt", "w", encoding="utf-8") as f:
        f.write(prompt)
        
    print(f"✅ Intelligence Briefing Query generated at: {output_path}.prompt")
    print("👉 ACTION: Submit this query to the LLM to get the Chinese report.")

if __name__ == "__main__":
    main()
