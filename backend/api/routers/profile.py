from api.dependencies.core import DBSessionDep
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)
from fastapi import APIRouter
from schemas.general import (
    PlatformEnum,
)
from schemas.profile import (
    InstagramProfileResponse,
    FacebookProfileResponse,
)
from repository.task import (
    get_task,
)
from repository.profile import (
    get_instagram_profile_with_followees,
    get_posts_by_username,
    get_facebook_profile
)
from api.routers.utils import (
    precheck_task,
    convert_posts,
)
from prom.prometheus import (
    time_request,
    PROM_HANDLERS,
)


router = APIRouter(
    prefix="/profile",
    tags=["profile"],
    responses={404: {"description": "Not found"}},
)


@router.get("/instagram/{username}")
@time_request
async def get_instagram_profile_handler(
    db_session: DBSessionDep,
    request: Request,
    username: str,
    include_content: bool = False
) -> InstagramProfileResponse:
    # check status
    task = await get_task(
        db_session,
        username=username,
        platform=PlatformEnum.instagram,
    )
    precheck_task(task, "/instagram/{{username}}", "GET")
    # get profile
    profile = await get_instagram_profile_with_followees(
        db_session,
        username=username
    )
    if profile is None:
        PROM_HANDLERS['request_count'].labels(
            "GET", "/profile/instagram/{{username}}", 404,
        ).inc()
        raise HTTPException(
            status_code=404,
            etail="Profile somehow non existing, but the task exists"
        )
    # get followees
    posts = await get_posts_by_username(
        db_session,
        profile.username,
        platform=PlatformEnum.instagram
    )
    if include_content:
        posts = convert_posts(posts)

    PROM_HANDLERS['request_count'].labels(
        "GET", "/profile/instagram/{{username}}", 200,
    ).inc()
    return InstagramProfileResponse(
        profile=profile,
        posts=posts,
    )


@router.get("/facebook/{username}")
@time_request
async def get_facebook_profile_handler(
    db_session: DBSessionDep,
    request: Request,
    username: str,
    include_content: bool = False,
) -> FacebookProfileResponse:
    # check status
    task = await get_task(
        db_session,
        username=username,
        platform=PlatformEnum.facebook,
    )
    precheck_task(task, "/profile/facebook/{{username}}", "GET")
    # get profile
    profile = await get_facebook_profile(
        db_session,
        username=username,
    )
    if profile is None:
        PROM_HANDLERS['request_count'].labels(
            "GET", "/profile/facebook/{{username}}", 404,
        ).inc()
        raise HTTPException(
            status_code=404,
            detail="Profile somehow non existing, but the task exists"
        )
    # get followees
    posts = await get_posts_by_username(
        db_session,
        profile.username,
        platform=PlatformEnum.facebook
    )
    if include_content:
        posts = convert_posts(posts)

    PROM_HANDLERS['request_count'].labels(
        "GET", "/profile/facebook/{{username}}", 200,
    ).inc()
    return FacebookProfileResponse(
        profile=profile,
        posts=posts,
    )
