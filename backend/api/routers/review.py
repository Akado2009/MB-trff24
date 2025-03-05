from api.dependencies.core import DBSessionDep
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)
from schemas.general import (
    PlatformEnum,
    GeneralResponse,
    StatusEnum,
    GeneralResponseMultiple,
)
from schemas.parser import (
    PlatformGuess,
)
from schemas.task import (
    LLMTask,
)
from schemas.review import (
    LLMReview,
    MultipleReviewRequest,
)
from api.routers.utils import (
    guess_platform_and_extract_user_id,
    precheck_task,
)
from repository.task import (
    get_task,
    upsert_llm_tasks,
    get_llm_task,
    get_all_llm_tasks,
)
from repository.review import (
    get_review,
)
import asyncio
from tasks.review import (
    submit_llm_review,
    multiple_submit_llm_review,
)
from typing import (
    List,
    Optional
)
from prom.prometheus import (
    time_request,
    PROM_HANDLERS,
)


router = APIRouter(
    prefix="/review",
    tags=["review"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{platform}/{username}/task")
@time_request
async def get_review_task(
    request: Request,
    username: str,
    platform: PlatformEnum,
    db_session: DBSessionDep,
) -> LLMTask:

    task = await get_llm_task(db_session, username=username, platform=platform)
    if task is None:
        PROM_HANDLERS['request_count'].labels(
            "GET", "/review/{platform}/{username}/task", 404,
        ).inc()
        raise HTTPException(
            status_code=404,
            detail="LLM task not found, submit this profile for a review"
        )
    return task


@router.get("/tasks")
@time_request
async def get_all_review_tasks(
    db_session: DBSessionDep,
    request: Request,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    platform: Optional[PlatformEnum] = None,
    status: Optional[StatusEnum] = None,
    page: Optional[int] = None,
    rows_per_page: Optional[int] = None,
) -> List[LLMTask]:
    tasks =  await get_all_llm_tasks(
        db_session,
        from_date,
        to_date,
        platform,
        status,
        page,
        rows_per_page,
    )
    PROM_HANDLERS['request_count'].labels(
        "GET", "/review/tasks/", 200,
    ).inc()
    if tasks is None:
        return []
    return tasks


@router.post("/{platform}/{username}")
@time_request
async def submit_review_handler(
    username: str,
    request: Request,
    platform: PlatformEnum,
    db_session: DBSessionDep,
) -> GeneralResponse:
    task = await get_task(
        db_session,
        username=username,
        platform=platform
    )

    precheck_task(task, "/review/{{platform}}/{{username}}", "POST")
    # upsert llm_task
    llm_task_ids = await upsert_llm_tasks(
        db_session,
        [
            LLMTask(
                username=username,
                platform=platform,
                status=StatusEnum.pending,
            )
        ]
    )
    if llm_task_ids is None or len(llm_task_ids) == 0:
        PROM_HANDLERS['request_count'].labels(
            "POST", "/review//{{platform}}/{{username}}", 500,
        ).inc()
        return GeneralResponse(
            id=None,
            status=500,
            error='Failed to insert a llm task',
        )
    loop = asyncio.get_event_loop()
    loop.create_task(
        submit_llm_review(
            db_session,
            user=PlatformGuess(
                user_id=username,
                platform=platform,
            ),
            llm_task_id=llm_task_ids[0],
            task_id=task.id,
        )
    )
    PROM_HANDLERS['request_count'].labels(
        "POST", "/review//{{platform}}/{{username}}", 200,
    ).inc()
    return GeneralResponse(
        id=llm_task_ids[0],
        status=200,
        error=''
    )


@router.post("/")
@time_request
async def submit_multiple_reviews_handler(
    db_session: DBSessionDep,
    request: Request,
    req: MultipleReviewRequest,
) -> GeneralResponseMultiple:
    guesses = []
    for link in req.links:
        user_guess = guess_platform_and_extract_user_id(link)
        if user_guess is not None:
            guesses.append(user_guess)
    actual_tasks = [
        LLMTask(
            username=guess.user_id,
            platform=guess.platform,
            status=StatusEnum.pending,
        )
        for guess in guesses
    ]
    task_ids = await upsert_llm_tasks(db_session, actual_tasks)
    if task_ids is None:
        PROM_HANDLERS['request_count'].labels(
            "POST", "/review/", 500,
        ).inc()
        raise HTTPException(
            status_code=500,
            detail='Failed to create the specified llm tasks'
        )
    loop = asyncio.get_event_loop()
    loop.create_task(multiple_submit_llm_review(task_ids, db_session))

    PROM_HANDLERS['request_count'].labels(
        "POST", "/review/", 200,
    ).inc()
    return GeneralResponseMultiple(
        status=200,
        error='',
        ids=task_ids
    )


@router.get("/{platform}/{username}")
@time_request
async def get_review_handler(
    username: str,
    request: Request,
    platform: PlatformEnum,
    db_session: DBSessionDep,
) -> LLMReview:
    review = await get_review(db_session, username, platform)
    if review is None:
        PROM_HANDLERS['request_count'].labels(
            "GET", "/review/{{platform}}/{{username}}", 404,
        ).inc()
        raise HTTPException(
            status_code=404,
            detail="Review not found, submit this profile for a review"
        )
    PROM_HANDLERS['request_count'].labels(
        "GET", "/review/{{platform}}/{{username}}", 200,
    ).inc()
    return review
