from libs.abstract import AbstractParserInterface
from schemas.profile import (
    FacebookParserResponse,
    FacebookProfile,
    SocialPost,
)
from schemas.general import (
    PlatformEnum,
    StatusEnum,
)

from repository.task import (
    update_task
)
from sqlalchemy.ext.asyncio import AsyncSession
import datetime
import os
import json
import time
import math
import re
from typing import List, Tuple, Union

from selenium.webdriver.common.by import By
from selenium import webdriver

from bs4 import BeautifulSoup
from logger import LOGURU_LOGGER
from prom.prometheus import PROM_HANDLERS


class FacebookParser(AbstractParserInterface):
    def __init__(self, logger):
        self.logger = logger
        self.DATA_BASE = "data"
        self.DATA_DIR = os.path.join(self.DATA_BASE, "facebook")
        self.COOKIES_PATH = os.path.join(self.DATA_BASE, "cookies", "cookies_facebook.json")
        self.MAX_SCROLLS = 4
        self.POSTS_TO_DOWNLOAD = 20
        self.POST_RETRIES = 4
        self.LINKS_IF_USERNAME = {
            "base": "https://www.facebook.com/{}",
            "work_and_ed": "https://www.facebook.com/{}/about_work_and_education",
            "civil": "https://www.facebook.com/{}/about_family_and_relationships",
            "gender": "https://www.facebook.com/{}/about_contact_and_basic_info",
            "age": "https://www.facebook.com/{}/about_contact_and_basic_info",
            "locations": "https://www.facebook.com/{}/about_places",
            "interests": "https://www.facebook.com/{}/sports",
            "events": "https://www.facebook.com/{}/events",
            "checkins": "https://www.facebook.com/{}/map",
        }
        self.LINKS_IF_ID = {
            "base": "https://www.facebook.com/profile.php?id={}",
            "work_and_ed": "https://www.facebook.com/profile.php?id={}&sk=about_work_and_education",
            "civil": "https://www.facebook.com/profile.php?id={}&sk=about_family_and_relationships",
            "gender": "https://www.facebook.com/profile.php?id={}&sk=about_contact_and_basic_info",
            "age": "https://www.facebook.com/profile.php?id={}&sk=about_contact_and_basic_info",
            "locations": "https://www.facebook.com/profile.php?id={}&sk=about_places",
            "interests": "https://www.facebook.com/profile.php?id={}&sk=sports",
            "events": "https://www.facebook.com/profile.php?id={}&sk=events",
            "checkins": "https://www.facebook.com/profile.php?id={}&sk=map",
        }

    def _setup_cookies(self, driver: webdriver.Chrome) -> None:
        with open(self.COOKIES_PATH, 'r') as cookies_file:
            cookies = json.load(cookies_file)
        for cookie in cookies:
            driver.add_cookie(cookie)

    def _scroll_down(self, driver: webdriver.Chrome) -> None:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

    def _parse_first_and_last_name(self, driver: webdriver.Chrome) -> Tuple[str, str]:
        a = driver.find_elements(
            By.XPATH,
            '//div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[1]/div[2]/div/div/div/div[3]/div/div/div[1]/div/div/span/h1'
        )
        if len(a) == 0:
            return '', ''
        splitted = a[0].text.split(' ')
        return splitted[0], ' '.join(splitted[1:]).strip()

    def _parse_friends_count(self, driver: webdriver.Chrome) -> str:
        a = driver.find_elements(By.XPATH, "//div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[1]/div[2]/div/div/div/div[3]/div/div/div[2]/span/a")
        for el in a:
            # 242 friends
            # ignore followers or following, but it is also possible :)
            if el.text.endswith("friends"):
                return el.text.replace(" friends", "")
        return 'Unavailable'

    def _parse_category(self, driver: webdriver.Chrome) -> str:
        a = driver.find_elements(By.XPATH, "//div/div/div/ul/div/div/div/div/div/span")
        # starts with "Profile · " - needs to be stripped
        for el in a:
            # Lives in / From
            # Married - here actual status
            if el.text.startswith('Profile ·'):
                return el.text.replace('Profile ·', '').strip()
        return ''

    def _parse_locations(self, driver: webdriver.Chrome, loc_url: str) -> str:
        driver.get(loc_url)
        time.sleep(2)
        a = driver.find_elements(By.XPATH, '//div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/span')
        cur_city = ''
        from_city = ''
        for i in range(len(a)):
            if a[i].text == 'Current city':
                cur_city = a[i - 1].text
            if a[i].text == 'Hometown':
                from_city = a[i - 1].text
        return cur_city, from_city

    def _parse_civil_status(self, driver: webdriver.Chrome, civil_url: str) -> str:
        driver.get(civil_url)
        time.sleep(2)
        a = driver.find_elements(By.XPATH, '//div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/span')
        for el in a:
            status = el.text
            if status.startswith('Married'):
                return 'Married'
            if status.startswith('Single'):
                return 'Single'
        return 'Unavailable'

    def _parse_education_and_work(self, driver: webdriver.Chrome, wae_url: str) -> Tuple[List[str], List[str]]:
        driver.get(wae_url)
        time.sleep(2)
        w_and_e = driver.find_elements(By.XPATH, "//div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/span")
        education = []
        work = []
        prefixes = {
            'work': ['Works at', 'Worked at'],
            'education': ['Studied at', 'Went to']
        }
        # Works at / Worked at / Studied at / Went to
        for el in w_and_e:
            place = el.text
            for prefix in prefixes['work']:
                if place.startswith(prefix):
                    work.append(place.replace(prefix, '').strip())
            for prefix in prefixes['education']:
                if place.startswith(prefix):
                    education.append(place.replace(prefix, '').strip())
        return education, work

    def _parse_gender(self, driver: webdriver.Chrome, gender_url: str) -> str:
        driver.get(gender_url)
        time.sleep(2)

        a = driver.find_elements(By.XPATH, '//div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/span')
        for i in range(len(a)):
            if a[i].text == 'Gender':
                return a[i - 1].text
        return ''

    def _parse_age(self, driver: webdriver.Chrome, age_url: str) -> str:
        driver.get(age_url)
        personal = driver.find_elements(By.XPATH, "//div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/span")
        # if element[i+1] == 'Gender' - previous Gender
        # == 'Birth year' - ages
        for i in range(len(personal)):
            if personal[i].text == 'Birth year':
                return str(datetime.date.today().year - int(personal[i - 1].text))
        return 'Unavailable'

    def _parse_interests(self, driver: webdriver.Chrome, int_url: str) -> List[str]:
        driver.get(int_url)
        # need to scroll, once seem to be enough
        time.sleep(2)
        self._scroll_down(driver)
        time.sleep(2)
        # interests = driver.find_elements(By.XPATH, "//div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/a/span")
        interests = driver.find_elements(
            By.XPATH,
            "//div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/a/span"
        )
        ints = []
        for i in interests:
            if i.text != '':
                ints.append(i.text)
        return ints

    def _parse_events(self, driver: webdriver.Chrome, events_url: str) -> List[str]:
        driver.get(events_url)
        # need to scroll, once seem to be enough
        time.sleep(2)
        self._scroll_down(driver)
        time.sleep(2)
        events = driver.find_elements(
            By.XPATH,
            "//div/span/span/div/a/span"
        )
        evnts = []
        for e in events:
            if e.text != '':
                evnts.append(e.text)
        return evnts

    def _parse_checkins(self, driver: webdriver.Chrome, events_url: str) -> List[str]:
        driver.get(events_url)
        # need to scroll, once seem to be enough
        time.sleep(2)
        self._scroll_down(driver)
        time.sleep(2)
        events = driver.find_elements(
            By.XPATH,
            "//div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/a/span"
        )
        evnts = []
        for e in events:
            if e.text != '':
                evnts.append(e.text)
        return evnts

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

    def _parse_posts(self, driver: webdriver.Chrome, posts_url: str, user_id: str) -> List[SocialPost]:
        posts_map = {}
        return_posts = []
        posts_count = 0
        scrolls = 0
        driver.get(posts_url)
        while scrolls < self.MAX_SCROLLS:
            scrolls += 1
            time.sleep(2)
            self._scroll_down(driver)
            time.sleep(5)
            is_featured = False
            featured = driver.find_elements(
                By.XPATH,
                '/html/body/div[1]/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[4]/div[2]/div/div[2]/div[1]/div/div/div/div/div[1]/div/div[1]/div/div/span'
            )
            if len(featured) != 0:
                for el in featured:
                    if el.text == 'Featured':
                        is_featured = True
            # /html/body/div[1]/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[4]/div[2]/div/div[2]/div[3]/div[1]/div/div/div/div/div/div/div/div/div/div/div[13]/div/div
            valid_xpath = '//div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[4]/div[2]/div/div[2]/div[2]/div/div/div/div/div/div/div/div/div/div'
            if is_featured:
                valid_xpath = '/html/body/div[1]/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[4]/div[2]/div/div[2]/div[3]/div'
            posts = driver.find_elements(
                By.XPATH,
                valid_xpath
            )
            for post in posts:
                soup = BeautifulSoup(post.get_attribute('innerHTML'), features="lxml")
                image_container = soup.find_all('a', attrs={
                    'role': "link",
                    'tabindex': 0,
                })
                # first is always an image :), also replace &amp; -> &
                _post = SocialPost(
                    platform=PlatformEnum.facebook,
                    username=user_id
                )
                broken = False
                if len(image_container) > 3:
                    for im_cont in image_container[3:]:
                        actual_images_soup = BeautifulSoup(im_cont.decode(), features="lxml")
                        images = actual_images_soup.find_all('img')
                        if len(images) != 0:
                            _post.picture_path = images[0]['src']
                            if _post.picture_path in posts_map or _post.picture_path.startswith("data:image") or 'static.xx.fbcdn.net' in _post.picture_path:
                                broken = True
                            folder = os.path.join(self.DATA_DIR, user_id)
                            if not os.path.exists(folder):
                                os.makedirs(folder)
                            picture_path = os.path.join(folder, f"{str(posts_count)}.jpg")
                            _post.picture_local_path = picture_path
                            if _post.picture_path is not None:
                                valid = self._download_picture(_post.picture_path, picture_path)
                                if not valid:
                                    broken = True
                if not broken:
                    divs = soup.findAll("div", {"dir" : "auto", "style": "text-align: start;"})
                    # that's our caption - extract hashtags from here
                    if len(divs) != 0:
                        _post.caption = divs[0].text
                        if _post.caption in posts_map:
                            continue
                        _post.hashtags = self._parse_tags(_post.caption)

                    if _post.picture_path != "" or _post.caption != "":
                        # we actually got a post
                        posts_count += 1
                        if (_post.picture_path != "" and _post.picture_path not in posts_map) or (_post.caption != "" and _post.caption not in posts_map):
                            return_posts.append(_post)
                        if _post.picture_path != "":
                            posts_map[_post.picture_path] = True
                        if _post.caption != "":
                            posts_map[_post.caption] = True

        return return_posts

    async def parse(
        self,
        user_id: str,
        task_id: int,
        db_session: AsyncSession,
        is_id: bool = False
    ) -> Union[FacebookParserResponse, None]:
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument("enable-automation")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-gpu")
        options.add_argument("--dns-prefetch-disable")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument('--remote-debugging-pipe')
        options.add_argument('--headless')
        options.add_argument("--user-data-dir=/tmp/")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--aggressive-cache-discard")
        options.add_argument("--disable-cache")
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-offline-load-stale-cache")
        options.add_argument("--disk-cache-size=0")
        options.add_argument("--no-proxy-server")
        options.add_argument('--lang=en')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)


        options.binary_location = "/usr/local/bin/chromedriver"
        # import undetected_chromedriver as uc
        # driver = uc.Chrome(
        #     # browser_executable_path="",
        #     # driver_executable_path="/usr/local/bin/chromedriver",
        #     options=options
        # )
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.facebook.com/")
        time.sleep(1)

        self._setup_cookies(driver)
        time.sleep(2)

        CURRENT_LINKS = self.LINKS_IF_USERNAME
        if is_id:
            CURRENT_LINKS = self.LINKS_IF_ID
        driver.get(CURRENT_LINKS['base'].format(user_id))
        time.sleep(2)

        profile = FacebookProfile(
            username=user_id,
            contact_information=CURRENT_LINKS['base'].format(user_id),
        )
        _ = await update_task(
            db_session,
            task_id,
            StatusEnum.parsing_posts,
        )
        posts = []
        tries = 0
        profile.friends_count = self._parse_friends_count(driver)
        profile.first_name, profile.last_name = self._parse_first_and_last_name(driver)
        while tries < self.POST_RETRIES:
            posts = self._parse_posts(
                driver,
                CURRENT_LINKS['base'].format(user_id),
                user_id
            )
            if len(posts) != 0:
                break
            tries += 1
        _ = await update_task(
            db_session,
            task_id,
            StatusEnum.parsing_profile,
        )
        if len(posts) == 0 or len(posts) == 1 or profile.friends_count == "0" or (profile.first_name == "" and profile.last_name == ""):
            PROM_HANDLERS['skipped_parser'].labels('facebook').inc()
            _ = await update_task(
                db_session,
                task_id,
                StatusEnum.skipped,
            )
            return None
        profile.category = self._parse_category(driver)

        profile.location, profile.location_from = self._parse_locations(
            driver,
            CURRENT_LINKS['locations'].format(user_id)
        )
        profile.civil_status = self._parse_civil_status(
            driver,
            CURRENT_LINKS['civil'].format(user_id),
        )
        profile.education, profile.workplaces = self._parse_education_and_work(
            driver,
            CURRENT_LINKS['work_and_ed'].format(user_id)
        )
        profile.gender = self._parse_gender(
            driver,
            CURRENT_LINKS['gender'].format(user_id)
        )
        profile.age = self._parse_age(
            driver,
            CURRENT_LINKS['age'].format(user_id)
        )
        profile.interests = self._parse_interests(
            driver,
            CURRENT_LINKS['interests'].format(user_id),
        )
        profile.events = self._parse_events(
            driver,
            CURRENT_LINKS['events'].format(user_id),
        )
        profile.events.extend(self._parse_checkins(
            driver,
            CURRENT_LINKS['checkins'].format(user_id),
        ))
        return FacebookParserResponse(
            profile=profile,
            posts=posts,
        )
