# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PriceTrackerItem(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    url = scrapy.Field()
    image_url = scrapy.Field()
    scraped_at = scrapy.Field()
    
    # New fields for Tata 1mg
    pack_size = scrapy.Field()
    rating = scrapy.Field()
    rating_count = scrapy.Field()
