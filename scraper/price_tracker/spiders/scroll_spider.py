import scrapy
from scrapy_playwright.page import PageMethod

class ScrollSpider(scrapy.Spider):
    name = "computers"
    
    def start_requests(self):
        yield scrapy.Request(
            url="https://webscraper.io/test-sites/e-commerce/scroll/computers/laptops",
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    # 1. Wait for the product grid to exist
                    PageMethod("wait_for_selector", "div.thumbnail"),
                    
                    # 2. Scroll to bottom 5 times to trigger "Infinite Load"
                    PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)"),
                    PageMethod("wait_for_timeout", 2000), # Wait 2s for load
                    PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)"),
                    PageMethod("wait_for_timeout", 2000),
                    PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)"),
                    PageMethod("wait_for_timeout", 2000),
                ]
            }
        )

    def parse(self, response):
        # Now 'response' contains the HTML *after* the scrolling happened
        for product in response.css('div.thumbnail'):
            yield {
                'name': product.css('a.title::attr(title)').get(),
                'price': float(product.css('h4.price::text').get().replace('$', '')),
                'description': product.css('p.description::text').get(),
                'url': "https://webscraper.io" + product.css('a.title::attr(href)').get(),
                'image_url': "https://webscraper.io" + product.css('img::attr(src)').get(),
                'scraped_at': "2025-12-09" # In real code, use datetime
            }