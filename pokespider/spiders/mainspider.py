#===============================================================================
# mainspider.py - Main Spider for the scraper
#
# This file implements the code to request pages and parse through responses.
#
# The spider starts by parsing through the initial search page, finding the URLs
# to each of the card details pages, and requesting those pages. After 
# requesting each detail page, the spider then requests the next search page and
# requests the next search page until there are none left. 
# 
# The spider will parse each detail page to find the lowest price, median price,
# card name, etc. and return a request for the last page of the card's details,
# where it will then parse for the high price for the card. 
#===============================================================================

from scrapy import Spider, Request, Selector

from pokespider.items import PokespiderItem

from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC

# This is defined here because scrapy-selenium does not provide bindings for
# EC.all_of() >_>
#
# I love dealing with libraries that haven't been updated in 4 years. 
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

# This is defined here because scrapy-selenium does not provide bindings for
# EC.any_of() >_>
#
# I love dealing with libraries that haven't been updated in 4 years. 
def any_of(*expected_conditions):
    """An expectation that any of multiple expected conditions is true.

    Equivalent to a logical 'OR'. Returns results of the first matching
    condition, or False if none do.
    """

    def any_of_condition(driver):
        for expected_condition in expected_conditions:
            try:
                result = expected_condition(driver)
                if result:
                    return result
            except WebDriverException:
                pass
        return False

    return any_of_condition

