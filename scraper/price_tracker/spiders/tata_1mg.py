import scrapy
from scrapy_playwright.page import PageMethod
from ..items import PriceTrackerItem
from datetime import datetime
from scrapy.selector import Selector
import asyncio

class Tata1mgSpider(scrapy.Spider):
    name = "tata_1mg"
    allowed_domains = ["1mg.com"]
    start_urls = [
        "https://www.1mg.com/categories/nutritional-drinks-196"
    ]

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            meta={
                "playwright": True,
                "playwright_include_page": True, # Keep page open for interaction
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "div[class*='VerticalProductTile__container']"),
                    PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)"),
                    PageMethod("wait_for_timeout", 2000),
                ]
            }
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        
        try:
            total_pages = 20 # Increased limit for more products
            
            for page_num in range(1, total_pages + 1):
                self.logger.info(f"Scraping Page {page_num}...")
                
                # Scroll to bottom to ensure lazy loading triggers
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                # Get current content
                content = await page.content()
                sel = Selector(text=content)
                
                # Extract Products
                containers = sel.css('div[class*="VerticalProductTile__container"]')
                self.logger.info(f"Found {len(containers)} products on Page {page_num}")
                
                for container in containers:
                    item = PriceTrackerItem()
                    
                    # Name
                    item['name'] = container.css('div[class*="VerticalProductTile__header"]::text').get()
                    
                    # URL
                    parent_href = container.xpath('./ancestor::a/@href').get()
                    if parent_href:
                         item['url'] = response.urljoin(parent_href)
                    else:
                         child_href = container.css('a::attr(href)').get()
                         item['url'] = response.urljoin(child_href) if child_href else response.url

                    # Image
                    item['image_url'] = container.css('img[class*="VerticalProductTile__image"]::attr(src)').get()
                    
                    # Pack Size
                    pack_size_text = container.css('div[class*="VerticalProductTile__expansionDiv"] > div[class*="textSecondary"]::text').get()
                    item['pack_size'] = pack_size_text
                    
                    # Rating
                    rating_text = container.css('div[class*="RatingBadge__"]::text').get()
                    if rating_text:
                        item['rating'] = rating_text
                        rating_count_text = container.css('div[class*="RatingBadge__"] ~ div::text').get()
                        if rating_count_text:
                             item['rating_count'] = rating_count_text.replace('(', '').replace(')', '').replace(',', '').strip()
                        else:
                             item['rating_count'] = "0"
                    else:
                        item['rating'] = "0"
                        item['rating_count'] = "0"
                    
                    # Price
                    price_text = container.css('span[class*="l5Medium"]::text').get()
                    if not price_text:
                         price_text = container.css('div[class*="Price__priceTag"]::text').get()
                    
                    if price_text:
                         try:
                            clean_price = price_text.replace('₹', '').replace(',', '').strip()
                            item['price'] = float(clean_price)
                         except:
                             self.logger.warning(f"Failed to parse price: {price_text}")
                             item['price'] = 0.0
                    else:
                        item['price'] = 0.0
                    
                    item['scraped_at'] = datetime.now().isoformat()
                    
                    yield item

                # Click Next if not last page
                if page_num < total_pages:
                    try:
                        # Capture first product name to verify change
                        first_product_name = None
                        try:
                            first_product_handle = await page.query_selector('div[class*="VerticalProductTile__header"]')
                            if first_product_handle:
                                first_product_name = await first_product_handle.inner_text()
                        except:
                            self.logger.warning("Could not capture first product name for verification.")

                        # Try multiple selectors for "Next" button
                        next_button = await page.query_selector('ul[class*="Pagination"] li.next a')
                        if not next_button:
                             next_button = await page.query_selector('li.next a') # Fallback
                        if not next_button:
                             # Use Locator for text match, but need element handle for consistency or just click it
                             next_locator = page.get_by_text("Next", exact=True)
                             if await next_locator.count() > 0:
                                 next_button = next_locator.first
                        
                        if next_button:
                            self.logger.info("Clicking Next button...")
                            await next_button.click()
                            
                            # Wait for content change
                            if first_product_name:
                                self.logger.info(f"Waiting for content to change from '{first_product_name}'...")
                                try:
                                    # Escape quotes in the name for JS string
                                    safe_name = first_product_name.replace("'", "\\'").replace('"', '\\"')
                                    await page.wait_for_function(
                                        f"document.querySelector('div[class*=\"VerticalProductTile__header\"]').innerText !== '{safe_name}'",
                                        timeout=10000
                                    )
                                    self.logger.info("Content change detected.")
                                except Exception as e:
                                    self.logger.warning(f"Timeout waiting for content change: {e}")
                            else:
                                await page.wait_for_timeout(4000) 
                            
                            # Additional stability wait
                            await page.wait_for_selector("div[class*='VerticalProductTile__container']")
                        else:
                            self.logger.info("No Next button found. Stopping.")
                            break
                    except Exception as e:
                        self.logger.error(f"Error clicking next: {e}")
                        break
                        
        finally:
            await page.close()
