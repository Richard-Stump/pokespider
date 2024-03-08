# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exporters import CsvItemExporter
import os

class PokespiderPipeline:
    def open_spider(self, spider):
        self.series_to_exporter = {}

    def close_spider(self, spider):
        for exporter, csv_file in self.series_to_exporter.values():
            exporter.finish_exporting()
            csv_file.close()

    def get_exporter(self, item):
        adapater = ItemAdapter(item)
        series = adapater['card_series']

        if series not in self.series_to_exporter:
            if not os.path.exists("./out/"):
                os.makedirs("./out/", exist_ok=True)

            csv_file = open(f"./out/{series}.csv", "wb")
            exporter = CsvItemExporter(csv_file, export_empty_fields = True)
            exporter.fields_to_export = {
                "card_order":           "Card Number",
                "card_name":            "Card Name",
                "has_normals":          "Norms",
                "low_price":            "Low Price",
                "high_price":           "High Price",
                "market_price":         "Normal Market Price",
                "median_price":         "Normal Median Price",
                "low_price_foils":      "Foil Low Price",
                "foil_market_price":    "Foil Market Price",
                "foil_median_price":    "Foil Median Price",
                "first_url":            "URL",
                "errors_encountered":   "Errors"
            }

            exporter.start_exporting()

            self.series_to_exporter[series] = (exporter, csv_file)

        return self.series_to_exporter[series]

    def process_item(self, item, spider):
        print(f"\n\n\n\n\n\n PROCESSING ITEM!!!!!!")
        
        print(f"    url    = {item['first_url']}")
        print(f"    order  = {item['card_order']}")
        print(f"    series = {item['card_series']}")
        print(f"    name   = {item['card_name']}")
        print(f"    rarity = {item['card_rarity']}")
        print(f"    low    = {item['low_price']}")
        print(f"    high   = {item['high_price']}")
        print(f"    market = {item['market_price']}")
        print(f"    median = {item['median_price']}")
        print(f"    f_mark = {item['foil_market_price']}")
        print(f"    f_medi = {item['foil_median_price']}")

        exporter, csv_file = self.get_exporter(item)
        exporter.export_item(item)

        csv_file.flush()

        return item
