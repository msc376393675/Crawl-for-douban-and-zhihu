import scrapy
from douban_zhihu.items import DoubanZhihuItem  # imort Item
import re
import html

class DoubanSpider(scrapy.Spider):
    name = 'douban'
    allowed_domains = ['movie.douban.com']
    start_urls = 'https://movie.douban.com/subject/34780991/'

    def start_requests(self):
        # Define Cookie
        cookies = {
            'bid': 'lbQVXue40Us',
            'll': '"118297"',
            'push_noty_num': '0',
            'push_doumail_num': '0',
            'ap_v': '0,6.0',
            'dbcl2': '"202398912:kKz5WDG2Vfo"',
        }
        # Define the URL prefixes for positive and negative comments
        high_rating_url = f'{self.start_urls}comments?percent_type=h'
        low_rating_url = f'{self.start_urls}comments?percent_type=l'

        # Define the URL Define the URL prefix for reviews
        review_url = f'{self.start_urls}reviews?'

        # Grab short comments
        for page in range(0, 20):  # Grab the first 20 pages
            # URL for positive comments
            print(f'Start grabbing comments page {page + 1}')
            yield scrapy.Request(
                url=f'{high_rating_url}&start={page * 20}&limit=20&status=P&sort=new_score',  # 20 comments per page
                callback=self.parse_comments,
                cookies=cookies,
            )
            # URL for negative comments
            yield scrapy.Request(
                url=f'{low_rating_url}&start={page * 20}&limit=20&status=P&sort=new_score',
                callback=self.parse_comments,
                cookies=cookies,
            )

        # Grab reviews
        for page in range(0, 15):  # Grab the first 15 pages
            # URL for positive reviews
            print(f'Start grabbing reviews page {page + 1}')
            yield scrapy.Request(
                url=f'{review_url}&sort=hotest&rating=5&start={page * 20}',
                callback=self.parse_reviews,
                cookies=cookies,
            )
            # URL for negative reviews
            yield scrapy.Request(
                url=f'{review_url}&sort=hotest&rating=1&start={page * 20}',
                callback=self.parse_reviews,
                cookies=cookies,
            )

    def parse_reviews(self, response):
        if response.status != 200:
            print(f'Failed to fetch reviews: {response.status}, URL: {response.url}')
            return
        
        reviews = response.xpath('//div[@class="main review-item"]')
        print(f'Found {len(reviews)} reviews')

        for review in reviews:
            review_id = review.xpath('.//@id').get().split('-')[-1]  # get the ID for each review
            full_content_url = f'https://movie.douban.com/j/review/{review_id}/full'
            yield scrapy.Request(
                url = full_content_url,
                cookies = response.request.cookies,
                callback = self.parse_full_reviews,
                meta={'review': review}
            )

    def parse_comments(self, response):
        if response.status != 200:
            print(f'Failed to fetch comments: {response.status}, URL: {response.url}')
            return
        comments = response.xpath('//div[@class="comment"]')
        print(f'Found {len(comments)} comments')

        # Score mapping dictionary
        rating_mapping = {
            '力荐': '5',
            '推荐': '4',
            '还行': '3',
            '较差': '2',
            '很差': '1',
        }

        for comment in comments:
            item = DoubanZhihuItem()
            item['comment'] = comment.xpath('.//p[@class=" comment-content"]/span/text()').get().strip()
            ratings = comment.xpath('.//h3/span[@class="comment-info"]/span[2]/@title').get()
            item['rating'] = rating_mapping.get(ratings)
            item['username'] = comment.xpath('.//h3/span[@class="comment-info"]/a/text()').get()
            item['useful_count'] = comment.xpath('.//h3/span[@class="comment-vote"]/span/text()').get()
            item['comment_time'] = comment.xpath('.//h3/span[@class="comment-info"]/span[@class="comment-time "]/text()').get().strip()
            yield item
        
    def parse_full_reviews(self, response):
        if response.status != 200:
            print(f'Failed to fetch full content: {response.status}, URL: {response.url}')
            return
        review = response.meta['review']
        full_content = response.json().get('html', '')
        pattern = re.compile(r'<p[^>]*>(.*?)</p>', re.DOTALL)
        full_review = pattern.findall(full_content)
        full_review = '\n'.join(full_review)
        full_review = html.unescape(full_review)
        full_review = re.sub(r'<span[^>]*>.*?</span>', '', full_review)
        # Score mapping dictionary
        rating_mapping = {
            '力荐': '5',
            '推荐': '4',
            '还行': '3',
            '较差': '2',
            '很差': '1',
        }
        item = DoubanZhihuItem()
        item['review'] = full_review
        item['username'] = review.xpath('.//header/a[2]/text()').get()
        rating = review.xpath('.//header/span[1]/@title').get()
        item['rating'] = rating_mapping.get(rating)
        item['useful_count'] = review.xpath('.//div[@class="action"]/a[1]/span/text()').get().strip()
        useless_count = review.xpath('.//div[@class="action"]/a[2]/span/text()').get().strip()
        item['useless_count'] = useless_count if useless_count else '0'
        reply_count = review.xpath('.//div[@class="action"]/a[3]/text()').get()
        item['reply_count'] = re.match(r'\d+', reply_count).group()
        item['review_time'] = review.xpath('.//header/span[2]/text()').get().strip()
        print('The number of review +1')
        yield item