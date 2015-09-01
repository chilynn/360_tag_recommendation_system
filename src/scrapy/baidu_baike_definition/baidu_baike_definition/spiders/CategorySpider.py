#encoding=utf-8
import scrapy
from scrapy.selector import Selector
from scrapy.spider import BaseSpider
from scrapy.http import Request
from baidu_baike_definition.items import BaiduBaikePageItem

#command "scrapy crawl baidu_baike_definition --logfile=scrapy.log -o crawl_data/definition.json -t json"
class CategorySpider(BaseSpider):

	name = "baidu_baike_definition"
	domain = "baike.baidu.com"

	#添加get请求
	def start_requests(self):
		infile = open('../../../data/all_word.txt','rb')
		requests = []
		#获取候选词
		row_index=0
		for row in infile:
			# row_index += 1
			# if row_index > 100:
			# 	break
			category = row.split(',')[0].decode('utf-8')
			request_url = u"http://baike.baidu.com/search?word="+category+"&rn=3"+"&pn=0"
			requests.append(scrapy.FormRequest(request_url,callback=lambda response,category=category:self.parseSearchPage(response,category)))
		print 'crawling'
		return requests

	#处理搜索列表页面
	def parseSearchPage(self,response,category):
		print category
		for search_result_item in response.xpath('//a[@class="result-title"]'):
			result_item_name = ''.join(search_result_item.xpath('.//text()').extract())
			# print result_item_name
			if result_item_name == category+u'_百度百科':
				url = search_result_item.xpath('@href').extract()[0]
				yield Request(url=url,meta={'is_to_ambiguous':1},callback=lambda response,category=category:self.parseDetailPage(response,category))

	#处理详情页面
	def parseDetailPage(self,response,category):
		is_to_ambiguous = response.meta['is_to_ambiguous']

		item = BaiduBaikePageItem()
		
		item['query_category'] = category

		#歧义提示
		ambiguous_tips = ''.join(response.xpath('//span[@class="view-tip-panel"]//text()').extract()).encode('utf-8')
		item['ambiguous_tips'] = ambiguous_tips

		#标题
		title = ''.join(response.xpath('//span[@class="lemmaTitleH1"]/text()').extract()).encode('utf-8')
		item['title'] = title
		
		#标题备注
		title_note = ''.join(response.xpath('//span[@class="lemmaTitleH1"]//span//text()').extract()).encode('utf-8')
		item['title_note'] = title_note

		#百度结构化标签
		structure_tag = {}
		for tag_record in response.xpath('//div[@class="baseInfoWrap"]//div[@class="biItem"]//div[@class="biItemInner"]'):
			tag_key = ''.join(tag_record.xpath('.//span[@class="biTitle"]//text()').extract()).encode('utf-8')
			tag_value = ''.join(tag_record.xpath('.//div[@class="biContent"]//text()').extract()).encode('utf-8')
			structure_tag[tag_key] = tag_value
		item['structure_tag'] = structure_tag

		#摘要
		abstract = ''.join(response.xpath('//div[@class="card-summary-content"]//div[@class="para"]//text()').extract()).encode('utf-8')
		abstract_link = ''.join(response.xpath('//div[@class="card-summary-content"]//div[@class="para"]//a//text()').extract()).encode('utf-8')
		abstract_bold = ''.join(response.xpath('//div[@class="card-summary-content"]//div[@class="para"]//b//text()').extract()).encode('utf-8')
		item['abstract'] = abstract
		item['abstract_link'] = abstract_link
		item['abstract_bold'] = abstract_bold

		#正文内容
		item['content'] = ''.join(response.xpath('//div[@class="para"]//text()').extract()).encode('utf-8')
		item['content_link'] = ''.join(response.xpath('//div[@class="para"]//a//text()').extract()).encode('utf-8')
		item['content_bold'] = ''.join(response.xpath('//div[@class="para"]//bold//text()').extract()).encode('utf-8')				

		#多义词处理
		if is_to_ambiguous:
			is_only = 1
			for ambiguous_url in response.xpath('//div[@class="polysemeBodyCon"]//a//@href').extract():
				is_only = 0
				ambiguous_url = "http://"+self.domain+ambiguous_url
				yield Request(url=ambiguous_url,meta={'is_to_ambiguous':0},callback=lambda response,category=category:self.parseDetailPage(response,category))
			item['is_only'] = is_only
		else:
			item['is_only'] = 0
		
		yield item


