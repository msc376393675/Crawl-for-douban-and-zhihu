# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DoubanZhihuItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    # Short comment fields
    comment = scrapy.Field()
    rating = scrapy.Field()
    username = scrapy.Field()
    useful_count = scrapy.Field()
    comment_time = scrapy.Field()

    # Review fields
    review = scrapy.Field()
    useless_count = scrapy.Field()
    review_time = scrapy.Field()
    reply_count = scrapy.Field()

    # Zhihu fields
    content = scrapy.Field()
    author_name = scrapy.Field()
    created_time = scrapy.Field()
    voteup_count = scrapy.Field()