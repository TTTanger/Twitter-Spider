# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import csv
import json
from datetime import datetime


class TwitterSpiderPipeline:
    def __init__(self):
        # 使用当前时间创建文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.file = open(f'twitter_data_{timestamp}.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.file, fieldnames=[
            'keyword', 'title', 'author', 'publish_date', 'image', 'images', 'post_url', 'comments'
        ])
        self.writer.writeheader()

    def process_item(self, item, _):
        # 将评论列表转换为JSON字符串
        item_dict = dict(item)
        # 确保图片列表是JSON格式
        if 'images' in item_dict:
            item_dict['images'] = json.dumps(item_dict['images'], ensure_ascii=False)
        # 处理评论数据
        if 'comments' in item_dict:
            item_dict['comments'] = json.dumps(item_dict['comments'], ensure_ascii=False)
        self.writer.writerow(item_dict)
        return item

    def close_spider(self, _):
        self.file.close()
