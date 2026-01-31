
import httpx
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional
import sys
import re
import time
import random

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

@dataclass
class ChromeAssetOpportunity:
    name: str
    url: str
    rating: float
    user_count_str: str
    user_count_val: int
    description: str
    kill_shot: str  # The "Desperation Summary" from bad reviews

class ChromeRadar:
    """
    Scans Chrome Web Store for "Ugly Cash Cows": High Users (>5000) + Low Rating (<3.8).
    Extracts "Kill Shot" insights from 1-star reviews.
    """
    
    # Target Categories for "SaaS Assets"
    CATEGORIES = {
        "workflow": "https://chromewebstore.google.com/category/extensions/productivity/workflow",
        "developer": "https://chromewebstore.google.com/category/extensions/productivity/developer_tools",
    }
    
    MIN_USERS = 5000
    MAX_RATING = 3.8
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        self.client = httpx.Client(headers=self.headers, timeout=20.0, follow_redirects=True)

    def scan_opportunities(self, limit: int = 3) -> List[ChromeAssetOpportunity]:
        print(f"🛒 Scanning Chrome Web Store for 'Ugly Cash Cows'...")
        opportunities = []
        
        for cat_name, url in self.CATEGORIES.items():
            print(f"  - Scanning category: {cat_name}...")
            try:
                response = self.client.get(url)
                soup = BeautifulSoup(response.content, "html.parser")
                
                # Based on Browser Agent Analysis:
                # Card: a.UvhDdd
                # Name: div.XunS9e
                # Rating: span.V979hc
                
                cards = soup.select("a.UvhDdd")
                print(f"    Found {len(cards)} items.")
                
                for card in cards:
                    try:
                        name_tag = card.select_one("div.XunS9e")
                        rating_tag = card.select_one("span.V979hc")
                        href = card.get("href")
                        
                        if not name_tag or not href or not rating_tag:
                            continue
                            
                        name = name_tag.get_text(strip=True)
                        rating_str = rating_tag.get_text(strip=True)
                        full_url = "https://chromewebstore.google.com" + href if href.startswith("/") else href
                        
                        try:
                            rating = float(rating_str)
                        except ValueError:
                            continue
                            
                        # Filter 1: Low Rating Requirement
                        if rating > self.MAX_RATING:
                            continue
                            
                        print(f"    🔍 Checking weak target: {name} ({rating}⭐)...")
                        
                        # Deep Dive: Check User Count on Detail Page
                        user_count_str, user_cnt, kill_shot = self._inspect_detail_page(full_url)
                        
                        # Filter 2: High User Count Requirement
                        if user_cnt >= self.MIN_USERS:
                            opp = ChromeAssetOpportunity(
                                name=name,
                                url=full_url,
                                rating=rating,
                                user_count_str=user_count_str,
                                user_count_val=user_cnt,
                                description="High traffic, low satisfaction.",
                                kill_shot=kill_shot
                            )
                            opportunities.append(opp)
                            print(f"    💎 FOUND GEM: {name} ({user_count_str} users, {rating} stars)")
                            
                            if len(opportunities) >= limit:
                                return opportunities
                                
                        # Polite delay
                        time.sleep(random.uniform(0.5, 1.5))
                        
                    except Exception as e:
                        print(f"    ⚠️ Error parsing card: {e}")
                        continue
                        
            except Exception as e:
                print(f"  ❌ Error scanning category {cat_name}: {e}")
                
        return opportunities

    def _inspect_detail_page(self, url: str) -> (str, int, str):
        """
        Visits the extension detail page to get User Count and 1-Star Reviews.
        """
        try:
            response = self.client.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 1. Get User Count
            # Look for text like "10,000+ users" or "200 users"
            # It's usually in a span or div with class 'F9iSGe' (from analysis) or just regex
            text_content = soup.get_text()
            user_count_match = re.search(r'([\d,]+)\+\s*users', text_content)
            
            if not user_count_match:
                 # Try finding just "users" number
                 user_count_match = re.search(r'([\d,]+)\s*users', text_content)

            user_count_str = "0"
            user_cnt = 0
            
            if user_count_match:
                user_count_str = user_count_match.group(1)
                user_cnt = int(user_count_str.replace(",", ""))
            
            # 2. Get "Kill Shot" (1-Star Reviews)
            # Chrome Store reviews are complex to scrape via static HTML (often dynamic).
            # We will grab specific review text if visible, or infer from 'Reviews' tab content if exposed.
            # NOTE: Static scraping of reviews is notoriously hard on Chrome Store.
            # Strategy: Look for specific critique keywords in the description or exposed review snippets.
            # Fallback: Just return a prompt for the user to check.
            
            # IMPROVEMENT: Try to find review containers.
            # If standard scraping fails, we return a instruction.
            kill_shot = "Auto-analysis of reviews requires browser automation. Please manually check the 'Reviews' tab and filter by 1-star."
            
            return user_count_str, user_cnt, kill_shot
            
        except Exception as e:
            # print(f"    Error inspecting detail page: {e}")
            return "0", 0, ""

if __name__ == "__main__":
    radar = ChromeRadar()
    opps = radar.scan_opportunities(limit=3)
    for opp in opps:
        print(f"💎 GEM: {opp.name}")
        print(f"   Stats: {opp.rating}⭐ | {opp.user_count_str} Users")
        print(f"   URL: {opp.url}")
        print(f"   Kill Shot: {opp.kill_shot}")
        print("-" * 40)
