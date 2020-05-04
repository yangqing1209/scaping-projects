#! encoding=utf-8

import time
import re
import requests
import parsel
from pymongo import MongoClient

class Kr36Scraping:
    '''
    爬取36氪videos全部视频及详细信息：676页，共14000条。从2017年8-11到现在。
    存入Mongodb数据库
    '''
    def __init__(self):
        self.url = ['https://36kr.com/video',
                    'https://gateway.36kr.com/api/mis/nav/video/flow']
        self.client = MongoClient('127.0.0.1:27017')
        self.videos = self.client['kr']['videos']
        self.page = 1
        self.total = 0

    def get_first_page(self):
        '''
        :return: pageCallback 每页有下一页的callback信息
        :return: text  第一页的文本信息
        '''
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko)"
                          " Chrome/72.0.3622.0 Safari/537.36",
        }
        text = requests.get(url=self.url[0], headers=headers).text
        pageCallback = re.findall('"pageCallback":"(.*?)",', text)[0]
        return pageCallback, text

    def get_page(self, pageCallback):
        '''
        :param pageCallback: 每页的pageCallback参数，来源于上一页
        :return: None
        '''
        self.page += 1
        print(f'第{self.page}页')
        timestamp = int(time.time() * 1000)
        data = {'param': {
            "pageCallback": pageCallback,
            "pageEvent": 1,
            "pageSize": 20,
            "platformId": 2,
            "siteId": 1},
            "partner_id": "web",
            "timestamp": timestamp,
        }
        headers = {
            "origin": "https://36kr.com",
            "referer": "https://36kr.com/video",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko)"
                          " Chrome/72.0.3622.0 Safari/537.36",
        }
        res = requests.post(url=self.url[1], json=data, headers=headers).json()
        self.parse_pages(res)
        pageCallback = res['data']['pageCallback']
        hasNextPage = res['data']['hasNextPage']
        if not hasNextPage:
            print('all finished')
            return
        time.sleep(1)
        self.get_page(pageCallback)

    def parse_first_page(self, text):
        '''
        第一页单独从html中提取数据
        '''
        selector = parsel.Selector(text)
        div_list = selector.xpath("//div[contains(@class,'video-catalog-flow-list')]/div")
        for div in div_list:
            di = {}
            di['itemId'] = div.xpath(
                './div/div[2]/div[1]/a[1]/@href').get().split('/')[-1]
            di['route'] = 'https://36kr.com/video/' + di['itemId']
            di['widgetTitle'] = div.xpath('./div/div[2]/div[1]/a[1]/text()').get()
            di['summary'] = div.xpath('./div/div[2]/div[1]/a[2]/text()').get()
            di['authorName'] = div.xpath('./div/div[2]/div[2]/a/text()').get()
            di['authorRoute'] = "https://36kr.com/user/" + \
                                div.xpath('./div/div[2]/div[2]/a/@href').get().split('/')[-1]
            di['publishTime'] = div.xpath('./div/div[2]/div[2]/span//text()').get()
            di['duration'] = div.xpath('.//span[@class="video-time-length"]/text()').get()
            self.save_data(di)

    def parse_pages(self,res):
        '''
       从json数据中解析数据
        '''
        li = res['data']['itemList']
        for i in li:
            di = {}
            di['itemId'] = i['itemId']
            di['route'] = 'https://36kr.com/video/' + str(di['itemId'])
            di['widgetTitle'] = i['templateMaterial']['widgetTitle']
            di['summary'] = i['templateMaterial']['summary']
            di['authorName'] = i['templateMaterial']['authorName']
            di['authorRoute'] = i['templateMaterial']['authorRoute'].split('=')[-1]
            timeStamp = int(i['templateMaterial']['publishTime']) / 1000
            di['publishTime'] = self.time_data(timeStamp)
            try:
                m, s = divmod(int(i['templateMaterial']['duration']), 60)
                di['duration'] = f"{m}:{s}"
            except Exception as e:
                di['duration'] = '0-0'
            self.save_data(di)

    @staticmethod
    def time_data(time_sj):
        data_sj = time.localtime(time_sj)
        time_str = time.strftime("%Y-%m-%d ", data_sj)
        return time_str

    def save_data(self, dic):
        global total
        self.total += 1
        self.videos.insert_one(dic)
        print(f"插入第{self.total}条成功")

    def main(self):
        callback = self.get_first_page()[0]
        self.get_page(callback)

if __name__ == '__main__':
    spider = Kr36Scraping()
    spider.main()