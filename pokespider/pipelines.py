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
            exporter = CsvItemExporter(csv_file)
            exporter.start_exporting()

            self.series_to_exporter[series] = (exporter, csv_file)

        return self.series_to_exporter[series]

    def process_item(self, item, spider):
        exporter, _ = self.get_exporter(item)
        item['card_series'] = None
        exporter.export_item(item)

        return item
