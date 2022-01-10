# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
from collections import OrderedDict
from scrapy.http import TextResponse

import random, re, requests

class stores_ebay_spider(scrapy.Spider):

	name = "stores_ebay_spider"

	use_selenium = True

	domain = 'https://www.ebay.com'
	next_count = 1
	total_count = 0
	result_data_list = []
	headers = ['Store name', 'ebay Item Number', 'is Child', 'Parent Sku', 'Variation theme', 'Variation value',
				 'UPC', 'Brand', 'Category path', 'Item location', 'Title', 'Price', 'Item specifics', 'Description',
				 'Weight', 'Length', 'Width', 'Height', 'Listing Url']

	# --------------- Get list of proxy-----------------------#
	proxy_text = requests.get('https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt').text
	list_proxy_temp = proxy_text.split('\n')
	list_proxy = []
	for line in list_proxy_temp:
		if line.strip() !='' and (line.strip()[-1] == '+' or line.strip()[-1] == '-'):
			ip = line.strip().split(':')[0].replace(' ', '')
			port = line.split(':')[-1].split(' ')[0]
			list_proxy.append('http://'+ip+':'+port)

	pass
	########################################################

	def __init__(self, *args, **kwargs):
		super(stores_ebay_spider, self).__init__(*args, **kwargs)

	def start_requests(self):
		filename = "basic_data/urls.csv"
		with open(filename, 'U') as f:
			for url in f.readlines():
				proxy = random.choice(self.list_proxy)
				print 'proxy: ' + proxy
				yield scrapy.Request(
									url=url.strip(),
									callback=self.parse_products_list,
									meta={'store_name': url, 'next_count': 1, 'proxy': proxy},
					  				errback=self.errCall)

		# yield scrapy.Request(
		# 			url='https://www.ebay.com/str/bestoffer01?rt=nc&_pgn=24',
		# 			callback=self.parse_products_list,
		# 			meta={'store_name': 'https://www.ebay.com/str/bestoffer01?rt=nc&_pgn=26', 'next_count': 24})
	def errCall(self, response):
		ban_proxy = response.request.meta['proxy']
		index_ban = self.list_proxy.index(ban_proxy)
		self.list_proxy.pop(index_ban)
		proxy = random.choice(self.list_proxy)
		if ban_proxy == proxy:
			index_ban = self.list_proxy.index(ban_proxy)
			if index_ban == 0 :
				index_ban +=1
			else:
				index_ban -=1
			proxy = self.list_proxy[index_ban]
			response.request.meta['proxy'] = proxy
		print proxy
		yield Request(response.request.meta['store_name'],
					  callback=self.parse_products_list,
					  meta={'proxy':proxy, 'store_name': response.request.url, 'next_count': response.request.meta['next_count']},
					  dont_filter=True,
					  errback=self.errCall)



	def parse_products_list(self, response):
		if '/str/' in response.url:
			product_links = response.xpath('//*[@class="s-item__link"]/@href').extract()
			print "\n####################################\n"
			print "products count: " + str(len(product_links))
			print "body: "
			# print response.body
			print "\n####################################\n"

			if len(product_links) == 0:
				# self.errCall(response)
				# return
				ban_proxy = response.request.meta['proxy']
				index_ban = self.list_proxy.index(ban_proxy)
				self.list_proxy.pop(index_ban)
				proxy = random.choice(self.list_proxy)
				print 'proxy: ' + proxy
				yield scrapy.Request(
									url=response.url,
									callback=self.parse_products_list,
									meta={'store_name': response.url, 'next_count': response.meta['next_count'], 'proxy': proxy},
					  				errback=self.errCall, dont_filter=True)
			else:

				for product_link in product_links:
					# yield Request(product_link, callback=self.parse_product, dont_filter=True, meta=response.meta, errback=self.err_product)
					yield Request(product_link, callback=self.parse_product, dont_filter=True, meta={'store_name':response.meta['store_name']})


			response.meta['next_count'] += 1
			# proxy = random.choice(self.list_proxy)
			# response.meta['proxy'] = proxy
			next_xpaths = response.xpath('//li[contains(@class,"ebayui-pagination__li ")]/a')
			for next_xpath in next_xpaths:

				if next_xpath.xpath('./text()').extract_first() == str(response.meta['next_count']):
					next_url = next_xpath.xpath('./@href').extract_first()

					print "next_url: " + next_url

					yield scrapy.Request(url=response.urljoin(next_url),
										 callback=self.parse_products_list,
										 meta=response.meta, errback=self.errCall)
		else:
			product_links = response.xpath('//*[@itemprop="name"]/@href').extract()
			print "products count: " + str(len(product_links))
			for product_link in product_links:
				yield Request(product_link, callback=self.parse_product, dont_filter=True, meta=response.meta, errback=self.err_product)

			next_url = response.xpath('//td[@class="next"]/a/@href').extract_first()
			if next_url:
				yield scrapy.Request(url=response.urljoin(next_url),
										 callback=self.parse_products_list,
										 meta=response.meta, dont_filter=True)

			# yield Request('https://www.ebay.com/itm/192525122776', callback=self.parse_product, dont_filter=True, meta=response.meta)

	def err_product(self, response):
		proxy = random.choice(self.list_proxy)
		yield Request(response.request.url, callback=self.parse_product, dont_filter=True,
					  meta={'proxy':proxy, 'store_name':response.request.meta['store_name']}, errback=self.err_product)


	def parse_product(self, response):
		self.total_count += 1
		print('Total Count: ' + str(self.total_count))

		item = OrderedDict()

		for key in self.headers:
			item[key] = ''
		for i in range(12):
			self.headers.append('Img {} Url'.format(i + 1))
			item['Img {} Url'.format(i + 1)] = ''

		item['Store name'] = response.meta['store_name']
		item['Title'] = response.xpath('//meta[@name="twitter:title"]/@content').extract_first()
		# price = response.xpath('//*[@itemprop="price"]/@content').extract_first()
		price = response.xpath('//*[@itemprop="price"]/text()').extract_first()
		if price:
			price = price.encode('latin1')
		item['Price'] = price
		item_number = response.url.split('?')[0].split('/')[-1]

		item['Listing Url'] = 'https://www.ebay.com/itm/{}'.format(item_number)
		item['Category path'] = '>'.join(response.xpath('//li[@itemprop="itemListElement"]/a/span/text()').extract())
		item['Item location'] = response.xpath('//*[@itemprop="availableAtOrFrom"]/text()').extract_first()
		item['Brand'] = response.xpath('//*[@itemprop="brand"]/span/text()').extract_first()
		if item_number == '142774657338':
			pass
		item['UPC'] = response.xpath('//*[@itemprop="gtin13"]/text()').extract_first()

		desc_url = response.xpath('//iframe[@id="desc_ifr"]/@src').extract_first()
		desc_content = requests.get(desc_url).text
		resp1 = TextResponse(url='',
                                body=desc_content,
                                encoding='utf-8')

		desc_str_list = []
		d_list = resp1.xpath('//div[@class="descdiv desc_details"]').extract_first()
		if not d_list:
			d_list = resp1.xpath('//div[@class="item-description"]').extract_first()
		if not d_list:
			d_list = resp1.xpath('//div[@id="patemplate_description"]').extract_first()
		if not d_list:
			d_list = resp1.xpath('//div[@id="ds_div"]').extract_first()

		re_list = []
		ls = d_list.split('>')
		for l in ls:
			l += '>'
			re_list.extend(re.findall('<div (.*)>', l))
			re_list.extend(re.findall('<span (.*)>', l))
			re_list.extend(re.findall('<p (.*)>', l))
			re_list.extend(re.findall('<font (.*)>', l))
			re_list.extend(re.findall('<ul (.*)>', l))
			re_list.extend(re.findall('<img (.*)>', l))
		for r in re_list:
			if not r:
				continue
			d_list = d_list.replace(r, '')

		item['Description'] = d_list

		print 'len: ' + str(len(d_list))
		# for d in d_list:
		# 	if d.root.tag == 'br':
		# 		d = '<br />'
		# 	elif d.root.tag == 'b':
		# 		d = '<b>' + d.xpath('.//text()').extract_first() + '</b>'
        #
		# 	else:
		# 		if not d.xpath('./text()').extract_first() or d.xpath('./text()').extract_first() == ' ':
		# 			continue
        #
		# 		d = d.xpath('./text()').extract_first()
		# 		d = d.strip()

			# try:
			# 	d = d.strip().encode('latin1')
			# except:
			# 	d = d.strip().encode('utf-8')
			# 	if not d:
			# 		continue
			# 	else:
			# 		d = d
			# 		pass
		# 	desc_str_list.append(d_list)
		# item['Description'] = '\n'.join(desc_str_list)

		itemAttrs = response.xpath('//*[@class="itemAttr"]//tr')

		itemAttr_list = []
		for itemAttr in itemAttrs:
			tds = itemAttr.xpath('./td')
			name = ''
			for i, td in enumerate(tds):
				td_strs = td.xpath('.//text()').extract()
				td_str_list = []
				for td_str in td_strs:
					td_str = td_str.strip()
					if not td_str:
						continue
					td_str_list.append(td_str)
				td_result_str = ' '.join(td_str_list)
				try:
					td_result_str = td_result_str.encode('latin1')
				except:
					td_result_str = td_result_str.encode('utf-8')
				if i % 2 == 0:
					name = td_result_str
				else:
					itemAttr_list.append('{} {}'.format(name, td_result_str))

					type_name = ''
					if 'weight' in name.lower():
						type_name = 'Weight'
					elif 'length' in name.lower():
						type_name = 'Length'
					elif 'width' in name.lower():
						type_name = 'Width'
					elif 'height' in name.lower():
						type_name = 'Height'

					if type_name:
						item[type_name] = td_result_str

		item['Item specifics'] = '\n'.join(itemAttr_list)

		for i, img_url in enumerate(response.xpath('//*[@class="lst icon"]//img/@src').extract()):
			if i > 11:
				break
			img_url = img_url.replace('/s-l64', '/s-l500')
			item['Img {} Url'.format(i + 1)] = img_url

		variation_xpaths = response.xpath('//*[@class="vi-msku-cntr "]')
		if variation_xpaths:
			item['Variation theme'] = variation_xpaths[0].xpath('./div/label/text()').extract_first().split(':')[0]
			item['is Child'] = 'no'
			item['ebay Item Number'] = item_number
			# yield scrapy.Request(url=desc_url,
			# 							 callback=self.parse_description,
			# 							 meta={'item': item}, dont_filter=True)
			# self.result_data_list.append(item)
			yield item

			item['is Child'] = 'yes'
			item['Parent Sku'] = item_number
			n = 1
			for variation_xpath in variation_xpaths:
				for j, option_str in enumerate(variation_xpath.xpath('./div/select/option/text()').extract()):
					if ('Select' in option_str) or ('out of stock' in option_str):
						continue
					item['ebay Item Number'] = '{}-{}'.format(item_number, n)
					item['Variation value'] = option_str
					n += 1
					# yield scrapy.Request(url=desc_url,
					# 					 callback=self.parse_description,
					# 					 meta={'item': item}, dont_filter=True)
					# self.result_data_list.append(item)
					yield item
		else:
			item['is Child'] = 'no'
			item['ebay Item Number'] = item_number

			# yield scrapy.Request(url=desc_url,
			# 							 callback=self.parse_description,
			# 							 meta={'item': item}, dont_filter=True)
			# self.result_data_list.append(item)
			yield item

	def parse_description(self, response):
		item = response.meta['item']
		desc_str_list = []
		d_list = response.xpath('//div[@class="descdiv desc_details"]//text()').extract()
		if not d_list:
			d_list = response.xpath('//div[@class="item-description"]//text()').extract()
		for d in d_list:
			if not d or d == ' ':
				continue
			d = d.strip().encode('utf-8')
			if not d:
				continue
			desc_str_list.append(d)
		item['Description'] = '\n'.join(desc_str_list)
		yield item



