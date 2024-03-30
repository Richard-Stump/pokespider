#===============================================================================
# main_spider.py - The spider that performs the actual web scraping. 
#
# Pseudocode:
# 
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

from scrapy_playwright.page import PageMethod

import logging

import wx
import wx.lib.scrolledpanel

class SelectionWindow:
    id_base = 1000

    def __init__(self, set_names = None, grid_width = 4):
        self.app = wx.App()
        self.window = wx.Frame(None, title="Select your sets")

        self.panel = wx.lib.scrolledpanel.ScrolledPanel(self.window)
        self.grid_sizer = wx.GridSizer(grid_width)

        self.selection_dict = {}

        for index, set_name in enumerate(set_names):
            id = self.id_base + index
            checkbox = wx.CheckBox(self.panel, id=id, label=set_name)
            checkbox.Bind(wx.EVT_CHECKBOX, self.select_item, checkbox)

            self.selection_dict[id] = [set_name, False]

            self.grid_sizer.Add(checkbox)

        self.panel.SetSizer(self.grid_sizer)
        self.panel.SetupScrolling()

        self.window.Layout()
        
        self.window.Show()
        self.app.MainLoop()

    def select_item(self, event):   
        checkbox = event.GetEventObject()
        checkbox_id = checkbox.GetId()   
        checked = checkbox.IsChecked()

        print(f"User modified item selection: id={checkbox_id}, checked={checked}")
        
        self.selection_dict[checkbox_id][1] = checked

    def get_selection(self):
        selection_list = []

        for id, value in self.selection_dict.items():
            set_name, selected = value
            if selected:    
                selection_list.append(set_name)

        return selection_list

class MainSpider(Spider):
    """The main spider for scraping """

    name = "main"

    def __init__(self):
        pass

    def start_requests(self):
        """Returns a list of requests that scrapy will process for the start of the spider. 
        """

        url = "https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&page=1&view=grid"
        
        yield self.request_set_selector(url)

    def get_set_selection(self, set_names):
        
        window = SelectionWindow(set_names, 4)

        selected_items =  window.get_selection()

        self.log(f"Selected Items: \n{selected_items}\n", level=logging.INFO)

        return selected_items


