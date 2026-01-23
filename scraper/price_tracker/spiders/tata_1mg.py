import scrapy
from datetime import datetime
from scrapy_playwright.page import PageMethod
from ..items import PriceTrackerItem

class Tata1mgSpider(scrapy.Spider):
    name = "tata_1mg"
    allowed_domains = ["1mg.com"]
    start_urls = ["https://www.1mg.com/categories/nutritional-drinks-196"]

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 2,
        'COOKIES_ENABLED': False,
        'ROBOTSTXT_OBEY': False,
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
        }
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "div[class*='VerticalProductTile__container']"),
                    PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)"),
                    PageMethod("wait_for_timeout", 2000),
                ]
            }
        )

    def parse(self, response):
        # Iterate over containers directly
        containers = response.css('div[class*="VerticalProductTile__container"]')
        self.logger.info(f"Found {len(containers)} product containers.")

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
            # Targeted selector based on structure: inside expansionDiv, child div with textSecondary
            pack_size_text = container.css('div[class*="VerticalProductTile__expansionDiv"] > div[class*="textSecondary"]::text').get()
            item['pack_size'] = pack_size_text
            
            # Rating
            rating_text = container.css('div[class*="RatingBadge__"]::text').get()
            if rating_text:
                item['rating'] = rating_text
                # Rating count usually in sibling or parenthesis
                # Snippet: <div class="xSmallRegular textSecondary RatingBadge__marginLeft8__CnSaU">(189)</div>
                rating_count_text = container.css('div[class*="RatingBadge__"] ~ div::text').get()
                if rating_count_text:
                     item['rating_count'] = rating_count_text.replace('(', '').replace(')', '').replace(',', '').strip()
                else:
                     item['rating_count'] = "0"
            else:
                item['rating'] = "0"
                item['rating_count'] = "0"
            
            # Price
            # Snippet: <span class="textPrimary l5Medium">...₹968</span>
            # We get text direct child of span.l5Medium
            price_text = container.css('span[class*="l5Medium"]::text').get()
            if not price_text:
                 # Fallback
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

        # Pagination logic
        current_page = response.meta.get('page_num', 1)
        next_page = response.xpath('//a[contains(text(), "Next")]/@href').get()
        if not next_page:
             # Try button selector from snippet: <button ...><span ...>Next</span><img ...></button>
             # Actually the snippet shows: <button class="TextualButtonNew__btn__nir4Q ..."><span ...>Next</span>...
             # But buttons usually have click handlers, not hrefs?
             # Wait, snippet shows pagination widget with numbers but buttons might be JS.
             # But I see: <div role="link" ...>1</div> which implies JS navigation.
             # However, earlier logs showed navigation to ?page=2 worked via construction.
             pass

        if next_page:
            yield response.follow(next_page, meta={
                 "playwright": True,
                 "page_num": current_page + 1,
                 "playwright_page_methods": [
                        PageMethod("wait_for_selector", "div[class*='VerticalProductTile__container']"),
                 ]
            })
        else:
             if containers:
                 next_page_num = current_page + 1
                 if next_page_num <= 3: 
                     next_url = f"https://www.1mg.com/categories/nutritional-drinks-196?page={next_page_num}"
                     self.logger.info(f"Constructing next page: {next_url}")
                     yield scrapy.Request(
                        url=next_url,
                        meta={
                            "playwright": True,
                            "page_num": next_page_num,
                            "playwright_page_methods": [
                                PageMethod("wait_for_selector", "div[class*='VerticalProductTile__container']"),
                            ]
                        }
                    )
