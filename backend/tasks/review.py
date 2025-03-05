from sqlalchemy.ext.asyncio import AsyncSession
from schemas.general import (
    PlatformEnum,
    StatusEnum,
)
from schemas.parser import (
    PlatformGuess,
)
from repository.task import (
    update_task,
    update_llm_task,
    update_task_is_reviewed,
    get_llm_tasks_by_ids,
    get_tasks_by_guesses
)
from repository.profile import (
    get_instagram_profile_with_followees,
    get_posts_by_username,
    get_facebook_profile
)
from api.routers.utils import (
    convert_posts,
    precheck_task,
    submit_platform_review,
)
from repository.review import (
    insert_review,
)
from typing import (
    List,
)
import asyncio
from logger import LOGURU_LOGGER
from prom.prometheus import PROM_HANDLERS


TASK_CHUNK_SIZE = 1


async def submit_llm_review(
    db_session: AsyncSession,
    user: PlatformGuess,
    llm_task_id: int,
    task_id: int,
) -> None:
    try:
        profile = None
        if user.platform == PlatformEnum.instagram:
            profile = await get_instagram_profile_with_followees(
                db_session,
                username=user.user_id
            )
        else:
            profile = await get_facebook_profile(
                db_session,
                username=user.user_id,
            )
        if profile is None:
            _ = await update_llm_task(
                db_session,
                task_id=llm_task_id,
                task_status=StatusEnum.failed,
                error_message="No such profile"
            )
            return
        # get profile
        posts = await get_posts_by_username(
            db_session,
            profile.username,
            platform=user.platform,
        )
        posts = convert_posts(posts)
        review = submit_platform_review(
            user.platform,
            profile,
            posts
        )
        _ = await insert_review(db_session, review)
        _ = await update_task_is_reviewed(db_session, task_id, True)

        _ = await update_llm_task(
            db_session,
            task_id=llm_task_id,
            task_status=StatusEnum.finished
        )
    except Exception as e:
        _ = await update_llm_task(
            db_session,
            task_id=llm_task_id,
            task_status=StatusEnum.failed,
            error_message=str(e)
        )

async def multiple_submit_llm_review(
    llm_task_ids: List[int],
    db_session: AsyncSession
) -> None:
    llm_tasks = await get_llm_tasks_by_ids(db_session, llm_task_ids)
    guesses = [
        PlatformGuess(
            user_id=task.username,
            platform=task.platform
        )
        for task in llm_tasks
    ]
    corresponding_tasks = await get_tasks_by_guesses(db_session, guesses)
    filtered_tasks = list(filter(
        lambda x: x.status == StatusEnum.finished,
        corresponding_tasks
    ))
    corr_mapping = {
        (t.username, t.platform): t.id
        for t in filtered_tasks
    }
    pending = list(filter(lambda x: x.status == StatusEnum.pending, llm_tasks))
    llm_mapping = {
        (t.username, t.platform): t.id
        for t in llm_tasks
    }
    pending = list(filter(lambda x: x.status == StatusEnum.pending, llm_tasks))
    for i in range(0, len(pending), TASK_CHUNK_SIZE):
        running_tasks = pending[i: i + TASK_CHUNK_SIZE]
        L = await asyncio.gather(
            *[
                submit_llm_review(
                    db_session,
                    PlatformGuess(
                        platform=task.platform,
                        user_id=task.username,
                    ),
                    llm_mapping.get((task.username, task.platform), None),
                    task.id,
                )
                for task in running_tasks
            ]
        )
    return None

