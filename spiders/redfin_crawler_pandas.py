from scrapy.spiders import CrawlSpider, Rule, Request
from scrapy.linkextractors import LinkExtractor
from scrapy import Selector
from redfin_test.items import RedfinTestItem
from mortgage import Loan
from pyzillow2.pyzillow import ZillowWrapper, GetDeepSearchResults, GetUpdatedPropertyDetails
import pandas as pd

zpid = 'X1-ZWz18oyuyo9ibv_3jtqm'
#'X1-ZWz1g8avbxgjrf_aau4b'
zillow_data = ZillowWrapper(zpid)

import re

def get_rent (add,zip):
	try:
		deep_search_response= zillow_data.get_deep_search_results(add,zip,rentzestimate=True)
		zillow_result = GetDeepSearchResults(deep_search_response)
		rent = float(zillow_result.rentzestimate_amount)
		#price_prediction = zillow_result.zestimate_amount
	except:
		rent = None
		pass

	return rent#,price_prediction
		
def make_float (data):
	try:
		if data in ["","-"]:
			return 0
		else:
			return float(data)
	except:
		return 0
		
def get_cashflow (rent, payment):
	if rent:
		return rent-payment
	else:
		return None

class RedfinSpider(CrawlSpider):
		
	name = "redfin_pd"
	download_delay = 2.0
	url_domain = "https://www.redfin.com/zipcode/{0}/filter/max-days-on-market=1mo,status=active/page-1"

	zipcode_list = ["30534"]#, "30506", "30041", "30542", "30518", "30126"]
	#zipcode_list = [60614]#, 60642, 60607, 60605]
	def url_constructor(domain, zipcodes):
		output = []
		for zipcode in zipcodes:
			output.append(domain.format(str(zipcode)))
		return output
	
	start_urls = url_constructor(url_domain,zipcode_list)
	
	# rules = (
        # Rule(LinkExtractor(allow=(), restrict_xpaths=('//a[@class="clickable goToPage"]')[0]), callback="parse_items", follow= True),
    # )
	
	def parse(self, response):
		
		pagesource = Selector(response)

		tax_rate = .01
		interest = 0.0435
		loan_term = 30 
		insurance = .5
		dp_percentage = 0.25
		
		total_page = re.findall(r"\d+", response.xpath('//span[@class="pageText"]//text()').extract()[0])[1]
		current_page = re.findall(r"\d+", response.xpath('//span[@class="pageText"]//text()').extract()[0])[0]
		
		search_results = pagesource.xpath("//div[@class='MapHomeCardReact HomeCard']")
		
		for search in search_results:
			entry = RedfinTestItem()
			entry['price'] = float(''.join(re.findall(r"\d+",search.xpath('.//span[@data-rf-test-name="homecard-price"]//text()').extract()[0])))
			entry['street'] = search.xpath('.//span[@data-rf-test-id="abp-streetLine"]//text()').extract()[0]
			entry['citystatezip'] = search.xpath('.//span[@data-rf-test-id="abp-cityStateZip"]//text()').extract()[0]
			entry['zipcode'] = re.findall(r"\d+",search.xpath('.//span[@data-rf-test-id="abp-cityStateZip"]//text()').extract()[0])
			entry['HOA'] = ''.join(re.findall(r"\d+",search.xpath('.//span[@data-rf-test-name="homecard-amenities-hoa"]//text()').extract()[0]))
			entry['Beds'] = ''.join(search.xpath('.//div[@class="value"]//text()').extract()[0])
			entry['Baths'] = ''.join(search.xpath('.//div[@class="value"]//text()').extract()[1])
			entry['SQFT'] = ''.join(search.xpath('.//div[@class="value"]//text()').extract()[2])
			
			entry['year_built'] = search.xpath('.//span[@data-rf-test-name="homecard-amenities-year-built"]//text()').extract()[0]
			entry['rent']= get_rent(str(entry['street']), str(entry['zipcode']))
			entry['mortgage_pmt'] = float(Loan(entry['price']*1-(dp_percentage), interest, loan_term).monthly_payment)
			entry['insurance'] = insurance*make_float(entry['SQFT'])
			if entry['insurance'] ==0:
				entry['insurance'] ==60
			entry['tax'] = entry['price']*tax_rate/12
			entry['total_pmt'] = make_float(entry['HOA']) + entry['mortgage_pmt'] + entry['insurance'] + entry['tax']
			entry['cashflow'] = get_cashflow(entry['rent'],entry['total_pmt'])
			#, entry['price_estimate'] 
			yield entry

		if int(total_page)>int(current_page):
			if int(current_page) == 1:
				next_page = response.url + "/page-2"
			else:
				next_page = re.sub(r"[page-][\d]+", "-"+str(int(current_page)+1), response.url)
			yield Request(next_page, callback=self.parse)
			

		