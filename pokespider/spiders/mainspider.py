
import scrapy

from scrapy import Spider, Request, Selector

from pokespider.items import PokespiderItem

from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC

def all_of(
    *expected_conditions
):
    """An expectation that all of multiple expected conditions is true.

    Equivalent to a logical 'AND'.
    Returns: When any ExpectedCondition is not met: False.
    When all ExpectedConditions are met: A List with each ExpectedCondition's return value.
    """

    def all_of_condition(driver):
        results = []
        for expected_condition in expected_conditions:
            try:
                result = expected_condition(driver)
                if not result:
                    return False
                results.append(result)
            except WebDriverException:
                return False
        return results

    return all_of_condition


class MainSpider(Spider):
    """The main spider for scraping """

    name = "Main Spider"

    def __init__(self):
        pass

    def start_requests(self):
        """Returns a list of requests that scrapy will process for the start of the spider. 
        """

        url = "https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&page=1&view=grid&RarityName=Common|Uncommon|Promo|Rare|Ultra+Rare|Holo+Rare|Secret+Rare|Amazing+Rare|Rare+Ace|Radiant+Rare|Hyper+Rare|Rare+BREAK|Prism+Rare|Special+Illustration+Rare|Unconfirmed|Double+Rare|Illustration+Rare|Shiny+Holo+Rare|Classic+Collection"

        # meta = {
        #     "playwright":               True,
        #     "playwright_page_methods":  [
        #         PageMethod("wait_for_selector", "div.search-result__content a", timeout=60000),
        #     ]            
        # }

        yield SeleniumRequest(
            url = url,
            wait_time = 10,
            wait_until = EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div.search-result__content a"))
        )

    async def parse(self, response):
        """Parses through the main requests that scrapy starts with, 
           returning more requests to continue through.
        """

        print("\n\nProcessing Search Page")

        # Get all the links to card pages in the search results
        card_details_links = response.css("div.search-result__content a::attr(href)").getall()

        for url in card_details_links:
            print(f"Following url: {url}")
            #meta = {
                # "playwright":               True,
                # "playwright_page_methods":  [
                #     PageMethod("wait_for_selector", "div#app"),
                #     PageMethod("wait_for_selector", "section.product-details", timeout=10000),
                #     PageMethod("wait_for_selector", ".tcg-breadcrumbs-item", timeout=10000),
                #     PageMethod("wait_for_selector", ".price-points", timeout=10000),
                #     PageMethod("wait_for_selector", ".tcg-pagination__pages", timeout=10000)
                # ]    
            #}

            condition = all_of(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "section.product-details")),
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".tcg-breadcrumbs-item")),
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".price-points")),
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".tcg-pagination__pages")),
            )

            yield SeleniumRequest(
                url = self.get_absolute_url(response, url),
                callback = self.parse_card_details_page,
                wait_time = 50,
                wait_until = condition
            )
        # Get the next page to search, and follow to it.
        next_page_url = response.xpath('.//a[@aria-label="Next page"]/@href').get()
        # meta = {
        #     "playwright":               True,
        #     "playwright_page_methods":  [
        #         PageMethod("wait_for_selector", "div.search-result__content a", timeout=60000),
        #     ]            
        # }
        #yield response.follow(next_page_url, callback=self.parse, meta=meta)

        condition = EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div.search-result__content a"))

        yield SeleniumRequest(
            url = self.get_absolute_url(response, next_page_url),
            callback = self.parse_card_details_page,
            wait_time = 50,
            wait_until = condition
        )

    async def parse_card_details_page(self, response):
        print("\n\nProcessing Details Page: First")
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
       # meta = {
            # "playwright":               True,
            # "playwright_page_methods":  [
            #     PageMethod("wait_for_selector", "div#app", timeout=10000),
            #     PageMethod("wait_for_selector", ".listing-item__price", timeout=10000),
            # ],
            #"wip_item": wip_item
        #}

        #yield response.follow(url, meta=meta, callback=self.parse_card_details_page_last)

        condition = all_of(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div#app")),
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".listing-item__price")),
        )

        yield SeleniumRequest(
            url = self.get_absolute_url(response, url),
            callback = self.parse_card_details_page_last,
            wait_time = 50,
            wait_until = condition,
            meta = {
                "wip_item": wip_item,
            }
        )
    
    async def parse_card_details_page_last(self, response):
        print("\n\nProcessing Details Page: Last")

        item = response.meta["wip_item"]
        print("\n\n\n\parsing last page\n\n\n")

        listing_prices = response.css(".listing-item__price::text").getall()
        print(f"\n\n listing prices: {listing_prices}")

        high_price = listing_prices[-1]

        item['high_price'] = high_price

        return item

    def get_absolute_url(self, response, url):
        new_url = response.urljoin(url)
        print(f"\n\nOriginal Url: {url}\nNew Url:    {new_url}")
        return new_url
    
