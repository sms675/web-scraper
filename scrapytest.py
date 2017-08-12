# -*- coding: utf-8 -*-
"""
Web scraper built using the Scrapy framework
@author: stephen schneider

"""
import os
import scrapy
import time
from scrapy.crawler import CrawlerProcess
 
class SecSpider(scrapy.Spider):
    name = 'sec_spider'
    allowed_domains = ['www.sec.gov']
    login_url = 'https://www.sec.gov/edgar/searchedgar/companysearch.html'
    start_urls = [login_url]
    #set rate of requests to prevent sending too many at once.
    download_delay = 5
    output_dir = '/home/stephen/Desktop/ETNfiles'
    
    #creates new directory to store output files if folder is missing
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  
    
    # Fills in CIK field in start url.. build GUI to fill this in
    def parse(self, response):
        CIK_code =  '0001166126'    
        data = {'CIK': CIK_code}
        return [scrapy.FormRequest.from_response(response, formid='fast-search', formdata = data, callback = self.parse_docs)]
	
    #counts and extracts document links from followed link : 
    #https://www.sec.gov/cgi-bin/browse-edgar?owner=exclude&action=getcompany&Find=Search&CIK=0001166126
    def parse_docs(self,response): 
        #Cycle through each document filing in the table... 42 is max?
        for newlink in range(2,9):  
            #location of table in new link
            table1_loc = '/html/body/div[4]/div[4]/table'  
            #relative link of document location
            relative_link = response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[2]/a/@href').extract_first()
            absolute_link = 'https://www.sec.gov' + str(relative_link)
            
            
            #stores filing name of link
            filing = str(response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[1]/text()').extract()[0]) 
            #stores description of link, accounts for exceptions when there is only one line of description
            try:
                description = (str(response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[3]/text()').extract()[0]) + 
                                   response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[3]/text()').extract()[1].encode('utf-8'))
            except  UnicodeEncodeError:
                print("Description Exception")
            #stores filing date
            filing_date = str(response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[4]/text()').extract()[0])
            #stores file number
            filenum = (str(response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[5]/a/text()').extract()[0]) +
                           response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[5]/text()').extract()[0].encode('utf-8'))
            
            
            #makes a list of all the stored information
            doc_info = [absolute_link,filing,description,filing_date,filenum]
            
            #requests next link in sequence.
            request = scrapy.Request(absolute_link, callback = self.parse_file)
            
            #sends all stored information from this webpage to the next requested page
            request.meta['doc_info'] = doc_info
            yield request
        
        
    #Looks for sub document links and info from each document previously scraped, sends final request
    def parse_file(self,response):
        #location of new (final) table
        table2_loc = '/html/body/div[4]/div[2]/div[1]/table'
        #counts size of table for for loop
        doc_count = len(response.xpath(table2_loc +'/tr').extract())
        #stores all info from previous link into final_info
        final_info = response.meta['doc_info']                

        for table_val in range(2,doc_count):
            #gets relative string of final document 
            final_doc = str(response.xpath(table2_loc + '/tr[' + str(table_val) + ']/td[3]/a/@href').extract_first())
            #only do something if the file extension is .txt or .htm.
            if (final_doc[-3:] == 'txt'or final_doc[-3:] == 'htm'):
                final_absolute_link = 'https://www.sec.gov' + str(final_doc)
                sub_description = str(response.xpath(table2_loc + '/tr[' + str(table_val) + ']/td[2]/text()').extract_first())
                #add sub_description to final_info passed from previous link                
                final_info.append(sub_description)#
                request = scrapy.Request(final_absolute_link, callback = self.to_text)
                request.meta['total_description'] = final_info               
                yield request
    '''
    Function 'to_text' is still in progress, we are in the process of extracting the text from the final 
    documents and comparing them with the strings ' ETN ' and ' Exchange Traded ' to classify documents as 
    ETN related. We must search through the txt or html files line by line... can extract them with response.xpath('/html')
    '''
    
    def to_text(self, response):
        #sec_file = open("newfile.txt","w+")
        #make string object with all document labels..named by date and filing.
        #may need to sort via date.
        #sec_file.write("add string here")
        #sec_file.close()
        #title = response.xpath('//title/text()').extract()
    
          
   
        total_description = response.meta['total_description']
        self.logger.info("Visited %s", response.url)
        print (response.url)
        print (total_description)
        print time.time()
            
           
        
process = CrawlerProcess()
process.crawl(SecSpider)
process.start() 
