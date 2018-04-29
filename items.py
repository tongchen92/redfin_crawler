# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class RedfinTestItem(scrapy.Item):
    # define the fields for your item here like:
	search_date = scrapy.Field()
	street = scrapy.Field()
	citystatezip = scrapy.Field()
	price = scrapy.Field()
	HOA = scrapy.Field()
	year_built = scrapy.Field()
	SQFT = scrapy.Field()
	Beds = scrapy.Field()
	Baths = scrapy.Field()
	zipcode = scrapy.Field()
	rent = scrapy.Field()
	price_estimate = scrapy.Field()
	mortgage_pmt = scrapy.Field()
	insurance = scrapy.Field()
	tax = scrapy.Field()
	cashflow = scrapy.Field()
	total_pmt = scrapy.Field()

