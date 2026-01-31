import os
import sys
import glob
import json
import httpx
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Force UTF-8 stdout for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
# Try multiple locations for .env
ENV_PATHS = [
    Path("d:/Skills/Roles/Commercial_Agent/.env"),
    Path(".env")
]
for p in ENV_PATHS:
    if p.exists():
        load_dotenv(p)

# Global Config
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1/chat/completions")
MODEL_NAME = os.getenv("XAI_MODEL", "grok-beta")

# Paths
INTEL_DIR = Path("d:/Intel_Briefing/reports/daily_briefings")
OUTPUT_DIR = Path("d:/Intel_Briefing/reports/opportunities")
SKILL_PROMPT_PATH = Path("d:/Intel_Briefing/.agent/skills/revenue-architect/prompts/commercial_logic.md")

def query_llm(system_prompt: str, user_input: str) -> str:
    """Send request to LLM via Relay/Official API."""
    if not XAI_API_KEY:
        return "❌ Error: XAI_API_KEY not found."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XAI_API_KEY}"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "stream": False,
        "temperature": 0.5
    }

    try:
        # verify=False to handle potential proxy SSL interception issues
        response = httpx.post(XAI_BASE_URL, headers=headers, json=payload, timeout=90, verify=False)
        response.raise_for_status()
        
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ LLM Call Failed: {e}"

def get_latest_briefing() -> Path:
    """Find the most recent Daily Briefing markdown file."""
    # Pattern: Morning_Report_*.md and Weekly_Report_*.md
    files = list(INTEL_DIR.glob("*_Report_*.md"))
    if not files:
        return None
    # Sort by name (which contains date) descending
    files.sort(key=lambda x: x.name, reverse=True)
    return files[0]

def run_revenue_architect(test_mode: bool = False):
    print("🏗️ Revenue Architect: Initializing...")
    
    # 1. Get Input Data
    if test_mode:
        print("🧪 TEST MODE: Using Mock Data")
        intel_content = """
        # Daily Briefing Mock Data (Expanded for Testing)
        
        ## 1. DeepSeek-V3 API Released
        DeepSeek has released their V3 model API. It is claimed to be 50% cheaper than GPT-4o while offering comparable performance on coding tasks. 
        The context window is 128k tokens. Developers are flocking to it for building low-cost agents.
        
        ## 2. OpenAI Search Goes Paid
        OpenAI has moved their 'SearchGPT' feature behind the Plus paywall effectively. This creates a gap for free, ad-supported search wrappers or niche search tools.
        
        ## 3. Cursor Editor Plugins
        The Cursor AI code editor is seeing a massive surge in plugin development. Users are asking for 'Voice Coding' and 'Figma to Cursor' bridges.
        
        ## 4. Solana Agent Frameworks
        New frameworks for deploying AI agents on Solana are trending. 'Eliza' framework allows agents to hold wallets and trade tokens autonomously.
        
        ## 5. Super-Individual Trends
        More designers are using 'Midjourney + Runway' to create full short films alone. The tooling is ready for 'One Person Netflix'.
        """
        date_str = "TEST_RUN"
    else:
        briefing_file = get_latest_briefing()
        if not briefing_file:
            print("❌ No briefing reports found in:", INTEL_DIR)
            return

        print(f"📄 Reading Intelligence: {briefing_file.name}")
        intel_content = briefing_file.read_text(encoding='utf-8')
        date_str = datetime.date.today().strftime("%Y-%m-%d")

    # 2. Circuit Breaker
    if len(intel_content) < 200:
        print("⚠️ Intel too sparse (<200 chars). Skipping execution.")
        return

    # 3. Load Skill Brain
    if not SKILL_PROMPT_PATH.exists():
        print(f"❌ Skill Prompt not found at: {SKILL_PROMPT_PATH}")
        return
    
    system_prompt = SKILL_PROMPT_PATH.read_text(encoding='utf-8')

    # 4. Execute
    print(f"🧠 Analyzing Intel with Model: {MODEL_NAME}...")
    mission_plan = query_llm(
        system_prompt=system_prompt,
        user_input=f"Here is the latest Intelligence Report. Identify actionable Antigravity Missions:\n\n{intel_content}"
    )
    
    # 5. Output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("--- RAW LLM RESPONSE START ---")
    print(mission_plan)
    print("--- RAW LLM RESPONSE END ---")
    
    if "NO OPPORTUNITY DETECTED" in mission_plan:
        print("💤 Revenue Architect found no opportunities today.")
        return

    output_file = OUTPUT_DIR / f"{date_str}_Mission_Plan.md"
    output_file.write_text(mission_plan, encoding='utf-8')
    
    print("\n" + "="*50)
    print(f"✅ Mission Plan Generated: {output_file}")
    print("="*50)
    print("👉 ACTION: Open the file and copy the 'Antigravity Execution Prompts'.")

if __name__ == "__main__":
    if "--test" in sys.argv:
        run_revenue_architect(test_mode=True)
    else:
        run_revenue_architect()
