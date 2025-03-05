from fastapi import HTTPException
from schemas.parser import (
    PlatformGuess,
)
import requests
import io
import pandas as pd
from config import settings
from schemas.profile import (
    SocialPost,
    InstagramProfile,
    FacebookProfile,
)
from schemas.general import (
    StatusEnum,
)
from schemas.review import (
    LLMReview,
)
from schemas.task import (
    ParsingTask,
)
from schemas.general import (
    PlatformEnum,
)
from typing import (
    List,
    Union,
)
import base64
from bs4 import BeautifulSoup
from prom.prometheus import PROM_HANDLERS


def guess_platform_and_extract_user_id(link: str) -> Union[PlatformGuess, None]:
    print("GUESSING", link)
    if PlatformEnum.instagram in link:
        return PlatformGuess(
            platform=PlatformEnum.instagram,
            user_id=_extract_user_for_instagram(link)
        )
    if PlatformEnum.facebook in link:
        _is_id = 'id=' in link
        return PlatformGuess(
            platform=PlatformEnum.facebook,
            user_id=_extract_user_for_facebook(link),
            is_id=_is_id,
        )
    return None

def _extract_user_for_instagram(link: str) -> str:
    # https://www.instagram.com/if_if_if_bar/
    splitted = list(filter(lambda x: x != '', link.split("/")))
    return splitted[2]

def _extract_user_for_facebook(link: str) -> str:
    # https://www.facebook.com/elizaveta.zhayvoron/
    # https://www.facebook.com/profile.php?id=1420510116
    if 'id=' in link:
        splitted = link.split("=")
        return splitted[1]
    splitted = list(filter(lambda x: x != '', link.split("/")))
    return splitted[2]

def convert_posts(posts: List[SocialPost]) -> List[SocialPost]:
    for post in posts:
        post.content = _read_image(post.picture_local_path)
    return posts

def _read_image(path: str) -> str:
    if path == '':
        return ''
    with open(path, "rb") as image_file:
        return str(base64.b64encode(image_file.read()))

def precheck_task(task: ParsingTask, url: str, method: str) -> None:
    if task is None:
        PROM_HANDLERS['request_count'].labels(
            method, url, 404,
        ).inc()
        raise HTTPException(
            status_code=404,
            detail="Task not found, submit this profile"
        )
    if task.status == StatusEnum.skipped:
        PROM_HANDLERS['request_count'].labels(
            method, url, 412,
        ).inc()
        raise HTTPException(
            status_code=412,
            detail="Skipped and not parsed"
        )
    if task.status != StatusEnum.finished:
        PROM_HANDLERS['request_count'].labels(
            method, url, 423,
        ).inc()
        raise HTTPException(
            status_code=423,
            detail="Task not finished yet"
        )

def submit_platform_review(
    platform: PlatformEnum,
    profile: InstagramProfile,
    posts: List[SocialPost],
) -> LLMReview:
    # Dict here is: status: int, text: str
    # too lazy to move it to a separate type
    # null IDs quickhack :)
    x = 0
    for x in range(len(posts)):
        posts[x].id = x
    prompts = {
        PlatformEnum.instagram: settings.instagram_multiprompt,
        PlatformEnum.facebook: settings.facebook_multiprompt,
    }
    urls = {
        PlatformEnum.instagram: settings.instagram_score_url,
        PlatformEnum.facebook: settings.facebook_score_url,
    }
    data = {
        "multiprompt": prompts[platform],
        "profile": profile.model_dump(),
        "posts": [post.model_dump() for post in posts]
    }
    # converts all the dates
    data["profile"]["created_at"] = str(data["profile"]["created_at"])
    data["profile"]["updated_at"] = str(data["profile"]["updated_at"])

    for post in data["posts"]:
        post["created_at"] = str(post["created_at"])
        post["updated_at"] = str(post["updated_at"])

    r = requests.post(
        urls[platform],
        json=data,
        timeout=300
    )
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        llm_review = LLMReview(
            platform=platform,
            username=profile.username,
            profile_section=get_section(soup, 'profile'),
            market_section=get_section(soup, 'marketologist'),
            psycho_section=get_section(soup, 'psychologist'),
            socio_section=get_section(soup, 'sociologist'),
            client_section=get_section(soup, 'clientologist'),
            tags_section=get_section(soup, 'tags'),
            final_review_section=get_section(soup, 'final_review'),
            status_code=200,
            error='',
        )
        return llm_review
    return LLMReview(
        platform=platform,
        username=profile.username,
        status_code=r.status_code,
        error=r.text,
    )

def get_section(soup: BeautifulSoup, section_name: str) -> str:
    section = soup.findAll(section_name)
    if len(section) == 0:
        return ''
    return section[0].renderContents().decode('utf-8')

def parse_csv(file_content: bytes) -> List[PlatformGuess]:
    content = str(file_content.decode())
    # remove header
    link_lines = content.splitlines()[1:]
    guesses = []
    for link in link_lines:
        user_guess = guess_platform_and_extract_user_id(link)
        if user_guess is not None:
            guesses.append(user_guess)
    return guesses

def parse_excel(file_content: bytes) -> List[PlatformGuess]:
    df = pd.read_excel(io.BytesIO(file_content))
    links = df['links'].tolist()
    guesses = []
    for link in links:
        user_guess = guess_platform_and_extract_user_id(link)
        if user_guess is not None:
            guesses.append(user_guess)
    return guesses
