# -*- coding: utf-8 -*-
import json

from scrapy import Spider,Request
from zhihuuser.items import ZhihuuserItem

# 抓取知乎所有用户
# https://www.zhihu.com/people/excited-vczh/activities 以此用户为入口，抓取此用户所关注的或者关注他的所有用户

class ZhihuSpider(Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']
    start_user = 'excited-vczh'

    # 用户详细信息
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'allow_message%2Cis_followed%2Cis_following%2Cis_org%2Cis_blocking%2Cemployments%2Canswer_count%2Cfollower_count%2Carticles_count%2Cgender%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics'
    # 关注他的人
    followers_url = 'https://www.zhihu.com/api/v4/members/{user}/followers?include={include}&offset={offset}&limit={limit}'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'
    # 他关注的人
    followees_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={offset}'
    followees_query='data%5B*%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset=0&limit=20'

    def start_requests(self):
        yield Request(self.user_url.format(user=self.start_user,include=self.user_query),self.parse_user)
        yield Request(self.followers_url.format(user=self.start_user,include=self.followers_query,offset=0,limit=20),self.parse_followers)
        yield Request(self.followees_url.format(user=self.start_user,include=self.followees_query,offset=0,limit=20),self.parse_followees)

    # 每页（用户列表）用户信息提取
    def parse_user(self, response):
        results = json.loads(response.text)
        item = ZhihuuserItem()
        for field in item.fields:
            if field in results.keys():
                item[field] = results.get(field)
        yield item

    # 关注他的人 (循环每页抓取)
    def parse_followers(self, response):
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'),include=self.user_query),self.parse_user)

        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            next_page = next_page.replace('members','api/v4/members')
            yield Request(next_page,self.parse_followers)

    # 他关注的人 (循环每页抓取)
    def parse_followees(self,response):
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in results.get('data'):
                yield Request(self.user_url.format(user=result.get('url_token'),include=self.user_query),self.parse_user)

        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            next_page = next_page.replace('members','api/v4/members')
            yield Request(next_page,self.parse_followees)