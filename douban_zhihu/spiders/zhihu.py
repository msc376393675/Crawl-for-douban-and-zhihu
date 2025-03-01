import scrapy
from douban_zhihu.items import DoubanZhihuItem
import json
import warnings
from urllib.parse import urlparse, parse_qs
from scrapy.exceptions import ScrapyDeprecationWarning
import re
warnings.filterwarnings('ignore', category=ScrapyDeprecationWarning)

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    question_id = '8045672950'

    start_url = f'https://www.zhihu.com/api/v4/questions/{question_id}/feeds'
    cookies = {
        '__snaker__id': 'Z81xOtVtRltcOhyv',
        'q_c1': '183068e8a92b4a1cbade0491da7cf42d|1710420208000|1710420208000',
        '_xsrf': 'TlAFfLbiBR0J5z1o8K6TrhnzgVVlsDAq',
        'z_c0': '2|1:0|10:1740758110|4:z_c0|80:MS4xdmlSZ0JBQUFBQUFtQUFBQVlBSlZUVjRxcjJnRnJmRHM0b3dvTUpsN2R1MEFta05sR0E3RnpBPT0=|72161fb9cb69e7ae76a2a7a1cde3b2989d5ee1d58e0cc88466909b786015efc2',
        '__zse_ck': '004_/srlnvL=XY4XGVvdH7vNcF3yEfSSdvHv2RwWXZIEUbSjwC9=ywq6KK1MQBICaB54kM3z8AHE4rE62xRsbq=mksrzDWhBD3tGayadgWv084A5R3ffqlUiBPO4=3YqXc2/-xjvHYRCO20qYeiJurkKsUiqyy1B2+MPLdpv/6vtiqb0JwrkRifUo212vIquIFFEdPJL5q0MwKETPpL9M2JpqjM+4PiI0n1bbkI7oN01d8xE27wA3h15zmed06Kw1G4cH',
        'tst': 'r',
        'SESSIONID': 'Ok4NzFAScyDFcjmcKQhpQAY2na7RuBTjoTVsCEMPlfZ',
        'JOID': 'V1wRBErZinfSXG5PWtufpK24yQ1Ol-FAmiIpDgq-8jOXOQAjOb8WsLdZb0xfnI3iZIm-XgzsLBeixYUcPguEO8A=',
        'osd': 'UV4SB0LfiHTRVGhNWdiXoq-7ygVIleJDkiQrDQm29DGUOgglO7wVuLFbbE9Xmo_hZ4G4XA_vJBGgxoYUOAmHOMg=',
        '_zap': '65d4a816-6f5c-4dd1-a313-5cad375f1dd7',
        'd_c0': '9POTDvhEFBqPTvwxzszGhWRXNULKqVa0cRs=|1740816855',
        'BEC': '46faae78ffea44ab7c29d705bdab5c18'
    }
    headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Referer': f'https://www.zhihu.com/question/{question_id}',
                'x-zse-93': '101_3_3.0',  
                'x-zse-96': '2.0_vVl1C+HP2257CK2j5QCp0t00TNZ5jqoNrQIQrgkXqJvSRoOOe4WpT=qPowrVhn+u', 
                 'Host': 'www.zhihu.com',
                
            }
    # https://www.zhihu.com/question/8045672950/answer/98576789837
    def start_requests(self):
        # 初始请求参数
        params = {
            'include': 'data[*].is_normal,admin_closed_comment,reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,is_sticky,collapsed_by,suggest_edit,comment_count,can_comment,content,editable_content,attachment,voteup_count,reshipment_settings,comment_permission,created_time,updated_time,review_info,relevant_info,question,excerpt,is_labeled,paid_info,paid_info_content,reaction_instruction,relationship.is_authorized,is_author,voting,is_thanked,is_nothelp;data[*].author.follower_count,vip_info,kvip_info,badge[*].topics;data[*].settings.table_of_content.enabled',
            'limit': 5,  # 每次请求返回的评论数量
            'offset': 0,  # 初始偏移量
            'order': 'default',  # 排序方式
            'platform': 'desktop',  # 平台
            'session_id': '',  # 会话 ID
            'cursor': '',  # 初始 cursor 为空
        }

        # 发送初始请求
        yield scrapy.Request(
            url=self.start_url,
            method='GET',
            headers=self.headers,
            cookies=self.cookies,
            callback=self.parse_comments,
            meta={'params': params, 'count': 0}  # 添加计数器
        )


    def parse_comments(self, response):
        # 解析返回的 JSON 数据
        data = json.loads(response.text)
        print(f'Fetched {len(data["data"])} comments')

        # 提取评论数据
        for comment in data['data']:
            target = comment.get('target', {})
            if not target:
                print("Target is empty, skipping...")
                continue

            # 抓取完整评论内容
            answer_id = target.get('id')
            if answer_id:
                # 使用正确的 API URL
                full_content_url = f'https://www.zhihu.com/question/{self.question_id}/answer/{answer_id}'
                print(f"Full content URL: {full_content_url}")
                yield scrapy.Request(
                    url=full_content_url,
                    method='GET',
                    headers=self.headers,
                    cookies=self.cookies,
                    callback=self.parse_full_content,
                    meta = {'count': response.meta['count']}
                )
            else:
                print("No answer_id found in target")

        # 获取下一个 cursor
        paging = data.get('paging', {})
        next_url = paging.get('next')  # 获取下一页的 URL
        if next_url and response.meta['count'] < 250:  # 限制抓取 250 条数据
            # 从 URL 中提取 cursor
            parsed_url = urlparse(next_url)
            query_params = parse_qs(parsed_url.query)
            next_cursor = query_params.get('cursor', [''])[0]  # 提取 cursor 参数

            # 更新请求参数
            params = response.meta['params']
            params['cursor'] = next_cursor
            params['offset'] += params['limit']

            # 更新计数器
            count = response.meta['count'] + len(data['data'])

            # 发送下一个请求
            yield scrapy.Request(
                url=next_url,  # 直接使用 next_url
                method='GET',
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse_comments,
                meta={'params': params, 'count': count}
            )
    def parse_full_content(self, response):
        if response.status != 200:
            print(f'Failed to fetch full content: {response.status}, URL: {response.url}')
            return
        data = response.xpath('//div[@class="ContentItem AnswerItem"]')
        item = DoubanZhihuItem()
        content = data.xpath('.//span[@class="RichText ztext CopyrightRichText-richText css-ob6uua"]/p/text()').getall()
        content = '\n'.join(content)
        if content == '':
            print("No content found")
            item['content'] = f'{response.url}'
        else:   
            item['content'] = content
        item['author_name'] = data.xpath('.//div[@class="AuthorInfo"]/meta[1]/@content').get()
        created_time = data.xpath('.//div[@class="ContentItem-time"]/a/span/text()').get().replace('发布于', '')
        created_time = created_time.replace('编辑于', '').strip()   
        item['created_time'] = created_time
        bottom_data= data.xpath('.//div[@class="RichContent RichContent--unescapable"]/div[2]').get()
        if not bottom_data:
            print("No bottom_data found")
            item['voteup_count'] = f'{response.url}'
            item['reply_count'] = '0'
        else:
            vote_count = re.findall(r'赞同 (\d+)', bottom_data)
            if not vote_count:
                vote_count = ['0']
            item['voteup_count'] = vote_count[0]

            reply_count = re.findall(r'(\d+) 条评论', bottom_data)
            if not reply_count:
                reply_count = ['0']
            item['reply_count'] = reply_count[0]

        yield item
        count = response.meta['count']
        # 打印抓取进度
        print(f'Fetched {count+1} comments')