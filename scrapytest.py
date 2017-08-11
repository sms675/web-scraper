# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 14:02:35 2017
Paste this:
CIK_code =  '0001166126'    
data = {'CIK': CIK_code}
fr = scrapy.FormRequest.from_response(response, formid='fast-search', formdata = data)
fetch(fr)
table_loc = '/html/body/div[4]/div[4]/table'
relative_link = response.xpath(table_loc + '/tr[' + str(2) + ']/td[2]/a/@href').extract_first()
absolute_link = 'https://www.sec.gov' + str(relative_link)
fetch(absolute_link)

table_loc2 = '/html/body/div[4]/div[2]/div[1]/table'
doc_count = len(response.xpath(table_loc2 +'/tr').extract())
doc_space = str(response.xpath(table_loc2 + '/tr[' + str(2) + ']/td[3]/a/@href').extract_first())

table_loc = '/html/body/div[4]/div[4]/table'  # location of table in new link


@author: stephen
"""
import os
import scrapy
import time
from scrapy.crawler import CrawlerProcess
 
class SecSpider(scrapy.Spider):
    name = 'secspider'
    allowed_domains = ['www.sec.gov']
    login_url = 'https://www.sec.gov/edgar/searchedgar/companysearch.html'
    start_urls = [login_url]
    download_delay = 5
    output_dir = '/home/stephen/Desktop/ETNfiles'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  #creates new directory to store files
    
    # Fills in CIK field in start url    
    def parse(self, response):
        CIK_code =  '0001166126'    
        data = {'CIK': CIK_code}
        return [scrapy.FormRequest.from_response(response, formid='fast-search', formdata = data, callback = self.parse_docs)]
	
    #counts and extracts document links  
    def parse_docs(self,response): 
        doc_list = []    
        for newlink in range(2,9):  #42 is max?
            table_loc = '/html/body/div[4]/div[4]/table'  # location of table in new link

            relative_link = response.xpath(table_loc + '/tr[' + str(newlink) + ']/td[2]/a/@href').extract_first()
            absolute_link = 'https://www.sec.gov' + str(relative_link)
            filing = str(response.xpath(table_loc + '/tr[' + str(newlink) + ']/td[1]/text()').extract()[0]) 
            try:
                description = (str(response.xpath(table_loc + '/tr[' + str(newlink) + ']/td[3]/text()').extract()[0]) + 
                        response.xpath(table_loc + '/tr[' + str(newlink) + ']/td[3]/text()').extract()[1].encode('utf-8'))
            except  UnicodeEncodeError:
                print("Description Exception")
            filing_date = str(response.xpath(table_loc + '/tr[' + str(newlink) + ']/td[4]/text()').extract()[0])
            filenum = (str(response.xpath(table_loc + '/tr[' + str(newlink) + ']/td[5]/a/text()').extract()[0]) +
                        response.xpath(table_loc + '/tr[' + str(newlink) + ']/td[5]/text()').extract()[0].encode('utf-8'))
            doc_info = [absolute_link,filing,description,filing_date,filenum]
            request = scrapy.Request(absolute_link, callback = self.parse_file)
            request.meta['doc_info'] = doc_info
            yield request
        
    #downloads text file from doc/
    def parse_file(self,response):
        table_loc2 = '/html/body/div[4]/div[2]/div[1]/table'
        doc_count = len(response.xpath(table_loc2 +'/tr').extract())
        final_info = response.meta['doc_info']                

        for table_val in range(2,doc_count):
            doc_space = str(response.xpath(table_loc2 + '/tr[' + str(table_val) + ']/td[3]/a/@href').extract_first())
            if (doc_space[-3:] == 'txt'or doc_space[-3:] == 'htm'):
                absolute_link2 = 'https://www.sec.gov' + str(doc_space)
                sub_description = str(response.xpath(table_loc2 + '/tr[' + str(table_val) + ']/td[2]/text()').extract_first())
                final_info.append(sub_description)
                request = scrapy.Request(absolute_link2, callback = self.to_text)
                request.meta['desc'] = final_info               
                yield request
            
            
    def to_text(self, response):
        #sec_file = open("newfile.txt","w+")
        #make string object with all document labels..named by date and filing.
    #may need to sort via date.
        #sec_file.write("add string here")
        #sec_file.close()
        #title = response.xpath('//title/text()').extract()
        desc = response.meta['desc']
        self.logger.info("Visited %s", response.url)
        print (response.url)
        print (desc)
        print time.time()
            
            
        #time.sleep(2)  sleep per document click
    
        
'''
            
 yield{
        'doc_count' : len(response.xpath('/html/body/div[4]/div[4]/table/tr'))
        return response.xpath('//title/text()').extract()
        }
        #when theres no return
        def to_text(self, response):
        title = response.xpath('//title/text()').extract()
        self.logger.info("Visited %s", response.url)
'''        
        
process = CrawlerProcess()
process.crawl(SecSpider)
process.start() 
