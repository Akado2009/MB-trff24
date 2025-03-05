from pydantic import BaseModel
from typing import (
    List,
    Optional,
    Union,
)
import datetime
from schemas.general import (
    PlatformEnum,
)

class InstagramFollowee(BaseModel):
    id: Optional[int] = None
    username: str
    description: str

    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class InstagramProfile(BaseModel):
    id: Optional[int] = None
    username: str
    full_name: Optional[str] = ''
    bio: Optional[str] = ''
    location: Optional[str] = ''
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    followees: Optional[List[Union[InstagramFollowee, int]]] = []

    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class FacebookProfile(BaseModel):
    id: Optional[int] = None
    username: str
    first_name: Optional[str] = ''
    last_name: Optional[str] = ''
    location: Optional[str] = ''
    location_from: Optional[str] = ''
    age: Optional[str] = ''
    gender: Optional[str] = ''
    civil_status: Optional[str] = ''
    category: Optional[str] = ''
    education: Optional[List[str]] = []
    workplaces: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    friends_count: Optional[str] = []
    groups: Optional[List[str]] = []
    events: Optional[List[str]] = []
    contact_information: str

    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class SocialPost(BaseModel):
    id: Optional[int] = None
    platform: Optional[str]
    username: str
    picture_path: Optional[str] = ''
    picture_local_path: Optional[str] = ''
    caption: Optional[str] = ''
    hashtags: Optional[List[str]] = []
    content: Optional[str] = None
    picture_url_hash: Optional[str] = None

    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class FacebookParserResponse(BaseModel):
    profile: FacebookProfile
    posts: List[SocialPost]


class InstagramParserResponse(BaseModel):
    profile: InstagramProfile
    posts: List[SocialPost]
    followees: List[InstagramFollowee]


class InstagramProfileResponse(BaseModel):
    profile: InstagramProfile
    posts: List[SocialPost]


class FacebookProfileResponse(BaseModel):
    profile: FacebookProfile
    posts: List[SocialPost]
