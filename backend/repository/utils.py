from models.profile import (
    InstagramProfile as DBInstagramProfile,
    InstagramFollowee as DBInstagramFollowee,
    FacebookProfile as DBFacebookProfile,
    SocialPost as DBSocialPost,
)
from models.review import (
    LLMReview as DBLLMReview,
)
from models.task import (
    ParsingTask as DBParsingTask,
    LLMTask as DBLLMTask,
)
from schemas.profile import (
    InstagramFollowee,
    InstagramProfile,
    FacebookProfile,
    SocialPost,
)
from schemas.task import (
    ParsingTask,
    LLMTask,
)
from schemas.review import (
    LLMReview,
)
from typing import (
    Union,
)


def convert_post_row(post: DBSocialPost) -> Union[SocialPost, None]:
    if post is None:
        return None
    return SocialPost(
        id=post.id,
        username=post.username,
        picture_path=post.picture_path,
        picture_local_path=post.picture_local_path,
        caption=post.caption,
        hashtags=post.hashtags,
        platform=post.platform,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )

def convert_followee_row(followee: DBInstagramFollowee) -> Union[InstagramFollowee, None]:
    if followee is None:
        return None
    return InstagramFollowee(
        id=followee.id,
        username=followee.username,
        description=followee.description,
        created_at=followee.created_at,
        updated_at=followee.updated_at,
    )

def convert_task_row(task: DBParsingTask) -> Union[ParsingTask, None]:
    if task is None:
        return None
    return ParsingTask(
        id=task.id,
        username=task.username,
        platform=task.platform,
        status=task.status,
        error_message=task.error_message,
        is_reviewed=task.is_reviewed,
        is_id=task.is_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )

def convert_llm_task_row(task: DBLLMTask) -> Union[LLMTask, None]:
    if task is None:
        return None
    return LLMTask(
        id=task.id,
        username=task.username,
        platform=task.platform,
        status=task.status,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )

def convert_instagram_profile_row(profile: DBInstagramProfile) -> Union[InstagramProfile, None]:
    if profile is None:
        return None
    return InstagramProfile(
        id=profile.id,
        username=profile.username,
        full_name=profile.full_name,
        bio=profile.bio,
        location=profile.location,
        followers_count=profile.followers_count,
        following_count=profile.following_count,
        followees=profile.followees,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )

def convert_facebook_profile_row(profile: DBFacebookProfile) -> Union[FacebookProfile, None]:
    if profile is None:
        return None
    return FacebookProfile(
        id=profile.id,
        username=profile.username,
        first_name=profile.first_name,
        last_name=profile.last_name,
        location=profile.location,
        location_from=profile.location_from,
        age=profile.age,
        gender=profile.gender,
        civil_status=profile.civil_status,
        category=profile.category,
        education=profile.education,
        workplaces=profile.workplaces,
        interests=profile.interests,
        friends_count=profile.friends_count,
        groups=profile.groups,
        contact_information=profile.contact_information,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )

def convert_review_raw(review: DBLLMReview) -> Union[LLMReview, None]:
    if review is None:
        return None
    return LLMReview(
        id=review.id,
        platform=review.platform,
        username=review.username,
        profile_section=review.profile_section,
        market_section=review.market_section,
        psycho_section=review.psycho_section,
        socio_section=review.socio_section,
        client_section=review.client_section,
        tags_section=review.tags_section,
        final_review_section=review.final_review_section,
        status_code=review.status_code,
        error=review.error,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )
