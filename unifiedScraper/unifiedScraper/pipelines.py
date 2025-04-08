# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re


class UnifiedscraperPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        field_names = adapter.field_names()
        for fileld_name in field_names:
            value = adapter.get(fileld_name)
            if fileld_name == "brand_name":
                adapter[fileld_name] = value.strip()

            if fileld_name == "number_of_products":
                adapter[fileld_name] = self.extract_number(value)

        return item

    def extract_number(self ,text):
        match = re.search(r"""
            [-+]?      # Optional sign
            (?:\d{1,3}(?:,\d{3})*  # Thousands with commas
            |\d+)      # Or plain numbers
            (?:\.\d+)? # Optional decimal part
            """, text, re.VERBOSE)

        if match:
            num_str = match.group().replace(',', '')  # Remove thousands separators
            return int(float(num_str))  # Handle both int and float cases
        return None  # Or raise an exception
