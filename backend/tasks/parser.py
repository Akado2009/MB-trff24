from sqlalchemy.ext.asyncio import AsyncSession

from libs.instagram import InstagramParser
from libs.facebook import FacebookParser
from schemas.general import (
    PlatformEnum,
    StatusEnum,
)
from logger import LOGURU_LOGGER
from schemas.parser import (
    PlatformGuess,
)
from repository.profile import (
    insert_instagram_followees,
    insert_instagram_profile,
    insert_posts,
    insert_facebook_profile,
)
from repository.task import (
    get_tasks_by_ids,
    update_task,
)
from typing import (
    Dict,
    List,
)
import asyncio
from logger import LOGURU_LOGGER
from prom.prometheus import PROM_HANDLERS

TASK_CHUNK_SIZE = 1


async def parse_social_network(
    user: PlatformGuess,
    db_session: AsyncSession,
    task_id: int,
) -> None:
    try:
        if user.platform == PlatformEnum.instagram:
            instagram_parser = InstagramParser(LOGURU_LOGGER)
            response = await instagram_parser.parse(
                user.user_id,
                task_id,
                db_session,
            )

            followees_ids = await insert_instagram_followees(
                db_session,
                response.followees
            )
            _ = await insert_posts(db_session, response.posts)
            profile = response.profile
            profile.followees = followees_ids
            profile = await insert_instagram_profile(db_session, profile)
            # TODO mark status properly
            _ = await update_task(
                db_session,
                task_id=task_id,
                task_status=StatusEnum.finished
            )
        elif user.platform == PlatformEnum.facebook:
            facebook_parser = FacebookParser(LOGURU_LOGGER)
            response = await facebook_parser.parse(
                user.user_id,
                task_id=task_id,
                db_session=db_session,
                is_id=user.is_id
            )
            if response is None:
                return

            _ = await insert_posts(db_session, response.posts)
            profile = await insert_facebook_profile(db_session, response.profile )
            # TODO mark status properly
            _ = await update_task(
                db_session,
                task_id=task_id,
                task_status=StatusEnum.finished
            )
        else:
            pass
    except Exception as e:
        PROM_HANDLERS['failed_parser'].inc()
        LOGURU_LOGGER.error(f"Failed to parser {user.user_id} on {user.platform}")
        _ = await update_task(
            db_session,
            task_id=task_id,
            task_status=StatusEnum.failed,
            error_message=str(e)
        )

async def multiple_parse_social_network(
    task_ids: List[int],
    db_session: AsyncSession
) -> None:
    # get all tasks that are pending
    # batch into 4-6 pieces and run parse_social_network
    # run infinitely
    all_tasks = await get_tasks_by_ids(db_session, task_ids)
    pending = list(filter(lambda x: x.status == StatusEnum.pending, all_tasks))
    while len(pending) != 0:
        for i in range(0, len(pending), TASK_CHUNK_SIZE):
            running_tasks = pending[i: i + TASK_CHUNK_SIZE]
            L = await asyncio.gather(
                *[
                    parse_social_network(
                       PlatformGuess(
                            platform=task.platform,
                            user_id=task.username,
                            is_id=task.is_id,
                        ),
                        db_session,
                        task.id,
                    )
                    for task in running_tasks
                ]
            )
            # processes = []
            # for task in running_tasks:
            #     p = Process(
            #         target=parse_social_network,
            #         args=(
            #             PlatformGuess(
            #                 platform=task.platform,
            #                 user_id=task.username,
            #                 is_id=task.is_id,
            #             ),
            #             db_session,
            #             task.id,
            #         )
            #     )
            #     processes.append(p)
            #     p.start()

            # for p in processes:
            #     p.join()
        all_tasks = await get_tasks_by_ids(db_session, task_ids)
        pending = list(filter(lambda x: x.status == StatusEnum.pending, all_tasks))

    return None