class MainSpider(Spider):
    """The main spider for scraping """

    name = "Main Spider"

    def __init__(self):
        pass

    def start_requests(self):
        """Returns a list of requests that scrapy will process for the start of the spider. 
        """

        url = "https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&page=1&view=grid&RarityName=Common|Uncommon|Promo|Rare|Ultra+Rare|Holo+Rare|Secret+Rare|Amazing+Rare|Rare+Ace|Radiant+Rare|Hyper+Rare|Rare+BREAK|Prism+Rare|Special+Illustration+Rare|Unconfirmed|Double+Rare|Illustration+Rare|Shiny+Holo+Rare|Classic+Collection"
        #url = "https://www.tcgplayer.com/search/pokemon/ruby-and-sapphire?productLineName=pokemon&setName=ruby-and-sapphire&page=1&view=grid"

        yield self.request_search_page(url)


    def parse(self, response):
        """
        Callback to parse through a search page 
        
        Parameters
        ----------
        self : MainSpider 
            Reference to the MainSpider object this method is being called for.
        response : Scrapy.Response 
            The response that we are parsing.

        Returns
        ----------
        Scrapy.Request 
            A request to handle the next step in scraping. 
        """

        print("\n\nProcessing Search Page")

        # Get all the links to card pages in the search results
        card_details_links = response.css("div.search-result__content a::attr(href)").getall()

        for url in card_details_links:
            print(f"Following url: {url}")

            yield self.request_first_details_page(response, url)

        # Get the next page to search, and follow to it.
        next_page_url = response.xpath('.//a[@aria-label="Next page"]/@href').get()

        yield self.request_search_page(next_page_url, response)

    def parse_card_details_page(self, response):
        """
        Callback to parse through the first page of a card's detail pages. 
        
        Parameters
        ----------
        self : MainSpider 
            Reference to the MainSpider object this method is being called for.
        response : Scrapy.Response 
            The response that we are parsing.

        Returns
        ----------
        Scrapy.Request 
            A request to handle the next step in scraping. 
        """

        print("\n\nProcessing Details Page: First")
        # print(f"\n\nPage HTML:\n\n{response.body}\n\n")

        card_series = response.css(".tcg-breadcrumbs-item__link::text")[2].get().replace(':', ' -')
        card_name = response.css(".tcg-breadcrumbs-item__non-link::text").get().split('-')[0].strip()

        card_number_rarity_strs = response.css(".product__item-details__attributes li div span::text").getall()[0].split('/')
        
        card_order  = card_number_rarity_strs[0].lstrip('0')
        card_rarity = card_number_rarity_strs[-1]

        market_price = None
        median_price = None
        foil_market_price = None
        foil_median_price = None

        print(f"market: '{market_price}'")
        print(f"merdian: '{median_price}'")

        headers = response.css(".price-points__header__price *::text").getall()
        headers = [h.strip(' ') for h in headers]
        has_normal_prices = "Normal" in headers
        has_foil_prices = "Foil" in headers


        print(f"headers: {headers}")
        print(f"has_normal_prices = {has_normal_prices}")
        print(f"has_foil_prices = {has_foil_prices}")

        price_points = response.css(".price-points table tr td span.price::text").getall()
        if has_normal_prices and has_foil_prices:
            print(f"price points: {price_points}")

            market_price = price_points[0]
            median_price = price_points[4]
            foil_market_price = price_points[1]
            foil_median_price = price_points[5]
        elif has_normal_prices:
            market_price = price_points[0]
            median_price = price_points[2]
        elif has_foil_prices:
            foil_market_price = price_points[0]
            foil_median_price = price_points[2]

        if len(response.css(".no-result").getall()) > 0:
            print("Card has no listings whatsoever, returning what we can")
            
            yield PokespiderItem(
                first_url = response.url,
                card_order = card_order,
                card_series = card_series,
                card_name = card_name,
                card_rarity = card_rarity,
                low_price = None,
                high_price = None,
                market_price = market_price,
                median_price = median_price,
                foil_market_price = foil_market_price,
                foil_median_price = foil_median_price,
            )

        low_price = response.css(".listing-item__price:nth-child(1)::text").get()

        # Create a W.I.P. item with all the data we have scraped from this page. 
        # This will be attatched to our request as a metadata object so that the
        # request for the last details page can fetch the high price for the
        # card. 
        wip_item = PokespiderItem(
            first_url = response.url,
            card_order = card_order,
            card_series = card_series,
            card_name = card_name,
            card_rarity = card_rarity,
            low_price = low_price,
            high_price = None,
            market_price = market_price,
            median_price = median_price,
            foil_market_price = foil_market_price,
            foil_median_price = foil_median_price,
        )

        # Navigate to the last page to get the high price
        url = response.css('.tcg-pagination__pages a:last-child::attr(href)').get()
        print(f"\n\nFollowing {url}\n\n")

        yield self.request_last_details_page(response, url, wip_item)

    def parse_card_details_page_last(self, response):
        """
        Callback to parse through the last page of a card's detail pages. 
        
        Parameters
        ----------
        self : MainSpider 
            Reference to the MainSpider object this method is being called for.
        response : Scrapy.Response 
            The response that we are parsing.

        Returns
        ----------
        PokespiderItem
            The completed 
        """

        print("\n\nProcessing Details Page: Last")
        print("\n\n\n\parsing last page\n\n\n")

        item = response.meta["wip_item"]

        # If we find the .no-result class, we have reached an invalid details page.
        # I assume this occurs if a number of listings are deleted at once, causing
        # a race condition between our site requesting the last page the the site
        # delivering the page. 
        if len(response.css(".no-result").getall()) > 0:
            print("    Failing over to try and hit the last page again")
            url = response.css('.tcg-pagination__pages a:last-child::attr(href)').get()
            return self.request_last_details_page(response, url, item)

        listing_prices = response.css(".listing-item__price::text").getall()
        print(f"\n\n listing prices: {listing_prices}")

        high_price = listing_prices[-1]

        item['high_price'] = high_price

        return item

    def error_callback(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        # If we have an error parsing a request, and its for a details page,
        # we simply want to write to the CSV that the card was not scraped, and
        # leave a link to the card so that it is possible to manually get the data
        # rather than re-run this scraper. 
        request = failure.request

        if request.meta["parse_step"] == "first_details_page" or request.meta["parse_step"] == "last_details_page":
            return PokespiderItem(
                first_url = request.url,
                card_name = f"ERROR ENCOUNTERED WHILE SCRAPING PAGE: {failure}",
                card_order = None,
                card_series = "ERRONEOUS CARDS",
                card_rarity = None,
                low_price = None, 
                high_price = None,
                market_price = None,
                median_price = None,
                foil_market_price = None,
                foil_median_price = None,
            )

    def get_absolute_url(self, response, url):
        """
        Converts a relative-pathed URL to an absolute-pathed URL for navigation.

        Parameters
        ----------
        self : MainSpider
            Reference to the MainSpider object this method is being called for.
        response : Scrapy.Response
            The response that the URL was parsed from
        url : string
            The URL to convert

        Returns
        -------
        string
            The absolute path of the passed url. 
        """
        if response is None:
            return url

        new_url = response.urljoin(url)
        print(f"\n\nOriginal Url: {url}\nNew Url:    {new_url}")
        return new_url

    def request_search_page(self, url, response = None):
        """
        Returns a Scrapy.Request object to request a search page, setting up the
        necessary metainfo for whatever drivers/middlewares are being used. 

        Parameters
        ----------
        self : MainSpider
            Reference to the MainSpider object this method is being called for.
        url : string
            The URL to the new request.
        response : Scrapy.Response
            The response that this new request is coming from, or None if this
            request is not coming from a parse response. 

        Returns
        -------
        Scrapy.Request
            A request object to request a search page.
        """
        
        return SeleniumRequest(
            url = self.get_absolute_url(response, url),
            errback = self.error_callback,
            wait_time = 10,
            wait_until = EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, "div.search-result__content a")
            ),
            meta = {
                "parse_step": "search_page",
            }
        )

    def request_first_details_page(self, response, url):
        """
        Returns a Scrapy.Request object to request the first page of a card's
        details page, setting up the necessary metainfo for whatever 
        drivers/middlewares are being used.

        Parameters
        ----------
        self : MainSpider
            Reference to the MainSpider object this method is being called for.
        url : string
            The URL to the new request.
        response : Scrapy.Response
            The response that this new request is coming from

        Returns
        -------
        Scrapy.Request
            A request object to request the first details page.
        """

        condition = any_of(
            all_of(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "section.product-details")),
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".tcg-breadcrumbs-item")),
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".price-points")),
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".tcg-pagination__pages")),
            ),
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".no-result")),
        )

        return SeleniumRequest(
            url = self.get_absolute_url(response, url),
            callback = self.parse_card_details_page,
            errback = self.error_callback,
            wait_time = 10,
            wait_until = condition,
            meta = {
                "parse_step": "first_details_page",
            }
        )

    def request_last_details_page(self, response, url, wip_item):
        """
        Returns a Scrapy.Request object to request the last page of a card's
        details page, setting up the necessary metainfo for whatever 
        drivers/middlewares are being used.

        Parameters
        ----------
        self : MainSpider
            Reference to the MainSpider object this method is being called for.
        url : string
            The URL to the new request.
        response : Scrapy.Response
            The response that this new request is coming from

        Returns
        -------
        Scrapy.Request
            A request object to request the last details page.
        """

        condition = any_of(
            all_of(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div#app")),
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".listing-item__price")),
            ),
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".no-result")),
        )

        return SeleniumRequest(
            url = self.get_absolute_url(response, url),
            callback = self.parse_card_details_page_last,
            errback = self.error_callback,
            wait_time = 10,
            wait_until = condition,
            meta = {
                "wip_item": wip_item,
                "parse_step": "last_details_page",
            }
        )