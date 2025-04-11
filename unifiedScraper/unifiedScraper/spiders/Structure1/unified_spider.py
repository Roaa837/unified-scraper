import json
import scrapy
from pathlib import Path
from urllib.parse import urljoin
from ...items import UnifiedscraperItem


class UnifiedSpider(scrapy.Spider):
    name = "unified"

    def __init__(self, website=None, *args, **kwargs):
        super(UnifiedSpider, self).__init__(*args, **kwargs)
        self.website = website
        self.config = self.load_config()
        self.selectors = self.config['selectors']

        try:
            self.custom_settings = self.config['custom_settings']

        except KeyError:
            pass


    def load_config(self):
        config_path = Path(__file__).parent.parent / 'configs' / 'websites.json'
        with open(config_path) as f:
            config = json.load(f)

        if self.website not in config:
            raise ValueError(f"Website '{self.website}' not found in configuration")

        return config[self.website]

    def start_requests(self):
        for url in self.config['start_urls']:
            yield scrapy.Request(url=url, callback=self.parse_site_brands_page)

    def parse_site_brands_page(self , response):

        brands_urls = response.css(self.selectors['site-brands-URLs']).getall()
        brands_names = response.css(self.selectors['site-brands-names']).getall()

        for brand_url , brand_name in zip(brands_urls,brands_names):
            absolute_url = self.make_absolute_url(response, brand_url)
            try:
                yield response.follow(
                    absolute_url,
                    callback = self.parse_brand_page,
                    meta = {'brand_name' : brand_name}
                )
            except:
                yield self.parse_brand_page(response)


    def parse_brand_page(self , response):
        brand_item = UnifiedscraperItem()
        brand_item['brand_name'] = response.meta['brand_name']

        brand_products = response.css(self.selectors['number-of-products']).get()
        brand_item['number_of_products'] = '0' if brand_products is None else brand_products

        return brand_item

    def make_absolute_url(self, response, url):
        """Convert any URL to absolute form"""
        if url.startswith(('http://', 'https://')):
            return url  # Already absolute
        return urljoin(response.url, url)  # Handle relative paths