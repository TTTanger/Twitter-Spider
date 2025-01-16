from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from .items import Comment, CommentObject
import time
import random

class CommentHandler:
    def __init__(self, driver, wait, logger):
        self.driver = driver
        self.wait = wait
        self.logger = logger

    def random_sleep(self, range_tuple):
        """随机等待一段时间"""
        time.sleep(random.uniform(range_tuple[0], range_tuple[1]))

    def process_single_comment(self, comment_element):
        """处理单个评论"""
        try:
            # 获取评论文本和作者
            comment_text = ""
            text_selectors = [
                ".//div[@data-testid='tweetText']",
                ".//div[@lang]",
                ".//div[contains(@class, 'css-901oao')]"
            ]
            for selector in text_selectors:
                try:
                    comment_text = comment_element.find_element(By.XPATH, selector).text
                    if comment_text:
                        break
                except:
                    continue

            comment_author = ""
            author_selectors = [
                ".//div[@data-testid='User-Name']",
                ".//span[contains(@class, 'username')]",
                ".//div[contains(@class, 'css-1dbjc4n')]//span"
            ]
            for selector in author_selectors:
                try:
                    comment_author = comment_element.find_element(By.XPATH, selector).text
                    if comment_author:
                        break
                except:
                    continue

            # 获取评论中的图片
            comment_images = []
            try:
                images = comment_element.find_elements(By.XPATH, ".//img[@alt='Image']")
                comment_images = [img.get_attribute("src") for img in images if img.get_attribute("src")]
            except:
                pass

            if comment_text and comment_author:
                return Comment(content=comment_text, author=comment_author, images=comment_images)
            return None

        except Exception as e:
            self.logger.error(f"处理单条评论时出错: {str(e)}")
            return None

    def get_comments(self, tweet):
        """获取推文的评论"""
        comment_object = CommentObject()
        try:
            # 首先检查是否有评论按钮
            try:
                reply_button = tweet.find_element(By.XPATH, ".//div[@data-testid='reply']")
                # 确保按钮可点击并在视图中
                self.driver.execute_script("arguments[0].scrollIntoView(true);", reply_button)
                self.random_sleep((1, 2))
                
                # 使用 JavaScript 点击评论按钮
                self.driver.execute_script("arguments[0].click();", reply_button)
                self.random_sleep((2, 4))
            except Exception as e:
                self.logger.error(f"点击评论按钮失败: {str(e)}")
                return {'comments': [], 'commentImage': None}
            
            # 等待评论加载
            comment_elements = None
            selectors = [
                "//article[@data-testid='tweet']",
                "//div[@data-testid='cellInnerDiv']//article",
                "//div[contains(@class, 'css-1dbjc4n')]//article"
            ]
            
            for selector in selectors:
                try:
                    comment_elements = self.wait.until(
                        EC.presence_of_all_elements_located(
                            (By.XPATH, selector)
                        )
                    )
                    if comment_elements and len(comment_elements) > 1:
                        break
                except:
                    continue
            
            if comment_elements and len(comment_elements) > 1:
                # 获取评论图片
                try:
                    image_element = comment_elements[0].find_element(By.XPATH, ".//img[@alt='Image']")
                    comment_object.commentImage = image_element.get_attribute("src")
                except:
                    comment_object.commentImage = None

                # 获取前5条评论
                for comment_element in comment_elements[1:6]:
                    comment = self.process_single_comment(comment_element)
                    if comment:
                        comment_object.comments.append(comment)
                    self.random_sleep((0.5, 1))
            else:
                return {'comments': [], 'commentImage': None}

        except Exception as e:
            self.logger.error(f"处理评论时出错: {str(e)}")
            return {'comments': [], 'commentImage': None}
        finally:
            try:
                self._close_comment_dialog()
            except Exception as e:
                self.logger.error(f"关闭评论对话框时出错: {str(e)}")

        return {
            'comments': [comment.to_dict() for comment in comment_object.comments],
            'commentImage': comment_object.commentImage
        }

    def _close_comment_dialog(self):
        """关闭评论对话框"""
        try:
            close_selectors = [
                "//div[@data-testid='app-bar-close']",
                "//div[@aria-label='Close']",
                "//div[contains(@class, 'css-18t94o4 css-1dbjc4n')]//div[@role='button']"
            ]
            
            for close_selector in close_selectors:
                try:
                    close_button = self.driver.find_element(By.XPATH, close_selector)
                    self.driver.execute_script("arguments[0].click();", close_button)
                    self.random_sleep((1, 2))
                    break
                except:
                    continue
        except Exception as e:
            self.logger.error(f"关闭评论对话框时出错: {str(e)}") 