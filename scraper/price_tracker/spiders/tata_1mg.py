import scrapy
import json
import re
from ..items import PriceTrackerItem
from datetime import datetime

class Tata1mgSpider(scrapy.Spider):
    name = "tata_1mg"
    allowed_domains = ["1mg.com"]
    
    # API Configuration
    BASE_URL = "https://www.1mg.com/pwa-api/api/v5/category/{category_id}?page={page}&per_page=20"
    
    # Category mapping based on user request
    CATEGORIES = {
        # Medicines
        "Health & Medicine": 1,
        "Diabetes Care": 210,
        "Healthcare Devices": 341,
        # Stomach Care
        "Indigestion": 504,
        "Acidity": 714,
        "Constipation": 649,
        "Diarrhoea": 645,
        "Probiotics": 624,
        # Fitness
        "Vitamins & Supplements": 194,
        "Protein Supplements": 458,
        "Fitness Supplements": 459,
        "Health Food & Drinks": 207,
        # Natural
        "Ayurveda": 416,
        "Homeopathy": 417,
        # Personal Care
        "Personal Care": 245,
        "Skin Care": 254,
        "Hair Care": 255,
        "Baby Care": 218,
        "Face Wash": 208,
        "Moisturizers": 646,
        "Cleansers": 117
    }

    # Headers required by the API
    headers = {
        "x-city": "Mumbai",
        "x-requested-with": "XMLHttpRequest",
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1.0,
        # Disable Playwright if it was enabled globally, or just don't use it in requests
        'DOWNLOAD_HANDLERS': {
             "http": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
             "https": "scrapy.core.downloader.handlers.http.HTTPDownloadHandler",
        }
    }

    def start_requests(self):
        for cat_name, cat_id in self.CATEGORIES.items():
            url = self.BASE_URL.format(category_id=cat_id, page=1)
            yield scrapy.Request(
                url=url,
                headers=self.headers,
                callback=self.parse,
                meta={
                    'category_id': cat_id,
                    'category_name': cat_name,
                    'page': 1
                }
            )

    def parse(self, response):
        data = response.json()
        category_name = response.meta['category_name']
        category_id = response.meta['category_id']
        current_page = response.meta['page']
        
        # 1mg API v5 uses a widget-based structure
        widgets = data.get('data', {}).get('widgets', [])
        
        products = []
        for widget in widgets:
            if widget.get('type') == 'sku_card':
                products.append(widget)
        
        found_count = len(products)
        self.logger.info(f"[{category_name}] Page {current_page}: Found {found_count} products.")

        if not products:
            # If no products found, we might have reached the end or API changed.
            pass

        for product in products:
            item = PriceTrackerItem()
            
            # Name
            item['name'] = product.get('name')
            
            # URL
            slug = product.get('url') # e.g. /otc/product-name
            if slug:
                 item['url'] = "https://www.1mg.com" + slug
            else:
                 item['url'] = response.url
            
            # Image
            item['image_url'] = product.get('image')
            
            # Pack Size
            item['pack_size'] = product.get('label')
            
            # Price extraction
            price_obj = product.get('prices', {})
            price_str = price_obj.get('discounted_price') or price_obj.get('mrp')
            
            if price_str:
                try:
                    # Remove currency symbol and commas
                    clean_price = price_str.replace('₹', '').replace(',', '').strip()
                    item['price'] = float(clean_price)
                except:
                    item['price'] = 0.0
            else:
                item['price'] = 0.0
            
            # Rating
            ratings_obj = product.get('ratings')
            if ratings_obj:
                item['rating'] = str(ratings_obj.get('average_rating', 0))
                item['rating_count'] = str(ratings_obj.get('total_ratings', 0))
            else:
                item['rating'] = "0"
                item['rating_count'] = "0"
            
            # Category
            item['category'] = category_name

            item['scraped_at'] = datetime.now().isoformat()
            
            # Yield request to product page for details
            yield scrapy.Request(
                url=item['url'],
                callback=self.parse_product,
                meta={'item': item},
                errback=self.errback_product
            )

    def parse_product(self, response):
        item = response.meta['item']
        
        # Helper to extract text relative to headers
        def get_all_text(response):
            # Extract all text from specific containers where details usually reside
            anchors = response.xpath("//*[contains(text(), 'Information about') or contains(text(), 'Product highlights') or contains(text(), 'Key Ingredients') or contains(text(), 'Safety Information') or contains(text(), 'Directions')]")
            
            seen_texts = set()
            collected_text = []

            if anchors:
                for anchor in anchors:
                    # Try to find the content container
                    container = anchor.xpath("./ancestor::div[contains(@class, 'style__content')]")
                    if not container:
                        container = anchor.xpath("./..")
                    
                    if container:
                        text = " ".join(container.xpath(".//text()").getall())
                        # Avoid duplicates if containers are nested or same
                        if text and text not in seen_texts:
                            seen_texts.add(text)
                            collected_text.append(text)
            
            return " ".join(collected_text)

        full_text = get_all_text(response)
        
        # Clean up text for regex
        # Normalize whitespace
        full_text = " ".join(full_text.split())

        def extract_section(text, header, next_headers):
            # Case insensitive search for header
            pattern = re.escape(header)
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                return None
            
            start_idx = match.end()
            remaining_text = text[start_idx:]
            
            # Find the earliest occurrence of any 'next_header'
            min_idx = len(remaining_text)
            for next_h in next_headers:
                next_match = re.search(re.escape(next_h), remaining_text, re.IGNORECASE)
                if next_match:
                    if next_match.start() < min_idx:
                        min_idx = next_match.start()
            
            return remaining_text[:min_idx].strip(": -")

        # Define headers to look for
        headers_map = {
            'description': ['Product highlights', 'Information about'],
            'key_ingredients': ['Key Ingredients'],
            'safety_information': ['Safety Information'],
            'directions_for_use': ['Directions For Use', 'Directions for Use']
        }
        
        all_headers = []
        for v in headers_map.values():
            all_headers.extend(v)
        all_headers.extend(['Key Benefits', 'Other Information', 'Quick Tips', 'Frequently Asked Questions', 'Product Form', 'Diet Type'])

        # Extract fields
        # Description
        desc = extract_section(full_text, 'Product highlights', all_headers)
        if not desc:
            # Fallback to 'Information about' ... but usually that includes the product Name
            # "Information about [Product Name]"
            # We can try to extract after that.
            # But let's stick to the Regex logic
            pass
        item['description'] = desc

        item['key_ingredients'] = extract_section(full_text, 'Key Ingredients', all_headers)
        item['safety_information'] = extract_section(full_text, 'Safety Information', all_headers)
        item['directions_for_use'] = extract_section(full_text, 'Directions For Use', all_headers)
        if not item['directions_for_use']:
             item['directions_for_use'] = extract_section(full_text, 'Directions for Use', all_headers)

        yield item

    def errback_product(self, failure):
        # If product page fails, yield the item with basic info
        self.logger.error(f"Failed to fetch product page: {failure}")
        yield failure.request.meta['item']

        # Pagination Logic
        # Stop after ~500 products (approx 25 pages @ 20 per page)
        MAX_PAGES = 25 
        
        if current_page < MAX_PAGES:
            next_page = current_page + 1
            next_url = self.BASE_URL.format(category_id=category_id, page=next_page)
            yield scrapy.Request(
                url=next_url,
                headers=self.headers,
                callback=self.parse,
                meta={
                    'category_id': category_id,
                    'category_name': category_name,
                    'page': next_page
                }
            )
