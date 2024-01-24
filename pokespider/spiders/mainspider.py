
import scrapy
from scrapy_playwright.page import PageMethod

from scrapy import Spider, Request, Selector

from pokespider.items import PokespiderItem


class MainSpider(Spider):
    """The main spider for scraping """

    name = "Main Spider"

    def __init__(self):
        pass

    def start_requests(self):
        """Returns a list of requests that scrapy will process for the start of the spider. 
        """

        url = "https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&page=1&view=grid&RarityName=Common|Uncommon|Promo|Rare|Ultra+Rare|Holo+Rare|Secret+Rare|Amazing+Rare|Rare+Ace|Radiant+Rare|Hyper+Rare|Rare+BREAK|Prism+Rare|Special+Illustration+Rare|Unconfirmed|Double+Rare|Illustration+Rare|Shiny+Holo+Rare|Classic+Collection"

        meta = {
            "playwright":               True,
            "playwright_include_page":  True,
            "errback":                  self.error_callback,
            "playwright_page_methods":  [
                PageMethod("wait_for_selector", "div.search-result__content a"),
            ]            
        }

        yield Request(url, meta=meta, dont_filter=True)

    async def parse(self, response):
        """Parses through the main requests that scrapy starts with, 
           returning more requests to continue through.
        """

        page = response.meta["playwright_page"]
        await page.close()

        print("\n\nDone Waiting on playwright")

        # Get all the links to card pages in the search results
        card_details_links = response.css("div.search-result__content a::attr(href)").getall()

        for url in card_details_links:
            print(f"Following url: {url}")
            meta = {
                "playwright":               True,
                "playwright_include_page":  True,
                "errback":                  self.error_callback,
                "playwright_page_methods":  [
                    PageMethod("wait_for_selector", "div#app"),
                    PageMethod("wait_for_selector",  "section.product-details"),
                ]    
            }
            return response.follow(url, callback=self.parse_card_details_page, meta=meta, dont_filter=True)

        # Get the next page to search, and follow to it.
        next_page_url = response.xpath('.//a[@aria-label="Next page"]/@href').get()
        meta = {
            "playwright":               True,
            "playwright_include_page":  True,
            "errback":                  self.error_callback,
            "playwright_page_methods":  [
                PageMethod("wait_for_selector", "div.search-result__content a"),
            ]            
        }
        #yield response.follow(next_page_url, callback=self.parse, meta=meta)

    async def parse_card_details_page(self, response):
        page = response.meta["playwright_page"]
        await page.close()

        print(f"\n\nPage HTML:\n\n{response.body}\n\n")

        #breadcrumb_items = response.css("a.tcg-breadcrumbs-item__link::text")
        #card_series = breadcrumb_items[2]
        #card_name = breadcrumb_items[3]
        #card_rarity = response.css("product__item-details__attributes li div span::text").split('/')[2]

        return PokespiderItem(
            card_series = "s",
            card_name = "n",
            card_type = "r",
            low_price = 0,
            high_price = 1,
            market_price = 2,
            median_price = 3,
        )

    async def error_callback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()