#===============================================================================
# PAGE REQUEST METHODS
# 
# These methods are the callbacks that repsond to responses from the web page
# and extract the information we want from them. We can think of these as the
# "Business" logic of the spider. 
#===============================================================================
        
    def set_name_to_url_param(self, set_name):
        """
        Converts the name of a set to the URL parameter that is used to query it.

        Parameters
        ----------
        self : MainSpider
            A referenece to the object that this method is being called on
        set_name : str
            The name of the set to convert. 
        """

        working_str = set_name.replace(":", "")
        working_str = working_str.replace("(", "")
        working_str = working_str.replace(")", "")
        working_str = working_str.replace("'", "")
        working_str = working_str.replace(" - ", " ")
        working_str = working_str.replace("&", "and")
        working_str = working_str.lower()
        working_str = working_str.replace(" ", "-")
        url_param = f"setName={working_str}"
        # TODO: Replace parenthesis
        return url_param

    def parse_set_selector(self, response):
        """
        Parses the card set filter on the search page, or the default list of 
        sets to scrape. Used for creating the set selector window. 

        Parameters
        ----------
        self : MainSpider
            A referenece to the object that this method is being called on
        Response :  Scrapy.Response
            The search page that we a parsing. 
        """

        # Fetch the list of sets that TCGPlayer.com has listed. 
        site_set_names = response.css("[data-testid=searchFilterSet] * .tcg-input-checkbox__label-text::text").getall()
        selected_sets = []

        # If we are not using the set selection window, add all the sets in the
        # DEFAULT_SET_LIST setting, but double check that they actually exist on
        # the site before adding it. Otherwise, use the list we scraped off of 
        # the search page.
        if not self.settings.getbool("USE_SET_SELECTION_WINDOW"):
            for item in self.settings.getlist("DEFAULT_SET_LIST"):
                if item not in site_set_names:
                    message = f"Set {item} does not exist on TCGPlayer.com!" + \
                        "Skipping"
                    self.log(message, level = logging.WARNING)
                else:
                    selected_sets.append(item)
        else:
            set_names = site_set_names
            selected_sets = self.get_set_selection(set_names)

        # Loop through all our selected sets and create a request for each one. 
        root_url = response.url
        for set_name in selected_sets:
            url_param = self.set_name_to_url_param(set_name)

            url = f"{root_url}&{url_param}"

            meta = { "card_set": set_name }

            yield self.request_search_page(url, response, meta=meta)

    def parse_search_page(self, response):
        """
        Parses a search result page. 

        Parameters
        ----------
        self : MainSpider
            A referenece to the object that this method is being called on
        Response :  Scrapy.Response
            The search page that we a parsing. 
        """

        card_set = response.meta["card_set"]

        self.log(f"Beginning parse of search page for set '{card_set}': {response.url}", level=logging.INFO)

        # Find each of the search result panels in the page and parse them.
        search_results = response.css(".search-result").getall()
        for search_result in search_results:
            item = self.parse_search_result(search_result)

            url = item['first_url']

            item['first_url'] = self.get_absolute_url(url, response)
            yield self.request_first_details_page(url, response, item)

        next_page_url = response.xpath('.//a[@aria-label="Next page"]/@href').get()

        # If we have a url from the next-page button, parse it. Otherwise, we
        # know that we have reached the last search page and can finish.
        if next_page_url is not None:
            meta = {"card_set": card_set}
            yield self.request_search_page(next_page_url, response, meta=meta)
        else:
            self.log(f"Done parsing card set '{card_set}'", level=logging.INFO)

    def parse_search_result(self, search_result_body):
        """
        Parses a search result panel for a singular card, from the search page. 

        Parameters
        ----------
        self : MainSpider
            A referenece to the object that this method is being called on
        Response :  Scrapy.Response
            The contents of the search result panel that we are parsing details
            from. 
        """

        selector = Selector(text=search_result_body)

        card_series = selector.css(".product-card__subtitle::text").get()  \
            .replace(": ", " - ")

        rarity_spans = selector.css(".product-card__rarity span")

        self.log(f"parse_search_result:\n    rarity_spans: {rarity_spans}")

        card_rarity = None

        # If this card doesn't have a rarity associated with it. Skip it because 
        # it's a pack of some sort we don't care about
        if len(rarity_spans) > 0:
            card_rarity = rarity_spans[0].css("span::text").get()

        card_number = None

        # Check that the search result card actually has a card number. 
        # Occasionally, some promo cards aren't actually used in deck building
        # and won't have a card number
        if len(rarity_spans) >= 3:
            card_number = rarity_spans[2].css("span::text").get()   \
                .split('/')[0]                                      \
                .strip("#")
        
        card_name = selector.css(".product-card__title::text").get()   \
            .split('-')[0]                                              \
            .strip()
    
        # Not actually the price with shipping. Some lazy-ass programmer didn't
        # bother to rename the class.
        minimum_price = selector.css(".inventory__price-with-shipping::text").get()

        market_price = selector.css(".product-card__market-price--value::text").get()

        first_url = selector.css("a::attr(href)").get()

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
        """
        Parses the first details page for a specific card. 

        Parameters
        ----------
        self : MainSpider
            A referenece to the object that this method is being called on
        Response :  Scrapy.Response
            The response that we are parsing
        """
        
        item = response.meta['wip_item']

        self.log(f"Parsing first details page for {item['first_url']}", level = logging.INFO)
        
        headers = response.css(".price-points__header__price *::text").getall()

        headers = [h.strip() for h in headers]
        has_normal_prices = "Normal" in headers
        has_foil_prices = "Foil" in headers

        item['has_normals'] = 'X' if has_normal_prices else None
        item['has_foils'] = 'X' if has_foil_prices else None

        # Depending on whether this card has holofoils, normal cards or both,
        # we need to scrape and store the data slightly differently
        prices = response.css(".price-points .price::text").getall()
        if has_normal_prices and has_foil_prices:
            item['market_price'] = prices[0]    
            item['foil_market_price'] = prices[1]
            item['median_price'] = prices[4]
            item['foil_median_price'] = prices[5]
        elif has_normal_prices:
            item['market_price'] = prices[0]
            item['median_price'] = prices[2]
        elif has_foil_prices:
            # This card has no normal cards, so we need to clear the normal
            # prices we scraped. 
            item['market_price'] = None
            item['median_price'] = None
            item['foil_market_price'] = prices[0]
            item['foil_median_price'] = prices[2]

        next_url = response.css('.tcg-pagination__pages a::attr(href)').getall()[-1]

        self.log(f"Done Parsing First Details Page for {item['first_url']}", level = logging.INFO)

        yield self.request_last_details_page(next_url, response, item)

    def parse_last_details_page(self, response):
        """
        Parses the last details page for a specific card. 

        Parameters
        ----------
        self : MainSpider
            A referenece to the object that this method is being called on
        Response :  Scrapy.Response
            The response that we are parsing
        """

        item = response.meta['wip_item']

        self.log(f"Parsing last details page for {item['first_url']}", level = logging.INFO)
        
        listing_prices = response.css(".listing-item__price::text").getall();
        
        item['high_price'] = listing_prices[-1]
        
        self.log(f"Done parsing last details page for {item['first_url']}", level = logging.INFO)

        yield item

    def error_callback(self, failure):
        """
        Responds to any errors encountered by scrapy. 

        Parameters
        ----------
        self : MainSpider
            A referenece to the object that this method is being called on
        Response :  Scrapy.Response
            The response that failed to download. 
        """
        request = failure.request

        try:
            item = request.meta['wip_item']
            item['error_encountered'] = failure.getErrorMessage()

            return item
        except KeyError:
            self.logger.error("Could not return partial item from error callback")
            return None

