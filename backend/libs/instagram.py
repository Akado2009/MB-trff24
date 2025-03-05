from libs.abstract import AbstractParserInterface
from schemas.profile import (
    InstagramFollowee,
    InstagramParserResponse,
    InstagramProfile,
    SocialPost,
)
from schemas.general import (
    StatusEnum,
)
from repository.task import (
    update_task
)
from sqlalchemy.ext.asyncio import AsyncSession
import os
import json
import time
import math
import re
from typing import List, Tuple

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver

from bs4 import BeautifulSoup


class InstagramParser(AbstractParserInterface):
    def __init__(self, logger):
        self.logger = logger
        self.DATA_BASE = "data"
        self.DATA_DIR = os.path.join(self.DATA_BASE, "instagram")
        self.COOKIES_PATH = os.path.join(self.DATA_BASE, "cookies", "cookies_instagram.json")
        # TODO Uncomment
        self.POSTS_TO_DOWNLOAD = 10
        self.FOLLOWEES_TO_GET = 24 # every scroll is 12
        self.FOLLOWEES_SCROLL_VALUE = 12

    def _setup_cookies(self, driver: webdriver.Chrome) -> None:
        with open(self.COOKIES_PATH, 'r') as cookies_file:
            cookies = json.load(cookies_file)
        for cookie in cookies:
            driver.add_cookie(cookie)

    def _turn_off_notifications(self, driver: webdriver.Chrome) -> str:
        notification_off = driver.find_elements('css selector', 'button')
        for button in notification_off:
            if button.text == "Not Now":
                button.click()

    def _get_location(self, driver: webdriver.Chrome) -> str:
        a = driver.find_elements(By.XPATH, "//header/section/div/h1")
        if len(a) == 0:
            return ''
        return a[0].text

    def _get_full_name(self, driver: webdriver.Chrome) -> str:
        a = driver.find_elements(By.XPATH, "//header/section/div/div/span")
        if len(a) == 0:
            return ''
        return a[0].text

    def _get_bio(self, driver: webdriver.Chrome) -> str:
        a = driver.find_elements(By.XPATH, "//header/section/div/span/div/span")
        if len(a) == 0:
            return ''
        return a[0].text

    def _parse_weird_number(self, number: str) -> int:
        n = number.replace(",", "")
        if "K" in n:
            n = n.replace("K", "")
            return int(float(n) * 1000)
        if "M" in n:
            n = n.replace("M", "")
            return int(float(n) * 1000000)
        return int(n)

    def _get_f_counts(self, driver: webdriver.Chrome) -> Tuple[int, int]:
        a = driver.find_elements(By.XPATH, "//header/section/ul/li/div/a/span/span")
        if len(a) < 2:
            return (0, 0)
        followers_count = a[0].text
        following_count = a[1].text
        return (
            self._parse_weird_number(followers_count),
            self._parse_weird_number(following_count)
        )

    def _parse_tags(self, caption: str) -> List[str]:
        substring_expression = "#.+"
        expression = "(?:^|[ #]+)([^ #]+)(?=[ #]|$)"
        tags = []
        x = re.findall(substring_expression, caption)
        for substring in x:
            k = re.findall(expression, substring)
            tags.extend(k)
        tags = list(map(lambda x: "#" + x, tags))
        return tags

    def _parse_post(self, driver: webdriver.Chrome, username: str, order: int) -> SocialPost:
        found = False
        time.sleep(2)
        a = driver.find_elements(By.XPATH, "//article/div/div/div/div/div/div/img")
        self.logger.opt(exception=True).info(a)
        if len(a) == 0:
            a = driver.find_elements(By.XPATH, "//article/div/div/div/div/div/div/div/img")
        if len(a) == 0:
            a = driver.find_elements(By.XPATH, "//article/div/div/div/div/div/div/div/div/ul/li[2]/div/div/div/div/div/div/img")
        if len(a) == 0:
            a = driver.find_elements(By.XPATH, "//article/div/div/div/div/div/div/div/div/ul/li[2]/div/div/div/div/div/img")
        if len(a) == 0:
            a = driver.find_elements(By.XPATH, "//article/div/div/div/div/div/div/ul/div/li/div/div/div/div/h1")
        if len(a) == 0:
            a = driver.find_elements(By.XPATH, "//article/div/div/div/div/div/")
        self.logger.opt(exception=True).info(a)

        # time.sleep(100)
        if len(a) != 0:
            pic = a[0]
            folder = os.path.join(self.DATA_DIR, username)
            if not os.path.exists(folder):
                os.makedirs(folder)
            picture_path = os.path.join(folder, f"{str(order)}.jpg")
            local_path = picture_path
            remote_path = pic.get_attribute('src')
            if remote_path is not None:
                valid = self._download_picture(pic.get_attribute('src'), picture_path)
                if not valid:
                    return None

            found = True
        if not found:
            return None
        post_text = a[0].text
        cleantext = BeautifulSoup(post_text, "lxml").text
        hashtags = self._parse_tags(cleantext)

        self.logger.opt(exception=True).info(remote_path, cleantext)
        return SocialPost(
            platform="instagram",
            username=username,
            picture_path=remote_path,
            picture_local_path=local_path,
            caption=cleantext,
            hashtags=hashtags,
        )

    def _click_first_post(sefl, driver: webdriver.Chrome) -> None:
        a = driver.find_elements(By.XPATH, "//main/div/div/div/div/div")
        a[0].click()

    def _next_post_click(self, driver: webdriver.Chrome, first: bool = False) -> bool:
        time.sleep(5)
        a = driver.find_elements(By.XPATH, "//div/div/div/div/div/div/div/button")
        # time.sleep(1000)
        if not first and len(a) < 2:
            self.logger.opt(exception=True).info(a)
            return True
        if first:
            a[0].click()
        else:
            a[1].click()
        return False

    def _get_posts_count(self, driver: webdriver.Chrome) -> int:
        a = driver.find_elements(By.XPATH, "//header/section/ul/li/div/span/span")
        return int(a[0].text.replace(",", ""))

    def _get_posts(self, driver: webdriver.Chrome, username: str) -> List[SocialPost]:
        posts_counter = 0
        i = 0
        posts_amount = self._get_posts_count(driver)
        if posts_amount > self.POSTS_TO_DOWNLOAD:
            posts_amount = self.POSTS_TO_DOWNLOAD
        posts = []
        self._click_first_post(driver)
        while i < posts_amount:
            post = self._parse_post(driver, username, i)
            if post is not None:
                i += 1
                posts.append(post)
            finished = self._next_post_click(driver, posts_counter == 0)
            if finished:

                break
            posts_counter += 1
        return posts

    def _exit_posts(sefl, driver: webdriver.Chrome) -> None:
        time.sleep(4)
        close_button = driver.find_elements(By.XPATH, "/html/body/div[6]/div[1]/div/div[2]/div/div")
        close_button[0].click()

    def _get_followees(self, driver: webdriver.Chrome) -> List[InstagramFollowee]:
        times_to_scroll = math.ceil(self.FOLLOWEES_TO_GET/self.FOLLOWEES_SCROLL_VALUE)
        self._exit_posts(driver)
        a = driver.find_elements(By.XPATH, "//header/section/ul/li/div/a/span/span")
        if len(a) == 0:
            return []
        a[1].click()
        time.sleep(5)
        panel = driver.find_elements(By.XPATH, "//div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/span")
        if len(panel) == 0:
            return []
        for i in range(times_to_scroll):
            panel = driver.find_elements(By.XPATH, "//div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/span")
            driver.execute_script("arguments[0].scrollIntoView(true);",panel[-1])
            time.sleep(4)
        panel = driver.find_elements(By.XPATH, "//div/div/div/div/div/div/div/div/div/div/a/div/div/span")
        usernames = []
        for p in panel:
            if p.text != "":
                usernames.append(p.text)
        panel = driver.find_elements(By.XPATH, "//div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/span")
        descriptions = []
        for p in panel:
            if p.text != "":
                descriptions.append(p.text)

        return [InstagramFollowee(username=usernames[i], description=descriptions[i]) for i in range(min(len(usernames), len(descriptions)))]

    async def parse(
        self,
        username: str,
        task_id: int,
        db_session: AsyncSession,
    ) -> InstagramParserResponse:
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument('--headless')
        options.add_argument(r"--user-data-dir=/tmp/")
        options.add_argument(r'--profile-directory=Default')
        options.binary_location = "/usr/local/bin/chromedriver"
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.instagram.com/")

        # setup cookies
        self._setup_cookies(driver)
        time.sleep(2)

        driver.get(f"https://www.instagram.com/{username}")
        time.sleep(2)
        # turn off notifications
        self._turn_off_notifications(driver)
        _ = await update_task(
            db_session,
            task_id,
            StatusEnum.parsing_profile,
        )
        profile = InstagramProfile(username=username)
        profile.full_name = self._get_full_name(driver)
        profile.bio = self._get_bio(driver)
        profile.location = self._get_location(driver)
        profile.followers_count, profile.following_count = self._get_f_counts(driver)

        _ = await update_task(
            db_session,
            task_id,
            StatusEnum.parsing_posts,
        )
        posts = self._get_posts(driver, username)
        # self.logger.opt(exception=True).info(posts)
        followees = self._get_followees(driver)
        return InstagramParserResponse(
            profile=profile,
            posts=posts,
            followees=followees,
        )
