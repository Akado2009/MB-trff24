from models.profile import (
    SocialPost as DBSocialPost,
    InstagramFollowee as DBInstagramFollowee,
    InstagramProfile as DBInstagramProfile,
    FacebookProfile as DBFacebookProfile,
)
import re
from schemas.profile import (
    SocialPost,
    InstagramProfile,
    InstagramFollowee,
    InstagramParserResponse,
    FacebookProfile,
    FacebookParserResponse,
)
from sqlalchemy.dialects.postgresql import (
    insert,
)

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import (
    List,
    Union,
)
from repository.utils import (
    convert_post_row,
    convert_followee_row,
    convert_instagram_profile_row,
    convert_facebook_profile_row,
)

import hashlib
from logger import LOGURU_LOGGER
from prom.prometheus import PROM_HANDLERS


async def insert_posts(
    db_session: AsyncSession,
    posts: List[SocialPost],
) -> Union[List[int], None]:
    try:
        if len(posts) == 0:
            return []
        hash_mapping = {}
        pic_regexp = re.compile(r'[0-9]+_[0-9]+_[0-9]+_n.')
        ext_pic_regexp = re.compile(r'url=.+?&')
        new_posts = []
        for post in posts:
            actual_path = re.search(pic_regexp, post.picture_path)
            if actual_path is None:
                actual_path = re.search(ext_pic_regexp, post.picture_path)
            if actual_path is not None:
                actual_hash = hashlib.md5(actual_path.group(0).encode('utf-8')).hexdigest()
                if hash_mapping.get(actual_hash, None) is None:
                    post.picture_url_hash = actual_hash
                    new_posts.append(post)
                    hash_mapping[actual_hash] = True
            else:
                post.picture_url_hash = ''
                new_posts.append(post)
        values = list(map(lambda x: x.model_dump(exclude_none=True), new_posts))
        statement = insert(DBSocialPost).values(values)
        upsert_stmt = statement.on_conflict_do_update(
            constraint="social_post_pkey",
            set_=dict(
                picture_path=statement.excluded.picture_path,
                caption=statement.excluded.caption,
                hashtags=statement.excluded.hashtags,
            )
        ).returning(
            DBSocialPost.id
        )
        result = await db_session.execute(statement=upsert_stmt)
        await db_session.commit()
        return [row[0] for row in result]
    except Exception as e:
        await db_session.rollback()
        LOGURU_LOGGER.error(f"Error inserting posts: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('insert_posts').inc()
        return None

async def get_post(
    db_session: AsyncSession,
    id: int,
) -> Union[SocialPost, None]:
    try:
        statement = select(DBSocialPost).where(DBSocialPost.id == id)
        result = await db_session.execute(statement=statement)
        result = result.first()[0]
        return convert_post_row(result)
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting a post: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_post').inc()
        return None

async def get_posts_by_username(
    db_session: AsyncSession,
    username: str,
    platform: str,
) -> Union[List[SocialPost], None]:
    try:
        statement = select(DBSocialPost).where(
            DBSocialPost.username == username,
            DBSocialPost.platform == platform,
        )
        result = await db_session.execute(statement=statement)
        result = result.all()
        return list(map(lambda x: convert_post_row(x[0]), result))
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting posts: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_posts_by_username').inc()
        return None

async def get_posts(
    db_session: AsyncSession,
    ids: List[int]
) -> Union[List[SocialPost], None]:
    try:
        statement = select(DBSocialPost).where(DBSocialPost.id.in_(tuple(ids)))
        result = await db_session.execute(statement=statement)
        result = result.all()
        return list(map(lambda x: convert_post_row(x[0]), result))
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting posts: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_posts').inc()
        return None


# INSTAGRAM
async def insert_instagram_profile(
    db_session: AsyncSession,
    profile: InstagramProfile
) -> Union[int, None]:
    # pkey instagram_profile_pkey
    try:
        statement = insert(DBInstagramProfile).values([
            profile.model_dump(exclude_none=True)
        ])
        upsert_stmt = statement.on_conflict_do_update(
            constraint="instagram_profile_pkey",
            set_=dict(
                full_name=statement.excluded.full_name,
                bio=statement.excluded.bio,
                location=statement.excluded.location,
                followers_count=statement.excluded.followers_count,
                following_count=statement.excluded.following_count,
                followees=statement.excluded.followees,
            )
        ).returning(
            DBInstagramProfile.id
        )
        result = await db_session.execute(statement=upsert_stmt)
        await db_session.commit()
        # unsafe code :)
        return result.first()[0]
    except Exception as e:
        await db_session.rollback()
        LOGURU_LOGGER.error(f"Error inserting a profile {profile.username}: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('insert_instagram_profile').inc()
        return None

async def insert_instagram_followees(
    db_session: AsyncSession,
    followees: List[InstagramFollowee]
) -> Union[List[int], None]:
    # pkey instagram_followee_pkey
    try:
        values = list(map(lambda x: x.model_dump(exclude_none=True), followees))
        statement = insert(DBInstagramFollowee).values(values).returning(
            DBInstagramFollowee.id
        )
        statement = insert(DBInstagramFollowee).values(values)
        upsert_stmt = statement.on_conflict_do_update(
            constraint="instagram_followee_pkey",
            set_=dict(
                description=statement.excluded.description,
            )
        ).returning(
            DBInstagramFollowee.id
        )
        result = await db_session.execute(statement=upsert_stmt)
        await db_session.commit()
        return [row[0] for row in result]
    except Exception as e:
        await db_session.rollback()
        usernames = list(map(lambda x: x.username, followees))
        LOGURU_LOGGER.error(f"Error inserting followees {','.join(usernames)}: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('insert_instagram_followees').inc()
        return None

async def get_instagram_followee(
    db_session: AsyncSession,
    f_id: int = None,
    username: str = None,
) -> Union[InstagramFollowee, None]:
    try:
        statement = None
        if f_id is None and username is None:
            LOGURU_LOGGER.warning(f"Provide a username or an id for a followee")
            return None
        if f_id is not None:
            statement = select(DBInstagramFollowee).where(DBInstagramFollowee.id == f_id)
        else:
            statement = select(DBInstagramFollowee).where(DBInstagramFollowee.username == username)
        result = await db_session.execute(statement=statement)
        result = result.first()[0]
        return convert_followee_row(result)
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting a followee: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_instagram_followee').inc()
        return None

async def get_instagram_followees(
    db_session: AsyncSession,
    ids: List[int],
) -> Union[List[InstagramFollowee], None]:
    try:
        statement = select(DBInstagramFollowee).where(DBInstagramFollowee.id.in_(tuple(ids)))
        result = await db_session.execute(statement=statement)
        result = result.all()
        return list(map(lambda x: convert_followee_row(x[0]), result))
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting followees: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_instagram_followees').inc()
        return None

async def get_instagram_profile(
    db_session: AsyncSession,
    p_id: int = None,
    username: str = None,
) -> Union[InstagramProfile, None]:
    try:
        statement = None
        if p_id is None and username is None:
            LOGURU_LOGGER.warning(f"Provide a username or an id for a profile")
            return None
        if p_id is not None:
            statement = select(DBInstagramProfile).where(DBInstagramProfile.id == p_id)
        else:
            statement = select(DBInstagramProfile).where(DBInstagramProfile.username == username)
        result = await db_session.execute(statement=statement)
        result = result.first()[0]
        return convert_instagram_profile_row(result)
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting a profile: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_instagram_profile').inc()
        return None

async def get_instagram_profile_with_followees(
    db_session: AsyncSession,
    username: str = None,
) -> Union[InstagramProfile, None]:
    profile = await get_instagram_profile(db_session, username=username)
    if profile is None:
        return None
    followees = await get_instagram_followees(
        db_session,
        profile.followees,
    )
    profile.followees = followees
    return profile

# FACEBOOK
async def insert_facebook_profile(
    db_session: AsyncSession,
    profile: FacebookProfile
) -> Union[int, None]:
    # pkey facebook_profile_pkey
    try:
        statement = insert(DBFacebookProfile).values([
            profile.model_dump(exclude_none=True)
        ])
        upsert_stmt = statement.on_conflict_do_update(
            constraint="facebook_profile_pkey",
            set_=profile.model_dump(exclude_none=True)
        ).returning(
            DBFacebookProfile.id
        )
        result = await db_session.execute(statement=upsert_stmt)
        await db_session.commit()
        # unsafe code :)
        return result.first()[0]
    except Exception as e:
        await db_session.rollback()
        LOGURU_LOGGER.error(f"Error inserting a profile {profile.username}: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('insert_facebook_profile').inc()
        return None

async def get_facebook_profile(
    db_session: AsyncSession,
    p_id: int = None,
    username: str = None,
) -> Union[FacebookProfile, None]:
    try:
        statement = None
        if p_id is None and username is None:
            LOGURU_LOGGER.warning(f"Provide a username or an id for a profile")
            return None
        if p_id is not None:
            statement = select(DBFacebookProfile).where(
                DBFacebookProfile.id == p_id
            )
        else:
            statement = select(DBFacebookProfile).where(
                DBFacebookProfile.username == username
            )
        result = await db_session.execute(statement=statement)
        result = result.first()[0]
        return convert_facebook_profile_row(result)
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting a profile: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_facebook_profile').inc()
        return None
