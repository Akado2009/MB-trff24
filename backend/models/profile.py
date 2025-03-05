from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from sqlalchemy import (
    func,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    TEXT,
)
import datetime
from typing import (
    List,
)
from . import Base


class SocialPost(Base):
    __tablename__ = 'social_post'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    platform: Mapped[str] = mapped_column(String(30), server_default='', nullable=False, index=True)
    username: Mapped[str] = mapped_column(default='')
    picture_path: Mapped[str] = mapped_column(default='')
    picture_local_path: Mapped[str] = mapped_column(default='')
    caption: Mapped[str] = mapped_column(default='')
    hashtags: Mapped[List[str]] = mapped_column(ARRAY(String))
    picture_url_hash: Mapped[str] = mapped_column(default='')

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())


class InstagramFollowee(Base):
    __tablename__ = 'instagram_followee'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(String(30), primary_key=True,  index=True, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(default='')

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())



class InstagramProfile(Base):
    __tablename__ = 'instagram_profile'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(String(30), primary_key=True,  index=True, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(50), default='')
    bio: Mapped[str] = mapped_column(default='')
    location: Mapped[str] = mapped_column(default='')
    followers_count: Mapped[int] = mapped_column(default=0)
    following_count: Mapped[int] = mapped_column(default=0)
    followees: Mapped[List[int]] = mapped_column(ARRAY(Integer))

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())


class FacebookProfile(Base):
    __tablename__ = 'facebook_profile'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(String(30), primary_key=True,  index=True, unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(30))
    last_name: Mapped[str] = mapped_column(String(30))
    location: Mapped[str] = mapped_column(default='')
    location_from: Mapped[str] = mapped_column(default='')
    age: Mapped[str] = mapped_column(default='')
    gender: Mapped[str] = mapped_column(String(30), default='')
    civil_status: Mapped[str] = mapped_column(String(25), default='')
    category: Mapped[str] = mapped_column(String(30), default='')
    friends_count: Mapped[str] = mapped_column(String(30), default='')
    education: Mapped[List[str]] = mapped_column(ARRAY(TEXT))
    workplaces: Mapped[List[str]] = mapped_column(ARRAY(TEXT))
    interests: Mapped[List[str]] = mapped_column(ARRAY(TEXT))
    events: Mapped[List[str]] = mapped_column(ARRAY(TEXT))
    groups: Mapped[List[str]] = mapped_column(ARRAY(TEXT))
    contact_information: Mapped[str] = mapped_column(TEXT, default='')

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())
