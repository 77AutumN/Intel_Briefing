
import sys
import os
import datetime

# Add sensors path
# Add sensors path
sys.path.append(os.path.join(os.path.dirname(__file__), "src", "sensors"))
# Add src path for utils
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

try:
    from x_grok_sensor import fetch_grok_intel
    from utils.verifier import verify_link
except ImportError as e:
    print(f"❌ Error importing sensors/utils: {e}")
    sys.exit(1)

import re

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def run_alpha_scan():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"🛰️ Alpha Radar Initiated: {today}")
    
    # "Code Hunter" Prompt - The "Noise Filter" logic
    prompt = """
    Search X (Twitter) for the latest OPEN SOURCE code releases related to 'Solana' AND 'AI Agent' OR 'Trading Bot'.
    
    🛑 STRICT NOISE FILTER (IGNORE THESE):
    - EXCLUDE "Airdrop", "Claim", "Whitelist", "Giveaway", "Presale", "Memecoin".
    - EXCLUDE generic news or price prediction threads.
    
    ✅ FINGERPRINT (LOOK FOR THESE):
    - Must contain "GitHub" link or mention "Open Source".
    - Keywords: "bot", "sniper", "script", "automation", "py", "rust", "repo", "cliff".
    
    OUTPUT FORMAT (Markdown in Simplified Chinese):
    For each valid finding (max 3), provide:
    1. **Project Name**: [Name]
    2. **GitHub Link**: [Link if found, or 'Search GitHub for X']
    3. **Wrapper Potential (1-10)**: 
       - 10 = CLI tool that is hard for normal people (Perfect for wrapping).
       - 1 = Already has a GUI or is just a library.
    4. **One-Line Pitch**: Why can we sell this as a tool?
    
    If no *code* is found, plainly state: "No Alpha Code found today."
    """
    
    print("  ...Transmitting 'Code Hunter' parameters to Grok...")
    
    report_content = fetch_grok_intel("Solana AI Agent GitHub", override_prompt=prompt)
    
    # ---------------------------------------------------------
    # 🕵️‍♂️ Anti-Hallucination Layer (Verification)
    # ---------------------------------------------------------
    print("\n🕵️‍♂️ Verifying Intelligence Sources...")
    
    def verify_match(match):
        text = match.group(1)
        url = match.group(2)
        
        # Skip internal links or non-http
        if not url.startswith("http"):
            return match.group(0)
            
        print(f"  --> Checking: {url} ...", end="", flush=True)
        is_valid = verify_link(url)
        
        if is_valid:
            print(" ✅ OK")
            return match.group(0) # Keep original
        else:
            print(" ❌ DEAD LINK")
            return f"[{text}]({url}) **(⚠️ 自动核实: 链接无效/404)**"
            
    # Regex to find markdown links: [text](url)
    report_content = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', verify_match, report_content)
    # ---------------------------------------------------------

    # Save Report
    filename = os.path.join(os.path.dirname(__file__), "reports", "web3", f"Alpha_Leak_{today}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# ⛏️ Web3 Tooling Dept: Alpha Leak ({today})\n\n")
        f.write("> **Mission**: Find 'Ugly Code' (CLI/Scripts) to Wrap & Sell.\n\n")
        f.write(report_content)
        
    print(f"✅ Alpha report generated: {filename}")

if __name__ == "__main__":
    run_alpha_scan()
