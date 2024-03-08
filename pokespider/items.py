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