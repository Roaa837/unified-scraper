# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class UnifiedscraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    brand_name = scrapy.Field()
    number_of_products = scrapy.Field()

class ProductItem(scrapy.Item):
    """For storing individual product information""" 
    product_url = scrapy.Field()          # Full URL to product page
    product_name = scrapy.Field()         # Title/name of product
    brand = scrapy.Field()                # Parent brand name  
    category = scrapy.Field()             # Product category
    product_price = scrapy.Field()        # Current price (numeric)
    product_description = scrapy.Field()  # Full description text

