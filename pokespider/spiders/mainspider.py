
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
            "playwright_page_methods":  [
                PageMethod("wait_for_selector", "div.search-result__content a", timeout=60000),
            ]            
        }

        yield Request(url, meta=meta, dont_filter=True)

    async def parse(self, response):
        """Parses through the main requests that scrapy starts with, 
           returning more requests to continue through.
        """

        print("\n\nDone Waiting on playwright")

        # Get all the links to card pages in the search results
        card_details_links = response.css("div.search-result__content a::attr(href)").getall()

        for url in card_details_links:
            print(f"Following url: {url}")
            meta = {
                "playwright":               True,
                "playwright_page_methods":  [
                    PageMethod("wait_for_selector", "div#app"),
                    PageMethod("wait_for_selector", "section.product-details"),
                    PageMethod("wait_for_selector", ".tcg-breadcrumbs-item"),
                    PageMethod("wait_for_selector", ".price-points"),
                    PageMethod("wait_for_selector", ".tcg-pagination__pages")
                ]    
            }
            return response.follow(url, callback=self.parse_card_details_page, meta=meta, dont_filter=True)

        # Get the next page to search, and follow to it.
        next_page_url = response.xpath('.//a[@aria-label="Next page"]/@href').get()
        meta = {
            "playwright":               True,
            "playwright_page_methods":  [
                PageMethod("wait_for_selector", "div.search-result__content a"),
            ]            
        }
        #yield response.follow(next_page_url, callback=self.parse, meta=meta)

    async def parse_card_details_page(self, response):
        # print(f"\n\nPage HTML:\n\n{response.body}\n\n")

        card_series = response.css(".tcg-breadcrumbs-item__link::text")[2].get()
        card_name = response.css(".tcg-breadcrumbs-item__non-link::text").get().split('-')[0].strip()
        card_rarity = response.css(".product__item-details__attributes li:nth-child(0) div span::text").get()
        price_points = response.css(".price-points table tr td span.price::text").getall()
        market_price = price_points[0]
        median_price = price_points[4]

        print(f"{market_price}")
        print(f"{median_price}")

        low_price = response.css(".listing-item__price:nth-child(1)::text").get()

        wip_item = PokespiderItem(
            card_series = card_series,
            card_name = card_name,
            card_type = card_rarity,
            low_price = low_price,
            high_price = 1,
            market_price = market_price,
            median_price = median_price,
        )

        # Navigate to the last page to get the high price
        url = response.css('.tcg-pagination__pages a:last-child::attr(href)').get()
        print(f"\n\nFollowing {url}\n\n")
        meta = {
            "playwright":               True,
            "playwright_page_methods":  [
                PageMethod("wait_for_selector", "div#app"),
                PageMethod("wait_for_selector", ".listing-item__price"),
            ],
            "wip_item": wip_item
        }

        yield response.follow(url, meta=meta, callback=self.parse_card_details_page_last)
    
    async def parse_card_details_page_last(self, response):
        item = response.meta["wip_item"]
        print("\n\n\n\parsing last page\n\n\n")

        listing_prices = response.css(".listing-item__price::text").getall()
        print(f"\n\n listing prices: {listing_prices}")

        high_price = listing_prices[-1]

        item['high_price'] = high_price

        return item