import schedule
import time
import os
import subprocess
from datetime import datetime

def run_spider():
    print(f"🕷️ Starting scraper job at {datetime.now()}")
    # This runs the same command you were typing manually
    # 'check=True' ensures we catch errors if the scraper crashes
    try:
        subprocess.run(["scrapy", "crawl", "tata_1mg"], check=True)
        print("✅ Scrape finished successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running scraper: {e}")

# 1. Schedule the job (e.g., every 6 hours)
schedule.every(6).hours.do(run_spider)

# 2. Run it once immediately when the container starts (so you don't have to wait 6 hours to test it)
print("🚀 Scheduler started. Running initial job...")
run_spider()

# 3. Keep the script running forever
while True:
    schedule.run_pending()
    time.sleep(1)