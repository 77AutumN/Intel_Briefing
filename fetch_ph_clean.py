
import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from sensors.product_hunt import fetch_trending_products
except ImportError:
    # Handling path if running from root
    sys.path.append(os.path.join(os.getcwd(), 'd:\\Intel_Briefing\\src'))
    from sensors.product_hunt import fetch_trending_products

def main():
    print("Fetching products internally...")
    try:
        products = fetch_trending_products(10)
        
        output_path = os.path.join(os.getcwd(), 'ph_clean_list.md')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Product Hunt Live List\n\n")
            for i, p in enumerate(products, 1):
                f.write(f"### {i}. {p.name}\n")
                f.write(f"> {p.tagline}\n")
                f.write(f"- Votes: {p.votes_count}\n")
                f.write(f"- URL: {p.url}\n")
                f.write("\n")
        
        print(f"Success. Wrote to {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
