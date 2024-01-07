
import scrapy

class MainSpider(scrapy.Spider):
    name = "Main Spider"

    def __init__(self):
        pass

    def start_requests(self):
        url = "https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&page=1&view=grid"

        meta = {
            "playwright":               True,
            "playwright_include_page":  True,
        }

        yield scrapy.Request(url, meta=meta)

    def parse(self, response):
        pass