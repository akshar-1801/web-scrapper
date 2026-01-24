from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        output = []
        
        # ... (URL Test Logic)
        
        # Define URLs
        url_simple_p2 = "https://www.1mg.com/categories/nutritional-drinks-196?page=2"
        
        print(f"--- Testing Simplified Page 2 URL: {url_simple_p2} ---")
        output.append(f"--- Testing Simplified Page 2 URL: {url_simple_p2} ---")
        page.goto(url_simple_p2)
        page.wait_for_selector('div[class*="VerticalProductTile__container"]', timeout=20000)
        p2_simple_name = page.eval_on_selector('div[class*="VerticalProductTile__header"]', 'el => el.innerText')
        print(f"Simple Page 2 First Product: {p2_simple_name}")
        output.append(f"Simple Page 2 First Product: {p2_simple_name}")
        
        # Test finding the Next button
        print("\n--- Searching for Pagination Controls on Page 1 ---")
        output.append("\n--- Searching for Pagination Controls on Page 1 ---")
        page.goto("https://www.1mg.com/categories/nutritional-drinks-196", wait_until="domcontentloaded")
        page.wait_for_selector('div[class*="VerticalProductTile__container"]', timeout=20000)
        
        # Get Page 1 Product again just to be sure
        p1_name = page.eval_on_selector('div[class*="VerticalProductTile__header"]', 'el => el.innerText')
        output.append(f"Page 1 First Product: {p1_name}")

        next_button = page.query_selector('ul[class*="Pagination"] li.next a')
        if not next_button:
             next_button = page.query_selector('li.next a')
        if not next_button:
             next_button = page.get_by_text("Next", exact=True)
             
        if next_button:
            print("Found 'Next' button/link!")
            output.append("Found 'Next' button/link!")
            print("Clicking Next...")
            
            # Click and wait for network idle or selector
            with page.expect_navigation(timeout=15000):
                next_button.click()
            
            page.wait_for_timeout(3000) # Wait for hydration
            
            p2_click_name = page.eval_on_selector('div[class*="VerticalProductTile__header"]', 'el => el.innerText')
            print(f"Page 2 (via Click) First Product: {p2_click_name}")
            output.append(f"Page 2 (via Click) First Product: {p2_click_name}")
            
            if p1_name == p2_click_name:
                output.append("[FAILURE] Clicking Next did NOT load new content (Duplicates).")
            else:
                output.append("[SUCCESS] Clicking Next LOADED NEW CONTENT.")
                
        else:
            print("Could not identify 'Next' button explicitly.")
            output.append("Could not identify 'Next' button explicitly.")
            
        with open("debug_result.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(output))
            
        browser.close()

if __name__ == "__main__":
    run()
