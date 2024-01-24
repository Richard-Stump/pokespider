# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class PokespiderItem(Item):
    card_series = Field()

    card_name = Field()

    card_type = Field()

    low_price = Field()
    
    high_price = Field()

    market_price = Field()

    median_price = Field()

    

