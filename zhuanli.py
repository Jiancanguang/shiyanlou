# -*- coding: utf-8 -*-
# 此程序用来抓取 的数据
import codecs
import os

import requests
import time
import random
import re
from multiprocessing.dummy import Pool
from concurrent.futures import ThreadPoolExecutor
import csv
import json
import sys
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


pool = ThreadPoolExecutor(128)

class Spider(object):
	def __init__(self):
		self.done = set()
		try:
			with open('ids.txt') as f:
				for line in f:
					self.done.add(line.strip())
		except:
			pass
		self.init_csv()
		self.sleep = 2

	def replace(self, x):
		# 去除img标签,7位长空格
		removeImg = re.compile('<img.*?>| {7}|')
		# 删除超链接标签
		removeAddr = re.compile('<a.*?>|</a>')
		# 把换行的标签换为\n
		replaceLine = re.compile('<tr>|<div>|</div>|</p>')
		# 将表格制表<td>替换为\t
		replaceTD = re.compile('<td>')
		# 把段落开头换为\n加空两格
		replacePara = re.compile('<p.*?>')
		# 将换行符或双换行符替换为\n
		replaceBR = re.compile('<br><br>|<br>')
		# 将其余标签剔除
		removeExtraTag = re.compile('<.*?>', re.S)
		# 将&#x27;替换成'
		replacex27 = re.compile('&#x27;')
		# 将&gt;替换成>
		replacegt = re.compile('&gt;|&gt')
		# 将&lt;替换成<
		replacelt = re.compile('&lt;|&lt')
		# 将&nbsp换成''
		replacenbsp = re.compile('&nbsp;')
		# 将&#177;换成±
		replace177 = re.compile('&#177;')
		replace1 = re.compile('\s{2,}')
		x = re.sub(removeImg, "", x)
		x = re.sub(removeAddr, "", x)
		x = re.sub(replaceLine, "\n", x)
		x = re.sub(replaceTD, "\t", x)
		x = re.sub(replacePara, "", x)
		x = re.sub(replaceBR, "\n", x)
		x = re.sub(removeExtraTag, "", x)
		x = re.sub(replacex27, '\'', x)
		x = re.sub(replacegt, '>', x)
		x = re.sub(replacelt, '<', x)
		x = re.sub(replacenbsp, '', x)
		x = re.sub(replace177, u'±', x)
		x = re.sub(replace1, ' ', x)
		x = re.sub(re.compile('[\r\n]'), ' ', x)
		return x.strip()

	def init_csv(self):
		title = [u'专利号', u'标题', u'摘要', u'公开日期', u'国际专利分类', u'专利权人和代码']
		path = os.path.join(os.getcwd(), 'data.csv')
		if not os.path.exists(path):
			with open(path, 'w') as f:
				pass
				# f.write(codecs.BOM_UTF8)
			with open(path, 'a') as f:
				writer = csv.writer(f, lineterminator='\n')
				writer.writerow([x.encode('utf-8', 'ignore') for x in title])

	def get_detail(self, doc_id, doc_url):
		retry = 5
		while 1:
			try:
				headers = {
					'cookie': "remember_token=; wengine_vpn_ticket=12b255c7626a144f; NSC_202.120.224.150-443=ffffffffc970fe8945525d5f4f58455e445a4a42378b; refresh=0",
					'referer': "https://webvpn.fudan.edu.cn/http/77726476706e69737468656265737421f1e7518f69276d52710e82a297422f30a0c6fa320a29ae/full_record.do?product=DIIDW&search_mode=AdvancedSearch&qid=2&SID=8CWqOLCBCXWyqccKQSG&page=3&doc=21",
					'sec-fetch-mode': "navigate",
					'sec-fetch-site': "same-origin",
					'sec-fetch-user': "?1",
					'upgrade-insecure-requests': "1",
					'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"}
				text = requests.get(doc_url, verify=False, headers=headers, timeout=10).text
				p_title = re.compile(u'<td class="FullRecTitle">(.*?)</td>', re.S)
				title = self.replace(re.findall(p_title, text)[0])
				p_abs = re.compile(u'<span class="FR_label">Abstract: </span>(.*?)</td>', re.S)
				abstract = self.replace(re.findall(p_abs, text)[0])
				p_date = re.compile(
					u'<td valign="center" align="left">Publ\. Date</td>.*?<tr class="fr_data_row_td">.*?<td>.*?</td><td>(.*?)</td>',
					re.S)
				date = re.findall(p_date, text)[0]
				date = date.replace('&nbsp;', ' ')
				p_guoji = re.compile(u'International Patent Classification:.*?</span><a title=".*?>(.*?)</td>', re.S)
				try:
					guoji = self.replace(re.findall(p_guoji, text)[0])
				except:
					guoji = ''
				p_daima = re.compile(u'Patent Assignee Name\(s\) and Code\(s\):.*?</span>(.*?)</td>', re.S)
				try:
					daima = self.replace(re.findall(p_daima, text)[0])
				except:
					daima = ''
				result = [doc_id, title, abstract, date, guoji, daima]
				with open('data.csv', 'a') as f:
					writer = csv.writer(f, lineterminator='\n')
					writer.writerow([x.encode('utf-8', 'ignore') for x in result])
				print(u'%s 抓取成功' % doc_id)
				return True
			except Exception as e:
				retry -= 1
				if retry == 0:
					print(e)
					print(u'%s 抓取失败' % doc_id)
					return False
				else:
					print(u'%s 抓取失败重试' % doc_id)
					time.sleep(2)
					continue

	def get_detail_page(self, page):
		print(u'开始抓取第 %d 页' % page)
		url = "https://webvpn.fudan.edu.cn/http/77726476706e69737468656265737421f1e7518f69276d52710e82a297422f30a0c6fa320a29ae/summary.do"
		querystring = {"product": "DIIDW",
		               "parentProduct": "DIIDW",
		               "search_mode": "AdvancedSearch",
		               "parentQid": "",
		               "qid": "1",
		               "SID": "5FrdXwcXWEjhP5h54y6",
		               "update_back2search_link_param": "yes",
		               "page": str(page)}
		headers = {'host': "webvpn.fudan.edu.cn",
		           'connection': "keep-alive",
		           'upgrade-insecure-requests': "1",
		           'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
		           'sec-fetch-user': "?1",
		           'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
		           'sec-fetch-site': "same-origin",
		           'sec-fetch-mode': "navigate",
		           'referer': "https://webvpn.fudan.edu.cn/http/77726476706e69737468656265737421f1e7518f69276d52710e82a297422f30a0c6fa320a29ae/summary.do?product=DIIDW&parentProduct=DIIDW&search_mode=AdvancedSearch&parentQid=&qid=1&SID=6DJCCX9QJ9bZUBRLo5i&&update_back2search_link_param=yes&page=3",
		           'accept-encoding': "gzip, deflate, br",
		           'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
		           'cookie': 'remember_token=; wengine_vpn_ticket=12b255c7626a144f; NSC_202.120.224.150-443=ffffffffc970fe8945525d5f4f58455e445a4a42378b; refresh=0'}
		retry = 10
		while 1:
			try:
				s = requests.Session()
				text = s.get(url, verify=False, params=querystring, headers=headers, timeout=10).text
				p0 = re.compile(
					'<div class="search-results-checkbox">.*?</value>.*?</div>(.*?)<div>.*?<a class=.*?href="(.*?)"',
					re.S)
				items = re.findall(p0, text)
				if len(items) == 0:
					retry -= 1
					if retry == 0:
						print(u'第 %d 页抓取出错' % page)
						with open('error.txt', 'a') as f:
							f.write(str(page) + '\n')
						return None
					else:
						time.sleep(2)
						continue
				for item in items:  # url = https://webvpn.fudan.edu.cn/http/77726476706e69737468656265737421f1e7518f69276d52710e82a297422f30a0c6fa320a29ae/full_record.do?product=DIIDW&search_mode=AdvancedSearch&qid=2&SID=8CWqOLCBCXWyqccKQSG&page=3&doc=21#searchErrorMessage
					doc_id = item[0]
					doc_url = 'https://webvpn.fudan.edu.cn' + item[1].replace('&amp;', '&')
					if doc_id not in self.done:
						print(doc_id)
						pool.submit(self.get_detail, doc_id, doc_url)
						# result = self.get_detail(doc_id, doc_url)
						# if result:
						# 	self.done.add(doc_id)
						# 	with open('ids.txt', 'a') as f:
						# 		f.write(doc_id + '\n')
						# 	print(u'%s 抓取成功' % doc_id)
						# else:
						# 	print(u'%s 抓取失败' % doc_id)
					else:
						continue
				print(u'第 %d 页抓取完毕' % page)
				return None
			except Exception as e:
				retry -= 1
				print(e)
				if retry == 0:
					print(e)
					print(u'第 %d 页抓取出错' % page)
					with open('error.txt', 'a') as f:
						f.write(str(page) + '\n')
					return None
				else:
					time.sleep(3)
					continue

	def run(self):
		a = input('Please input start_page and end_page(eg:1-10):').strip()
		start, end = map(int, a.split('-'))
		page = start
		while page <= end:
			self.get_detail_page(page)
			page += 1
			time.sleep(random.uniform(1, 2))
		print(u'run over!!!')
		time.sleep(1000)


if __name__ == "__main__":
	spider = Spider()
	spider.run()