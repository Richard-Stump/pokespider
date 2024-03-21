# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class PokespiderItem(Item):
    card_order  = Field(name = "Number")

    card_series = Field(name = "Series")

    card_name = Field(name = "Name")

    card_rarity = Field(name = "Rarity")

    low_price = Field(name = "Low Price")
    
    high_price = Field(name = "High Price")

    market_price = Field(name = "Market Price")

    median_price = Field(name = "Median Price")  

    foil_low_price = Field(name = "Foil Low Price")

    foil_market_price = Field(name = "Foil Market Price")

    foil_median_price = Field(name = "Foil Median Price")

    has_foils = Field(name = "Has Fields")

    has_normals = Field(name = "Has Normals")

    first_url = Field(name = "Url")

    error_encountered = Field(name = "Errors")


    def print_indented(self):
        print(f"    first_url:          {self['card_series']}")
        print(f"    card_number:        {self['card_order']}")
        print(f"    card_series:        {self['card_series']}")
        print(f"    card_rarity:        {self['card_rarity']}")
        print(f"    card_name:          {self['card_name']}")
        print(f"    low_price:          {self['low_price']}")
        print(f"    high_price:         {self['high_price']}")
        print(f"    market_price:       {self['market_price']}")
        print(f"    median_price:       {self['median_price']}")
        print(f"    has_foils:          {self['has_foils']}")
        print(f"    has_normals:        {self['has_normals']}")
        print(f"    error_encountered:  {self['error_encountered']}")