# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pandas as pd


class DoubanZhihuPipeline:
    def __init__(self):
        self.comments_data = []  # Used to store all data
        self.reviews_data = []
        self.zhihu_data = []
    def process_item(self, item, spider):
        # Add each piece of data to the list
        if 'comment' in item:
            self.comments_data.append(dict(item))
        elif 'content' in item:
            self.zhihu_data.append(dict(item))
        else:
            self.reviews_data.append(dict(item))
        return item
    def close_spider(self, spider):
        # 将数据保存为 Excel 文件
        if self.comments_data:
            comments_df = pd.DataFrame(self.comments_data)
            print('Comments are being stored')
            comments_df.to_excel('douban_comments.xlsx', index=False, engine='openpyxl')

        if self.reviews_data:
            reviews_df = pd.DataFrame(self.reviews_data)
            print('Reviews are being stored')
            reviews_df.to_excel('douban_reviews.xlsx', index=False, engine='openpyxl')
        
        if self.zhihu_data:
            zhihu_df = pd.DataFrame(self.zhihu_data)
            print('Zhihu are being stored')
            zhihu_df.to_excel('zhihu_data.xlsx', index=False, engine='openpyxl')