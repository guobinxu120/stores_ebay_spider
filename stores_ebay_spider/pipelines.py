# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy import signals
import csv, os, xlsxwriter

class StoresEbayDeWerkzeugstorePipeline(object):
    def __init__(self):
        pass

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline


    def spider_opened(self, spider):
        pass
    def process_item(self, item, spider):
        return item

    def spider_closed(self, spider):
        filepath = 'rs_online_Batteries.xlsx'
        if os.path.isfile(filepath):
            os.remove(filepath)
        workbook = xlsxwriter.Workbook(filepath)
        sheet = workbook.add_worksheet('rs_online')
        data = spider.result_data_list
        headers = spider.headers
        flag =True
        # headers = []
        print('---------------Writing in file----------------------')
        print('total row: ' + str(len(data)))

        for index, value in enumerate(data):
            if flag:
                for col, val in enumerate(headers):
                    # headers.append(val)
                    sheet.write(index, col, val)
                flag = False
            for col, key in enumerate(headers):
                if key in value.keys():
                    val = value[key]
                    if val is not None:
                        try:
                            val = val.encode('latin1')
                            val = val.encode('utf-8')
                        except:
                            pass
                        # val = val.encode('utf-8')
                    sheet.write(index+1, col, val)
                else:
                    sheet.write(index+1, col, '')
            print('row :' + str(index))

        workbook.close()
        # filepath = 'output_data/{}_result.csv'.format(spider.name)
        # data = spider.result_data_list
        # headers = spider.headers
        #
        # f1 = open(filepath, "wb")
        # writer = csv.writer(f1, delimiter=',',quoting=csv.QUOTE_ALL)
        # writer.writerow(headers)
        #
        # for item in data:
        #     d = item.values()
        #     new_d = []
        #     for dd in d:
        #         try:
        #             new_d.append(dd.encode('utf-8'))
        #         except:
        #             new_d.append(dd)
        #     writer.writerow(new_d)
        # f1.close()