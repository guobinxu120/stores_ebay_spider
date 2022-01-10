from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from scrapy.http import TextResponse
from scrapy.exceptions import CloseSpider
from scrapy import signals
from selenium.webdriver.chrome.options import Options
from datetime import date
import json
import time

class SeleniumMiddleware(object):

    def __init__(self, s):
        # self.exec_path = s.get('PHANTOMJS_PATH', './chromedriver.exe')
        self.exec_path = 'chromedriver.exe'
###########################################################

    @classmethod
    def from_crawler(cls, crawler):
        obj = cls(crawler.settings)

        crawler.signals.connect(obj.spider_opened,
                                signal=signals.spider_opened)
        crawler.signals.connect(obj.spider_closed,
                                signal=signals.spider_closed)
        return obj

###########################################################

    def spider_opened(self, spider):
        try:
            self.d = init_driver(self.exec_path)
        except TimeoutException:
            CloseSpider('PhantomJS Timeout Error!!!')

###########################################################

    def spider_closed(self, spider):
        self.d.quit()
###########################################################
    
    def process_request(self, request, spider):
        if spider.use_selenium:
            print "############################ Received url request from scrapy #####"

            try:
                self.d.get(request.url)
                

            except TimeoutException as e:            
                raise CloseSpider('TIMEOUT ERROR')
            
            # lastHeight = self.d.execute_script("return document.body.scrollHeight")
            # print "*** Last Height = ", lastHeight
            # while True:
            #     self.d.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            #     time.sleep(5)
            #     newHeight = self.d.execute_script("return document.body.scrollHeight")
            #     if newHeight == lastHeight:
            #         break
            #     lastHeight = newHeight

            # time.sleep(1)
            #
            # selector = None
            # city = None
            # button = None
            #
            # if not "categories" in spider.name:
            #
            #
            #
            #     resultData = ""
            #     next_count = 0
            #     while True:
            #
            #         response = TextResponse(url=self.d.current_url,
            #                     body=self.d.page_source,
            #                     encoding='utf-8')
            #         response.request = request.copy()
            #
            #         product_listing_container = response.xpath('//*[@class="product_listing_container"]')[0]
            #
            #         products = product_listing_container.xpath('.//*[@class="product"]')
            #
            #         print len(products)
            #         print "###########"
            #         print response.url
            #
            #         if not products: return
            #
            #         for i in products:
            #
            #
            #             item = {}
            #
            #             item['Vendedor'] = 140
            #             if not i.xpath('.//*[@class="promotionsApplied"]/@id').extract_first():
            #                 continue
            #             item['ID'] = i.xpath('.//*[@class="promotionsApplied"]/@id').extract_first().split('_')[0]
            #             item['Title'] = i.xpath('.//*[@class="product_name"]/a/text()').extract_first().strip()
            #             #item['Description'] = ''
            #
            #             price = i.xpath('.//*[contains(@id,"offerPrice_")]/text()').re(r'[\d.,]+')
            #             item['Price'] = ''
            #
            #             if price:
            #                 price[0] = price[0].replace('.', '')
            #                 price[0] = price[0].replace(',', '.')
            #                 # if price[0].count('.') == 2:
            #                 #     price[0] = price[0].replace('.', '', 1)
            #             else:
            #                 continue
            #             item['Price'] = price[0]
            #             item['Currency'] = 'CLP'
            #
            #             item['Category URL'] = response.meta['CatURL']
            #             item['Details URL'] = response.urljoin(i.xpath('.//*[@class="product_name"]/a/@href').extract_first().strip())
            #             item['Date'] = str(date.today())
            #
            #             resultData = resultData + json.dumps(item) + '+++++'
            #
            #         # count = len(response.xpath('//ul[@class="pagination"]/li'))
            #         next00 = response.xpath('//*[@class="right_arrow "]')
            #
            #
            #         if next00:
            #             selector = self.d.find_element_by_xpath('//*[@class="right_arrow "]')
            #             selector.click()
            #             time.sleep(1)
            #             continue
            #         break
            #     resp0 = TextResponse(url=self.d.current_url,
            #                         body=resultData, #self.d.page_source,
            #                         encoding='utf-8')
            #     resp0.request = request.copy()
            #
            #     return resp0


            resp1 = TextResponse(url=self.d.current_url,
                                body=self.d.page_source,
                                encoding='utf-8')
            resp1.request = request.copy()
            
            return resp1

###########################################################
###########################################################

def init_driver(path):

    chrome_options = Options()
    chrome_options.add_argument("window-size=3000,3000")
    chrome_options.add_argument("window-position=-10000,0")
    d = webdriver.Chrome(executable_path=path, chrome_options=chrome_options)
    #d = webdriver.PhantomJS(executable_path=path)
    d.set_page_load_timeout(30)

    return d