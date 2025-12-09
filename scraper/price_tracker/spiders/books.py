import scrapy
from datetime import datetime

class BooksSpider(scrapy.Spider):
    name = "books"
    start_urls = ['http://books.toscrape.com/catalogue/category/books/fantasy_19/index.html']

    def parse(self, response):
        # Loop through every book card on the page
        for book in response.css('article.product_pod'):
            
            # Extract raw data
            title = book.css('h3 a::attr(title)').get()
            price_text = book.css('p.price_color::text').get()
            image_url = book.css('div.image_container a img::attr(src)').get()
            
            # Clean the data (Engineering work!)
            price = float(price_text.replace('£', ''))
            relative_url = book.css('h3 a::attr(href)').get()
            absolute_url = response.urljoin(relative_url)

            yield {
                'name': title,
                'price': price,
                'url': absolute_url,
                'image_url': response.urljoin(image_url),
                'scraped_at': datetime.now().isoformat()
            }

        # Pagination: Follow the "Next" button if it exists
        next_page = response.css('li.next a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)