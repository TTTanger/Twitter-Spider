# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from typing import Optional, List

class Comment:
    def __init__(self, content, author, images=None):
        self.content = content
        self.author = author
        self.images = images or []

    def to_dict(self):
        return {
            "content": self.content, 
            "author": self.author,
            "images": self.images
        }

class CommentObject:
    def __init__(self):
        self.comments: List[Comment] = []
        self.commentImage: Optional[str] = None

class TwitterItem(scrapy.Item):
    keyword = scrapy.Field()
    author = scrapy.Field()
    author_id = scrapy.Field()
    title = scrapy.Field()
    publish_date = scrapy.Field()
    comments = scrapy.Field()
    image = scrapy.Field()
    images = scrapy.Field()
    post_url = scrapy.Field()
