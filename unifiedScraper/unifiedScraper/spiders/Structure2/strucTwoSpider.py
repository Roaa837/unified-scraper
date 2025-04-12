import json
import scrapy
from pathlib import Path
from urllib.parse import urljoin
from ...items import ProductItem

class StrucTwoSpider(scrapy.Spider):
    name = "struc_two"
    
    custom_settings = {
        'FEEDS': {
            '%(website)s_products.csv': {
                'format': 'csv',
                'fields': ['product_url', 'product_description', 'category', 'brand', 'product_name', 'product_price'],
                'overwrite': True,
                'encoding': 'utf8'
            }
        },
        'DEFAULT_REQUEST_HEADERS': {
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
    }

    def __init__(self, website=None, *args, **kwargs):
        super(StrucTwoSpider, self).__init__(*args, **kwargs)
        self.website = website
        self.config = self.load_config()
        self.selectors = self.config['selectors']
        self.category = self.config.get('categories', 'uncategorized')

    def load_config(self):
        """Load website-specific configuration from JSON"""
        config_path = Path(__file__).parent.parent / 'configs' / 'websites2.json'
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if self.website not in config:
                    raise ValueError(f"Website '{self.website}' not found in configuration")
                return config[self.website]
        except Exception as e:
            raise ValueError(f"Error loading config: {str(e)}")

    def start_requests(self):
        """Initialize scraping with start URLs"""
        for url in self.config['start_urls']:
            yield scrapy.Request(
                url=url,
                callback=self.parse_product_listing,
                meta={'category': self.category},
                errback=self.handle_error
            )

    def parse_product_listing(self, response):
        """Parse product listing pages and extract product links"""
        try:
            product_links = response.css(self.selectors['product_links']).getall()
            
            for product_url in product_links:
                absolute_url = self.make_absolute_url(response, product_url)
                yield scrapy.Request(
                    url=absolute_url,
                    callback=self.parse_product_page,
                    meta={
                        'category': response.meta['category'],
                        'listing_page_brand': self.extract_brand_from_listing(response)
                    },
                    errback=self.handle_error
                )
            
            # Handle pagination
            next_page = response.css(self.selectors.get('next_page', '')).get()
            if next_page:
                yield response.follow(
                    next_page,
                    callback=self.parse_product_listing,
                    meta={'category': response.meta['category']},
                    errback=self.handle_error
                )
                
        except Exception as e:
            self.logger.error(f"Error parsing listing page: {str(e)}")

    def parse_product_page(self, response):
        """Parse individual product pages"""
        try:
            item = ProductItem()
            item['product_url'] = response.url
            item['category'] = response.meta['category']
            item['product_name'] = self.clean_text(response.css(self.selectors['product_name']).get())
            item['product_price'] = self.clean_price(response.css(self.selectors['product_price']).get())
            item['product_description'] = self.clean_text(' '.join(
                response.css(self.selectors['product_description']).getall()))
            item['brand'] = self.extract_brand(response)
            
            yield item
            
        except Exception as e:
            self.logger.error(f"Error parsing product page {response.url}: {str(e)}")

    def extract_brand(self, response):
        """Extract brand name from multiple possible locations with priority:
        1. From listing page (meta)
        2. From dedicated brand element on product page
        3. From image alt text
        4. From product name
        """
        # 1. Check if brand was passed from listing page
        if brand := response.meta.get('listing_page_brand'):
            return brand
        
        # 2. Check dedicated brand selectors
        brand_selectors = self.selectors.get('brand_selectors', [
            'a[href*="/brand/"]::text',
            '.product-brand::text',
            'span.brand::text',
            'meta[property="brand"]::attr(content)'
        ])
        
        for selector in brand_selectors:
            if brand := response.css(selector).get():
                return self.clean_brand_name(brand)
        
        # 3. Check image alt text (for cases like "NIKE TRACKSUIT")
        if alt_text := response.css('img::attr(alt)').get():
            if ' ' in alt_text:  # If alt contains multiple words
                return self.clean_brand_name(alt_text.split()[0])
            return self.clean_brand_name(alt_text)
        
        # 4. Fallback to first word of product name
        if product_name := response.meta.get('product_name'):
            return self.clean_brand_name(product_name.split()[0])
            
        return 'unknown_brand'

    def extract_brand_from_listing(self, response):
        """Extract brand from product listing page if available"""
        listing_brand_selectors = self.selectors.get('listing_brand_selectors', [
            'a[href*="/brand/"]::text',
            '.listing-brand::text'
        ])
        
        for selector in listing_brand_selectors:
            if brand := response.css(selector).get():
                return self.clean_brand_name(brand)
        return None

    def clean_brand_name(self, brand):
        """Clean and normalize brand names"""
        if not brand:
            return 'unknown_brand'
            
        brand = brand.strip()
        # Remove common prefixes/suffixes
        for suffix in ['®', '™', ':', '-']:
            brand = brand.replace(suffix, '')
        return brand.strip()

    def clean_text(self, text):
        """Clean and normalize text data"""
        return ' '.join(text.strip().split()) if text else ''

    def clean_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return None
        # Remove currency symbols and thousands separators
        cleaned = ''.join(c for c in price_text if c.isdigit() or c in ',.')
        try:
            return float(cleaned.replace(',', '.'))
        except ValueError:
            return None

    def make_absolute_url(self, response, url):
        """Convert any URL to absolute form"""
        if not url:
            return None
        if url.startswith(('http://', 'https://')):
            return url
        return urljoin(response.url, url)

    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")