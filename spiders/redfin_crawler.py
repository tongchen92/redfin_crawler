from scrapy.spiders import CrawlSpider, Rule, Request
from scrapy.linkextractors import LinkExtractor
from scrapy import Selector
from redfin_test.items import RedfinTestItem
from mortgage import Loan
from pyzillow2.pyzillow import ZillowWrapper, GetDeepSearchResults, GetUpdatedPropertyDetails
import re
import datetime
import pandas as pd

dmv_zip = pd.read_csv('dmv_zip2.csv')
dmv_ziplst = dmv_zip['zipcode'].tolist()

NOVA = 'https://www.redfin.com/state/Virginia/filter/property-type=house+condo+townhouse+multifamily,max-price=850k,max-days-on-market=3d,hoa=400,status=active,viewport=39.14078:38.76218:-77.02335:-77.46486/'
DC = 'https://www.redfin.com/county/436/DC/District-of-Columbia/filter/property-type=house+condo+townhouse+multifamily,max-price=950k,max-days-on-market=3d,status=active,viewport=39.00096:38.81154:-76.90993:-77.13069/'
now = datetime.datetime.now()

# zpid = 'X1-ZWz18oyj4hl6h7_3s95g'
zpid = 'X1-ZWz18oyuyo9ibv_3jtqm'
# zpid = 'X1-ZWz1g8avbxgjrf_aau4b'
zillow_data = ZillowWrapper(zpid)

tax_rate = .01
interest = 0.0435
loan_term = 30
insurance = .5
dp_percentage = 0.20


def get_rent(add, zip):
    try:
        deep_search_response = zillow_data.get_deep_search_results(add, zip, rentzestimate=True)
        zillow_result = GetDeepSearchResults(deep_search_response)
        rent = float(zillow_result.rentzestimate_amount)
    # price_prediction = zillow_result.zestimate_amount
    except:
        rent = None
        pass

    return rent  # ,price_prediction


def make_float(data):
    try:
        if data in ["", "-"]:
            return 0
        else:
            return float(data)
    except:
        return 0


def null_handle(data):
    try:
        if data == "-":
            return None
        else:
            return data
    except:
        return None


def get_insurance(SQFT):
    if SQFT:
        return min(insurance * float(SQFT) / 12, 160)
    else:
        return 80


def get_cashflow(rent, payment):
    if rent:
        return rent - payment
    else:
        return None


class RedfinSpider(CrawlSpider):
    name = "redfin"
    download_delay = 3.0
    url_domain = "https://www.redfin.com/zipcode/{0}/filter/max-days-on-market=3d,status=active/page-1"

    #zipcode_list = ['22031']

    zipcode_list = dmv_ziplst
    def url_constructor(domain, zipcodes):
        output = []
        for zipcode in zipcodes:
            output.append(domain.format(str(zipcode)))
        return output

    start_urls = url_constructor(url_domain, zipcode_list)

    # rules = (
    # Rule(LinkExtractor(allow=(), restrict_xpaths=('//a[@class="clickable goToPage"]')[0]), callback="parse_items", follow= True),
    # )

    def parse(self, response):

        pagesource = Selector(response)
        total_page = re.findall(r"\d+", response.xpath('//span[@class="pageText"]//text()').extract()[0])[1]
        current_page = re.findall(r"\d+", response.xpath('//span[@class="pageText"]//text()').extract()[0])[0]

        search_results = pagesource.xpath("//div[@class='MapHomeCardReact HomeCard']")

        # self.logger.info(u'User-Agent: {} {}'.format(request.headers.get('User-Agent'), request))

        for search in search_results:
            entry = RedfinTestItem()
            entry['search_date'] = now.day
            entry['price'] = float(''.join(
                re.findall(r"\d+", search.xpath('.//span[@data-rf-test-name="homecard-price"]//text()').extract()[0])))
            entry['street'] = search.xpath('.//span[@data-rf-test-id="abp-streetLine"]//text()').extract()[0]
            entry['citystatezip'] = search.xpath('.//span[@data-rf-test-id="abp-cityStateZip"]//text()').extract()[0]
            entry['zipcode'] = re.findall(r"\d+", search.xpath(
                './/span[@data-rf-test-id="abp-cityStateZip"]//text()').extract()[0])
            entry['HOA'] = ''.join(re.findall(r"\d+", search.xpath(
                './/span[@data-rf-test-name="homecard-amenities-hoa"]//text()').extract()[0]))
            entry['Beds'] = null_handle(re.findall(r"\d+", search.xpath('.//div[@class="value"]//text()').extract()[0]))
            entry['Baths'] = null_handle(
                re.findall(r"\d+", search.xpath('.//div[@class="value"]//text()').extract()[1]))
            entry['SQFT'] = ''.join(re.findall(r"\d+", search.xpath('.//div[@class="value"]//text()').extract()[2]))
            entry['year_built'] = search.xpath(
                './/span[@data-rf-test-name="homecard-amenities-year-built"]//text()').extract()
            entry['rent'] = get_rent(str(entry['street']), str(entry['zipcode']))
            entry['mortgage_pmt'] = float(
                Loan(entry['price'] * (1 - (dp_percentage)), interest, loan_term).monthly_payment)
            entry['insurance'] = get_insurance(entry['SQFT'])
            if entry['insurance'] == 0:
                entry['insurance'] == 60
            entry['tax'] = entry['price'] * tax_rate / 12
            entry['total_pmt'] = make_float(entry['HOA']) + entry['mortgage_pmt'] + entry['insurance'] + entry['tax']
            entry['cashflow'] = get_cashflow(entry['rent'], entry['total_pmt'])
            # #, entry['price_estimate']
            yield entry

        if int(total_page) > int(current_page):
            if int(current_page) == 1:
                next_page = response.url + "/page-2"
            else:
                next_page = re.sub(r"[page-][\d]+", "-" + str(int(current_page) + 1), response.url)
            yield Request(next_page, callback=self.parse)
