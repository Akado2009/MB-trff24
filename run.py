import json
import time
import requests
import re
from typing import List, Tuple

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver

import os
from bs4 import BeautifulSoup


def download_image(url: str, filename: str) -> None:
    with open(filename, 'wb') as handle:
        response = requests.get(url, stream=True)

        if not response.ok:
            print(response)

        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)

def parse_tags(caption: str) -> List[str]:
    substirng_exp = "#.+"
    expression = "(?:^|[ #]+)([^ #]+)(?=[ #]|$)"
    tags = []
    x = re.findall(substirng_exp, caption)
    for substring in x:
        k = re.findall(expression, substring)
        tags.extend(k)
    tags = list(map(lambda x: "#" + x, tags))
    return tags


def parse_post(driver, i: int, base_data: str, username: str):
    time.sleep(2)
    result_post = {
        "picture_path": "",
        "picture_local_path": "",
        "caption": "",
        "hashtags": [],
        "content": None
    }

    a = driver.find_elements(By.XPATH,  "//article/div/div/div/div/div/div/img")
    time.sleep(1000)
    for sp in a:
        folder = os.path.join(base_data, username)
        if not os.path.exists(folder):
            os.makedirs(folder)
        picture_path = os.path.join(folder, f"{str(i)}.jpg")
        result_post['picture_local_path'] = picture_path
        result_post['picture_path'] = sp.get_attribute('src')
        download_image(sp.get_attribute('src'), picture_path)
    if len(a) == 0:
        return None
    # get the description
    a = driver.find_elements(By.XPATH, "//article/div/div/div/div/div/div/ul/div/li/div/div/div/div/h1")
    post_text = a[0].text
    cleantext = BeautifulSoup(post_text, "lxml").text
    hahtags = parse_tags(cleantext)
    result_post['hashtags'] = hahtags
    result_post['caption'] = cleantext
    return result_post

def next_post_click(driver, first: bool = False) -> None:
    # next button
    a = driver.find_elements(By.XPATH, "//div/div/div/div/div/div/div/button")
    if first:
        a[0].click()
    else:
        a[1].click()

def turn_off_notifications(driver):
    notification_off = driver.find_elements('css selector', 'button')
    for button in notification_off:
        if button.text == "Not Now":
            button.click()

def get_full_name(driver) -> str:
    time.sleep(2)
    a = driver.find_elements(By.XPATH, "//header/section/div/div/span")
    return a[0].text

def get_bio(driver) -> str:
    a = driver.find_elements(By.XPATH, "//header/section/div/span/div/span")
    return a[0].text

def _parse_weird_number(number: str) -> int:
    n = number.replace(",", "")
    if "K" in n:
        n = n.replace("K", "")
        return int(float(n) * 1000)
    if "M" in n:
        n = n.replace("M", "")
        return int(float(n) * 1000000)
    return int(n)

def get_f_counts(driver) -> Tuple[int, int]:
    a = driver.find_elements(By.XPATH, "//header/section/ul/li/div/a/span/span")
    followers_count = a[0].text
    following_count = a[1].text
    return (_parse_weird_number(followers_count), _parse_weird_number(following_count))

def main():

    USERNAME = "xxnick13"
    BASE_DATA = "data"
    POSTS_TO_DOWNLOAD = 5

    cookies = None
    profile = {
        'posts': [],
    }
    with open('cookies.json', 'r') as cookies_file:
        cookies = json.load(cookies_file)
    driver = webdriver.Chrome()

    driver.get("https://www.instagram.com/")
    for cookie in cookies:
        driver.add_cookie(cookie)

    time.sleep(2)

    driver.get("https://www.instagram.com/")

    time.sleep(2)
    turn_off_notifications(driver)

    driver.get(f"https://www.instagram.com/{USERNAME}")

    profile['full_name'] = get_full_name(driver)
    profile['username'] = USERNAME
    profile['bio'] = get_bio(driver)
    profile['followers_count'], profile['followees_count'] = get_f_counts(driver)

    # return
    time.sleep(1)
    a = driver.find_elements(By.XPATH, "//header/section/ul/li/div/span/span")
    posts_count = int(a[0].text.replace(",", ""))

    # if posts_count < POSTS_TO_DOWNLOAD:
    #     POSTS_TO_DOWNLOAD = posts_count
    # posts
    a = driver.find_elements(By.XPATH, "//main/div/div/div/div/div")
    a[1].click()
    # ignore for now
    # i = 0
    # posts_counter = 0
    # while i < POSTS_TO_DOWNLOAD:
    #     post = parse_post(driver, i, BASE_DATA, USERNAME)
    #     if post is not None:
    #         i += 1
    #         profile['posts'].append(post)
    #     next_post_click(driver, posts_counter == 0)
    #     posts_counter += 1

    # //article/8div/li[2]/6div/img
    a = driver.find_elements(By.XPATH, "//article/div/div/div/div/div/div/div/div/ul/li[2]/div/div/div/div/div/div/img")
    print(a[0].get_attribute('src'))
    # click somewhere else
    # 5divsvg
    # close_button = driver.find_elements(By.XPATH, "/html/body/div[7]/div[1]/div/div[2]/div")
    # print(close_button)
    # time.sleep(1000)
    # close_button[0].click()

    # # get followees_list
    # a = driver.find_elements(By.XPATH, "//header/section/ul/li/div/a/span/span")
    # a[1].click()
    # time.sleep(5)

    # panel = driver.find_elements(By.XPATH, "//div/div/div/div/div/div/div/div/div/div/a/div/div/span")
    # usernames = []
    # for p in panel:
    #     if p.text != "":
    #         usernames.append(p.text)

    # panel = driver.find_elements(By.XPATH, "//div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/span")
    # descriptions = []
    # for p in panel:
    #     if p.text != "":
    #         descriptions.append(p.text)
    #         # print("TEXT", p.text)
    # driver.execute_script("arguments[0].scrollIntoView(true);",panel[-1])
    # time.sleep(5)
    # panel = driver.find_elements(By.XPATH, "//div/div/div/div/div/div/div/div/div/div/a/div/div/span")
    # usernames = []
    # for p in panel:
    #     print("USERNAME", p.text)

    # panel[-1].send_keys(Keys.PAGE_DOWN)
    # for p in panel:
    #     print(p.text)
    # for p in panel:
    #     print(p.get_attribute("innerHTML"))
    # print(followees, len(followees))
    time.sleep(100)

if __name__ == "__main__":
    main()