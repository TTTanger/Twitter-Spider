import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from ..items import TwitterItem, Comment, CommentObject
import time
from urllib.parse import quote
import random
from time import sleep
from ..comment_handler import CommentHandler

class TwitterSpider(scrapy.Spider):
    name = "twitter"
    allowed_domains = ["twitter.com"]
    
    keywords = [
        "Honda Gold Wing, Gold Wing",
        "Adeveture Tourer",
        "Honda Africa Twin, Africa Twin",
        "Honda CB650R, CB650R",
        "Honda CB500X, CB500X",
        "Honda CB300F, CB300F",
        "Honda CB350RS, CB350RS",
    ]

    def __init__(self, keyword=None, *args, **kwargs):
        super(TwitterSpider, self).__init__(*args, **kwargs)
        self.keywords_to_crawl = [keyword] if keyword else self.keywords
        
        # 添加已爬取的URL集合
        self.crawled_urls = set()
        
        # 尝试从文件加载历史记录
        try:
            with open('crawled_urls.txt', 'r', encoding='utf-8') as f:
                self.crawled_urls = set(line.strip() for line in f)
        except FileNotFoundError:
            self.crawled_urls = set()
            
        # 设置Chrome选项
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # 无头模式，取消注释以隐藏浏览器
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1000,1000')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 初始化WebDriver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, 10)
        
        # 添加爬取控制参数
        self.max_tweets_per_keyword = 100  # 每个关键词最多爬取的推文数
        self.scroll_pause_time = (3, 7)    # 滚动暂停时间范围
        self.tweet_pause_time = (1, 3)     # 处理每条推文的暂停时间范围
        self.search_pause_time = (5, 10)   # 搜索关键词之间的暂停时间范围
        
        # 初始化评论处理器
        self.comment_handler = CommentHandler(self.driver, self.wait, self.logger)

    def random_sleep(self, range_tuple):
        """随机等待一段时间"""
        time.sleep(random.uniform(range_tuple[0], range_tuple[1]))

    def start_requests(self):
        # 登录Twitter
        self.login_twitter()
        
        for keyword in self.keywords_to_crawl:
            self.logger.info(f"开始爬取关键词: {keyword}")
            search_url = f'https://twitter.com/search?q={quote(keyword)}&src=typed_query&f=live'
            yield scrapy.Request(
                url=search_url,
                callback=self.parse_search_page,
                meta={'keyword': keyword},
                dont_filter=True
            )
            # 在处理下一个关键词之前随机等待
            self.random_sleep(self.search_pause_time)

    def login_twitter(self):
        try:
            self.driver.get('https://twitter.com/login')
            time.sleep(3)  # 等待页面加载
            
            # 输入用户名
            username_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            username_input.send_keys("TTTanger2003")  # 替换为你的Twitter用户名
            username_input.send_keys(Keys.ENTER)
            time.sleep(2)
            
            input("Enter to continue\n")

            # 输入密码
            password_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.send_keys("qwe/530127321")  # 替换为你的Twitter密码
            password_input.send_keys(Keys.ENTER)
            time.sleep(5)  # 等待登录完成
            
        except Exception as e:
            self.logger.error(f"登录失败: {str(e)}")

    def parse_search_page(self, response):
        keyword = response.meta['keyword']
        self.driver.get(response.url)
        self.random_sleep((4, 7))  # 等待页面加载
        
        tweets_processed = 0
        last_height = self.driver.execute_script("return document.documentElement.scrollHeight")
        
        while tweets_processed < self.max_tweets_per_keyword:
            # 等待推文加载
            try:
                tweets = self.wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, "//article[@data-testid='tweet']"))
                )
                
                # 只处理新的推文
                start_index = tweets_processed
                end_index = min(len(tweets), tweets_processed + 10)  # 每次最多处理10条
                
                for tweet in tweets[start_index:end_index]:
                    try:
                        item = self.process_tweet(tweet, keyword)
                        if item:
                            yield item
                            tweets_processed += 1
                            
                            # 随机等待一段时间再处理下一条推文
                            self.random_sleep(self.tweet_pause_time)
                            
                    except Exception as e:
                        self.logger.error(f"处理推文时发生错误: {str(e)}")
                
                # 检查是否需要继续滚动
                if tweets_processed >= self.max_tweets_per_keyword:
                    break
                
                # 滚动页面
                self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                self.random_sleep(self.scroll_pause_time)
                
                # 检查是否到达页面底部
                new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
            except Exception as e:
                self.logger.error(f"加载推文时发生错误: {str(e)}")
                break

    def process_tweet(self, tweet, keyword):
        try:
            # 首先获取推文URL
            try:
                post_url = tweet.find_element(By.XPATH, ".//a[contains(@href, '/status/')]").get_attribute("href")
                # 检查URL是否已经爬取过
                if post_url in self.crawled_urls:
                    self.logger.info(f"跳过已爬取的推文: {post_url}")
                    return None
                self.crawled_urls.add(post_url)
            except:
                post_url = ""
                
            item = TwitterItem()
            item['keyword'] = keyword
            
            # 提取文本内容
            try:
                content = tweet.find_element(By.XPATH, ".//div[@data-testid='tweetText']").text
            except:
                content = ""
            item['title'] = content
            
            # 提取作者信息
            try:
                author = tweet.find_element(By.XPATH, ".//div[@data-testid='User-Name']").text
            except:
                author = ""
            item['author'] = author
            
            # 提取时间
            try:
                time_element = tweet.find_element(By.XPATH, ".//time").get_attribute("datetime")
            except:
                time_element = ""
            item['publish_date'] = time_element
            
            # 提取所有图片URL
            try:
                images = tweet.find_elements(By.XPATH, ".//img[@alt='Image']")
                image_urls = [img.get_attribute("src") for img in images if img.get_attribute("src")]
                item['images'] = image_urls
                # 保持向后兼容，将第一张图片存储在image字段
                item['image'] = image_urls[0] if image_urls else ""
            except:
                item['images'] = []
                item['image'] = ""

            # 提取推文URL
            try:
                post_url = tweet.find_element(By.XPATH, ".//a[contains(@href, '/status/')]").get_attribute("href")
            except:
                post_url = ""
            item['post_url'] = post_url
            
            # 处理评论
            item['comments'] = self.comment_handler.get_comments(tweet)
            
            return item

        except Exception as e:
            self.logger.error(f"处理推文详情时发生错误: {str(e)}")
            return None

    def closed(self):
        # 保存已爬取的URL到文件
        try:
            with open('crawled_urls.txt', 'w', encoding='utf-8') as f:
                for url in self.crawled_urls:
                    f.write(f"{url}\n")
        except Exception as e:
            self.logger.error(f"保存爬取历史记录时出错: {str(e)}")
            
        # 关闭浏览器
        if hasattr(self, 'driver'):
            self.driver.quit()
