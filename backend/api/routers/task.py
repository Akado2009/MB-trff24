from api.dependencies.core import DBSessionDep
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

from typing import (
    List,
    Optional,
)
from schemas.general import (
    PlatformEnum,
    StatusEnum,
    GeneralResponse,
)
from schemas.task import (
    ParsingTask,
)
from repository.task import (
    insert_task,
    get_all_tasks,
    get_all_tasks_for_platform,
    get_task,
)
from prom.prometheus import (
    time_request,
    PROM_HANDLERS,
)


router = APIRouter(
    prefix="/task",
    tags=["task"],
    responses={404: {"description": "Not found"}},
)


@router.post("/")
@time_request
async def create_task_handler(
    db_session: DBSessionDep,
    request: Request,
    task: ParsingTask,
) -> GeneralResponse:
    res = await insert_task(db_session, task)
    if res is None:
        PROM_HANDLERS['request_count'].labels(
            "POST", "/task/", 500,
        ).inc()
        return GeneralResponse(
            status=500,
            id=None,
            error="Failed to create a task"
        )
    PROM_HANDLERS['request_count'].labels(
        "POST", "/task/", 200,
    ).inc()
    return GeneralResponse(
        status=200,
        id=res,
        error=""
    )


@router.get("/")
@time_request
async def get_all_tasks_handler(
    db_session: DBSessionDep,
    request: Request,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    platform: Optional[PlatformEnum] = None,
    status: Optional[StatusEnum] = None,
    is_reviewed: Optional[bool] = None,
    page: Optional[int] = None,
    rows_per_page: Optional[int] = None,
) -> List[ParsingTask]:
    PROM_HANDLERS['request_count'].labels(
        "GET", "/task/", 200,
    ).inc()
    return await get_all_tasks(
        db_session,
        from_date,
        to_date,
        platform,
        status,
        is_reviewed,
        page,
        rows_per_page,
    )


@router.get("/{platform}")
@time_request
async def get_all_tasks_for_platform_handler(
    db_session: DBSessionDep,
    request: Request,
    platform: PlatformEnum,
) -> List[ParsingTask]:
    PROM_HANDLERS['request_count'].labels(
        "GET", "/task/", 200,
    ).inc()
    return await get_all_tasks_for_platform(db_session, platform)


@router.get("/{platform}/{username}/username")
@time_request
async def get_task_for_platform_user_handler(
    db_session: DBSessionDep,
    request: Request,
    platform: PlatformEnum,
    username: str,
) -> ParsingTask:
    task = await get_task(db_session, username=username, platform=platform)
    if task is None:
        PROM_HANDLERS['request_count'].labels(
            "GET", "/task/{{platform}}/{{username}}/username", 404,
        ).inc()
        raise HTTPException(
            status_code=404,
            detail="Task not found, submit this profile"
        )

    PROM_HANDLERS['request_count'].labels(
        "GET", "/task/{{platform}}/{{username}}/username", 200,
    ).inc()
    return task


@router.get("/{platform}/{id}/id")
@time_request
async def get_task_for_platform_user_handler(
    db_session: DBSessionDep,
    request: Request,
    platform: PlatformEnum,
    id: int,
) -> ParsingTask:
    task = await get_task(db_session, t_id=id, platform=platform)
    if task is None:
        PROM_HANDLERS['request_count'].labels(
            "GET", "/task/{{platform}}/{{id}}/id", 404,
        ).inc()
        raise HTTPException(
            status_code=404,
            detail="Task not found, submit this profile"
        )
    PROM_HANDLERS['request_count'].labels(
        "GET", "/task/{{platform}}/{{id}}/id", 200,
    ).inc()
    return task
