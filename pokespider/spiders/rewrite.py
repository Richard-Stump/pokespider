#===============================================================================
# Rewrite.py - Rewrite of the spider for improved robustness
#
# Pseudocode:
# 
# do:
#   request search page
#   if valid results:
#       Exit Scraper
#
#   For each search result:
#       Extract the following fields into a wip item:
#           Card series, Rarity, # in set, card name, market price,
#           first url
#
#       Request the first details page:
#           Extract the mininmum price, 
#       
#   find url for next search result
#       
# while (search page has valid results)
#
# General algorithm guidelines for this rewrite:
#   1) Check each request for no/invalid data and early exit if none are available.
#   2) Scrape data fields on the earliest screen possible, optionally replacing
#      then with newer values.
#   3) If a particular page failed to be requested, dump whatever fields are
#      available to the CSV files
#===============================================================================

from scrapy import Spider, Request, Selector

from pokespider.items import PokespiderItem

import time

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

class NewSpider(Spider):
    """The main spider for scraping """

    name = "rewrite"

    def __init__(self):
        pass

    def start_requests(self):
        """Returns a list of requests that scrapy will process for the start of the spider. 
        """

        url = "https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&page=1&view=grid&RarityName=Common|Uncommon|Promo|Rare|Ultra+Rare|Holo+Rare|Secret+Rare|Amazing+Rare|Rare+Ace|Radiant+Rare|Hyper+Rare|Rare+BREAK|Prism+Rare|Special+Illustration+Rare|Unconfirmed|Double+Rare|Illustration+Rare|Shiny+Holo+Rare|Classic+Collection"
        #url = "https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&page=18&view=grid&RarityName=Common%7CUncommon%7CPromo%7CRare%7CUltra+Rare%7CHolo+Rare%7CSecret+Rare%7CAmazing+Rare%7CRare+Ace%7CRadiant+Rare%7CHyper+Rare%7CRare+BREAK%7CPrism+Rare%7CSpecial+Illustration+Rare%7CUnconfirmed%7CDouble+Rare%7CIllustration+Rare%7CShiny+Holo+Rare%7CClassic+Collection"

        yield self.request_search_page(url)

    #===========================================================================
    # Page Parsing Methods
    #===========================================================================
        
    def parse_search_page(self, response):
        print("GOT SEARCH PAGE!!!!!!!")

        # Find each of the search result panels in the page and parse them.
        search_results = response.css(".search-result").getall()
        for search_result in search_results:
            item = self.parse_search_result(search_result)

            url = item['first_url']

            item['first_url'] = self.get_absolute_url(url, response)
            print("\n\n\nRETURNINGNONE\n\n\n\n\n")
            yield self.request_first_details_page(url, response, item)

            #return None

        next_page_url = response.xpath('.//a[@aria-label="Next page"]/@href').get()

        # If we have a url from the next-page button, parse it. Otherwise, we
        # know that we have reached the last search page and can finish.
        if next_page_url is not None:
            yield self.request_search_page(next_page_url, response)

    def parse_search_result(self, search_result_body):
        selector = Selector(text=search_result_body)

        card_series = selector.css(".search-result__subtitle::text").get()  \
            .replace(": ", " - ")

        rarity_spans = selector.css(".search-result__rarity span")
        print(f"    rarity_spans: {rarity_spans}")

        card_rarity = rarity_spans[0].css("span::text").get()

        card_number = None

        # Check that the search result card actually has a card number. 
        # Occasionally, some promo cards aren't actually used in deck building
        # and won't have a card number
        if len(rarity_spans) >= 3:
            card_number = rarity_spans[2].css("span::text").get()   \
                .split('/')[0]                                      \
                .strip("#")
        
        card_name = selector.css(".search-result__title::text").get()   \
            .split('-')[0]                                              \
            .strip()
    
        # Not actually the price with shipping. Some lazy-ass programmer didn't
        # bother to rename the class.
        minimum_price = selector.css(".inventory__price-with-shipping::text").get()

        market_price = selector.css(".search-result__market-price--value::text").get()

        first_url = selector.css("a::attr(href)").get()
        print(f"    card_series:    {card_series}")
        print(f"    card_rarity:    {card_rarity}")
        print(f"    card_number:    {card_number}")
        print(f"    card_name:      {card_name}")
        print(f"    minimum_price:  {minimum_price}")
        print(f"    market_price:   {market_price}")
        print(f"    first_url:      {first_url}")

        return PokespiderItem(
            first_url = first_url,
            card_name = card_name,
            card_order = card_number,
            card_series = card_series,
            card_rarity = card_rarity,
            low_price = minimum_price,
            market_price = market_price,
            
            high_price = None,
            median_price = None,
            foil_market_price = None,
            foil_median_price = None,
            has_normals = None,
            has_foils = None,
        )
    
    def parse_first_details_page(self, response):
        item = response.meta['wip_item']

        print(f"\n\n\ PARSING FIRST DETAILS PAGE For: {item['first_url']}")
        yield item
        return None
        
        if response.css(".no-result").get() is not None:
            print(f"    Returning due to no results")
            yield item
            return None

        headers = response.css(".price-points__header__price *::text").getall()
        if headers is not None and len(headers) > 0:
            print(f"    Fetching normal/holo prices")

            headers = [h.strip() for h in headers]
            has_normal_prices = "Normal" in headers
            has_foil_prices = "Foil" in headers

            item['has_normals'] = 'X' if has_normal_prices else None
            item['has_foils'] = 'X' if has_foil_prices else None

            if (not has_normal_prices) and has_foil_prices:
                item['foil_low_price'] = item['market_price']
                item['foil_market_price'] = item['market_price']
                item['low_price'] = None,
                item['market_price'] = None
        
        yield item

    def error_callback(self, failure):
        request = failure.request

        try:
            item = request.meta['wip_item']
            item['error_encountered'] = failure.getErrorMessage()

            return item
        except KeyError:
            self.logger.error("Could not return partial item from error callback")
            return None

    #===========================================================================
    # Page Request Methods
    #===========================================================================
    def get_absolute_url(self, url, response):
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
    
    def request_search_page(self, url, response = None, meta = None):
    
        # This sleep exists to prevent memory issues with the selenium web
        # driver. Without this, the browser doesn't have enough time to clean
        # up memory in between requests. 
        time.sleep(0.5)

        if meta is None:
            meta = {}

        return SeleniumRequest(
            url = self.get_absolute_url(url, response),
            callback = self.parse_search_page,
            errback = self.error_callback,
            wait_time = 60,
            wait_until = EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, "section.search-results")
            ),
            meta = meta
        )
    
    def request_first_details_page(self, url, response, item, meta = None):
        
        if meta is None:
            meta = {}

        meta['wip_item'] = item
    
        condition = any_of(
            #EC.visibility_of_all_elements_located(
            #    (By.CSS_SELECTOR, "body")
            #)
            #EC.visibility_of_all_elements_located(
            #     (By.CSS_SELECTOR, ".price-guide")
            #),
             #EC.visibility_of_all_elements_located(
             #    (By.CSS_SELECTOR, ".listing-item")
             #),
             #EC.visibility_of_all_elements_located(
             #    (By.CSS_SELECTOR, ".no-result")
             #)
            EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, "#app")
            )
        )

        return SeleniumRequest(
            url = self.get_absolute_url(url, response),
            callback = self.parse_first_details_page,
            errback = self.error_callback,
            wait_time = 60,
            wait_until = condition,
            meta = meta,
        )