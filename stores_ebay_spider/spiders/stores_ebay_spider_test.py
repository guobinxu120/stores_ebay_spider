# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
from collections import OrderedDict
import re, json, time

class stores_ebay_spider(scrapy.Spider):

	name = "stores_ebay_spider111"

	domain = 'https://www.ebay.com'
	next_count = 1
	total_count = 0
	nextCountJson = {}
	item_keys = ['Store name', 'ebay Item Number', 'is Child', 'Parent Sku', 'Variation theme', 'Variation value',
				 'UPC', 'Brand', 'Category path', 'Item location', 'Title', 'Price', 'Item specifics', 'Description',
				 'Weight', 'Length', 'Width', 'Height', 'Listing Url']

	def __init__(self, *args, **kwargs):
		super(stores_ebay_spider, self).__init__(*args, **kwargs)

	def start_requests(self):
		filename = "basic_data/urls.csv"
		with open(filename, 'U') as f:
			for url in f.readlines():
				yield scrapy.Request(
					url=self.domain + url.strip(),
					callback=self.parse_products_list,
					dont_filter=True,
					meta={'store_name': url, 'next_count': 1},
					errback=self.errCall)

	def parse_products_list(self, response):
		if 'stores.ebay.com' not in response.url:
			product_links = response.xpath('//*[@class="s-item__link"]/@href').extract()
			# for product_link in product_links:
			# 	yield Request(product_link.replace('//www.', '//m.'), callback=self.parse_product, dont_filter=True, meta=response.meta)

			# ------------------- test -----------------------#
			# yield Request(product_links[0], callback=self.parse_product, dont_filter=True, meta=response.meta)
			yield Request('https://m.ebay.com/itm/CJH-198A-3-50-Miles-1080P-HD-Digital-Aluminum-Foil-Antennas-with-One-IEC-Head-PU/283009436956?hash=item41e4ad4d1c:g:-r8AAOSwVvRbI6q6', callback=self.parse_product, dont_filter=True, meta=response.meta)
			# -----------------------------------------------#
			# si = response.body.split('si=')[-1].split(',')[0]
			# response.meta['next_count'] += 1
			# header = {':authority': 'www.ebay.com', 'upgrade-insecure-requests': '1', 'cookie': si}
			# next_url = '{}{}?_pgn={}'.format(self.domain, response.meta['store_name'], response.meta['next_count'])
			# yield scrapy.Request(url=response.urljoin(next_url),
			# 					 headers=header,
			# 					 callback=self.parse_products_list,
			# 					 meta=response.meta, dont_filter=True)


			# next_xpaths = response.xpath('//li[contains(@class,"ebayui-pagination__li ")]/a')
			# response.meta['next_count'] += 1
			# for next_xpath in next_xpaths:
			# 	if next_xpath.xpath('./text()').extract_first() == str(response.meta['next_count']):
			# 		next_url = next_xpath.xpath('./@href').extract_first()
			# 		yield scrapy.Request(url=response.urljoin(next_url),
			# 							 callback=self.parse_products_list,
			# 							 dont_filter=True,
			# 							 meta=response.meta)


	def parse_product(self, response):
		self.total_count += 1
		print('Total count: ' + str(self.total_count))

		item = OrderedDict()

		for key in self.item_keys:
			item[key] = ''
		for i in range(12):
			item['Img {} Url'.format(i + 1)] = ''

		body_str = 'var viData = ' + response.body.split('var viData = ')[-1].split('viData.pageId=')[0]

		first_json_data = json.loads(re.findall('var viData = (.*);',body_str)[0])

		item['Store name'] = response.meta['store_name']
		item['Title'] = response.xpath('//meta[@name="twitter:title"]/@content').extract_first()
		price = response.xpath('//*[@class="vi-bin-primary-price__main-price"]/span/text()').extract_first()
		if not price:
			price = response.xpath('//*[contains(@class,"msku-price") and contains(@class,"msku-pad")]/text()').extract_first()
		if not price:
			price = first_json_data['itemTeaser']['price']['price']
			if price and (price is not None):
				price = price.split(' ')[-1]
			else:
				pass
		if price:
			item['Price'] = price.replace('&pound;', 'GBP')

		item_number = response.url.split('?')[0].split('/')[-1]

		item['Listing Url'] = 'https://www.ebay.com/itm/{}'.format(item_number)
		item['Category path'] = response.xpath('//meta[@name="description"]/@content').extract_first().split('|')[1].encode('latin1')



		item_location = response.xpath('//div[@class="detailsEntry"]/div[@class="valueRight shipDispValue"]/text()').extract_first()
		item['Item location'] = item_location

		itemDetails = first_json_data['viDetailsModel']['viSpecificsModel']['itemDetails']
		spec_data_list = []
		for itemDetail in itemDetails:
			try:
				name = itemDetail['name'].encode('latin1')
			except:
				name = itemDetail['name'].encode('utf-8')
			try:
				val = itemDetail['value'].encode('latin1')
			except:
				val = itemDetail['value'].encode('utf-8')

			spec_data_list.append('{}:{}'.format(name, val))

			type_name = ''
			if 'weight' in name.lower():
				type_name = 'Weight'
			elif 'length' in name.lower():
				type_name = 'Length'
			elif 'width' in name.lower():
				type_name = 'Width'
			elif 'height' in name.lower():
				type_name = 'Height'
			elif 'brand' in name.lower():
				type_name = 'Brand'
			elif 'ean' in name.lower():
				type_name = 'UPC'

			if type_name:
				item[type_name] = val
		item['Item specifics'] = '\n'.join(spec_data_list)

		viImageGallery = first_json_data['viImageGallery']['imgGalleryModel']
		for i, img_data in enumerate(viImageGallery):
			if i > 11:
				break
			item['Img {} Url'.format(i + 1)] = img_data['singleViewImg']

		variation_xpaths = response.xpath('//*[@class="trait-ctr"]')
		if variation_xpaths:
			item['is Child'] = 'yes'
			item['Parent Sku'] = item_number
			n = 1
			for variation_xpath in variation_xpaths:
				item['Variation theme'] = variation_xpath.xpath('./div/label/text()').extract_first().split(':')[0]

				for j, option_str in enumerate(variation_xpath.xpath('./div/select/option/text()').extract()):
					if 'Select' in option_str or ('out of stock' in option_str):
						continue
					item['ebay Item Number'] = '{}-{}'.format(item_number, n)
					item['Variation value'] = option_str
					n += 1

					yield item
		else:
			if 'viVariation' in first_json_data.keys():
				variation_datas = first_json_data['viVariation']
				variation_datas = variation_datas['traits']
				item['is Child'] = 'yes'
				item['Parent Sku'] = item_number
				n = 1
				for variation_data in variation_datas:
					item['Variation theme'] = variation_data['name']

					for j, option in enumerate(variation_data['traitVals']):
						item['ebay Item Number'] = '{}-{}'.format(item_number, n)
						item['Variation value'] = option['name']
						n += 1

						yield item
			else:
				item['is Child'] = 'no'
				item['ebay Item Number'] = item_number

				yield item