#===============================================================================
# PAGE REQUEST METHODS
# 
# These exist to abstract the details of requesting pages. Different download 
# handlers use different ways of storing which CSS selectors they should wait
# for, and this makes it so that only needs to be changed in the methods bellow
# without having to touch the business logic of the spider. 
#===============================================================================
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
        return new_url
    
    def request_set_selector(self, url, response = None, meta = None):
        """
        Requests a search page with a wait for the set selector to appear. 
        Handles whatever middleware-specific details are necessary

        Parameters
        ----------
        self : MainSpider
            Reference to the MainSpider object this method is being called for.
        url : str
            The url to request.
        response : Scrapy.Response
            The response that the URL was parsed from.
        meta : dict
            A dictionary that will be attached to the request and response, and 
            used by middlewares. 

        Returns
        -------
        Scrapy.Request
            A request to the passed URL with the passed meta data, and middleware
            specific data to wait for the set selector. 
        """
        if meta is None:
            meta = {}

        meta['playwright'] = True
        meta['playwright_page_methods'] = [
            PageMethod("wait_for_selector", "[data-testid=searchFilterSet]")
        ]
        
        new_url = self.get_absolute_url(url, response)
        self.log(f"Requesting set selector: {new_url}", level=logging.INFO)

        return Request(
            url = new_url,
            callback = self.parse_set_selector,
            errback = self.error_callback,
            meta = meta
        )

    def request_search_page(self, url, response = None, meta = None):
        """
        Requests a search page with a wait for the search result cards to appear.
        Handles whatever middleware-specific details are necessary.

        Parameters
        ----------
        self : MainSpider
            Reference to the MainSpider object this method is being called for.
        url : str
            The url to request.
        response : Scrapy.Response
            The response that the URL was parsed from.
        meta : dict
            A dictionary that will be attached to the request and response, and 
            used by middlewares. 

        Returns
        -------
        Scrapy.Request
            A request to the passed URL with the passed meta data, and middleware
            specific data to wait for the search cards.  
        """

        if meta is None:
            meta = {}

        meta['playwright'] = True
        meta['playwright_page_methods'] = [
            PageMethod("wait_for_selector", ".search-results")
        ]

        new_url = self.get_absolute_url(url, response)

        self.log(f"Requesting search page {new_url}", level=logging.INFO)
        return Request(
            url = new_url,
            callback = self.parse_search_page,
            errback = self.error_callback,
            meta = meta
        )
    
    def request_first_details_page(self, url, response, item, meta = None):
        """
        Requests a cards initial details page with a wait for necessary data to 
        appear. Handles whatever middleware-specific details are necessary.

        Parameters
        ----------
        self : MainSpider
            Reference to the MainSpider object this method is being called for.
        url : str
            The url to request.
        response : Scrapy.Response
            The response that the URL was parsed from.
        meta : dict
            A dictionary that will be attached to the request and response, and 
            used by middlewares. 

        Returns
        -------
        Scrapy.Request
            A request to the passed URL with the passed meta data, and middleware
            specific data to wait for the required data. 
        """
        
        if meta is None:
            meta = {}

        meta['wip_item'] = item

        meta['playwright'] = True
        meta['playwright_page_methods'] = [
            PageMethod("wait_for_selector", ".price-points"),
            PageMethod("wait_for_selector", ".tcg-pagination__pages")
        ]

        new_url = self.get_absolute_url(url, response)

        self.log(f"Requesting first details page: {new_url}", level=logging.INFO)
        return Request(
            url = new_url,
            callback = self.parse_first_details_page,
            errback = self.error_callback,
            meta = meta,
        )
    
    def request_last_details_page(self, url, response, item, meta = None):
        """
        Requests a card's last details page with a wait for necessary data to 
        appear. Handles whatever middleware-specific details are necessary.

        Parameters
        ----------
        self : MainSpider
            Reference to the MainSpider object this method is being called for.
        url : str
            The url to request.
        response : Scrapy.Response
            The response that the URL was parsed from.
        meta : dict
            A dictionary that will be attached to the request and response, and 
            used by middlewares. 

        Returns
        -------
        Scrapy.Request
            A request to the passed URL with the passed meta data, and middleware
            specific data to wait for the required data. 
        """

        if meta is None:
            meta = {}

        meta['wip_item'] = item

        meta['playwright'] = True
        meta['playwright_page_methods'] = [
            PageMethod("wait_for_selector", ".price-points"),
        ]
        
        new_url = self.get_absolute_url(url, response)

        self.log(f"Requesting first details page: {new_url}", level=logging.INFO)
        return Request(
            url = new_url,
            callback = self.parse_last_details_page,
            errback = self.error_callback,
            meta = meta,
        )

        