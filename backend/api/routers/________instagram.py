from api.dependencies.core import DBSessionDep
from schemas.general import (
    LLMRewviewModel,
)
import requests
from schemas.general import GeneralResponse
from fastapi import APIRouter, HTTPException, BackgroundTasks
from tasks.instagram import parse_instagram
from repository.instagram import (
    get_profile_with_followees,
)
from repository.general import (
    insert_review,
    get_review,
)
from typing import (
    List,
    Union,
)
from config import settings
from api.routers.utils import (
    precheck_task,
    submit_instagram_review,
)


router = APIRouter(
    prefix="/api/instagram",
    tags=["instagram"],
    responses={404: {"description": "Not found"}},
)


# @router.post("/single")
# async def parse_single_instagram(
#     profile: InstagramProfileRequest,
#     db_session: DBSessionDep,
#     background_tasks: BackgroundTasks,
# ) -> GeneralResponse:
#     background_tasks.add_task(parse_instagram, profile.username, db_session)
#     return GeneralResponse(status=200, error=None)


# # get all tasks
# @router.get("/tasks")
# async def all_tasks(
#     db_session: DBSessionDep,
# ) -> List[InstagramTask]:
#     return await get_all_tasks(db_session)


# @router.get("/tasks/{id}/id")
# async def task_by_id(
#     id: int,
#     db_session: DBSessionDep,
# ) -> InstagramTask:
#     task = await get_task(db_session, t_id=id)
#     if task is None:
#         raise HTTPException(status_code=404, detail="Task not found")
#     return task

# @router.get("/tasks/{username}/username")
# async def task_by_username(
#     username: str,
#     db_session: DBSessionDep,
# ) -> InstagramTask:
#     task = await get_task(db_session, username=username)
#     if task is None:
#         raise HTTPException(status_code=404, detail="Task not found")
#     return task


# @router.get("/profile/{username}/username")
# async def profile_by_username(
#     username: str,
#     db_session: DBSessionDep,
# ) -> InstagramProfileResponse:
#     # check status
#     task = await get_task(db_session, username=username)
#     precheck_task(task)
#     # get profile
#     profile = await get_profile_with_followees(db_session, username=username)
#     if profile is None:
#         raise HTTPException(status_code=404, detail="Profile somehow non existing, but the task exists")
#     # get followees
#     posts = await get_posts_by_username(db_session, profile.username)
#     posts = convert_posts(posts)
#     return InstagramProfileResponse(
#         profile=profile,
#         posts=posts,
#     )


# @router.post("/review/{username}")
# async def review_profile(
#     username: str,
#     db_session: DBSessionDep,
# ) -> GeneralResponse:
#     task = await get_task(db_session, username=username)
#     precheck_task(task)
#     # get profile
#     profile = await get_profile_with_followees(db_session, username=username)
#     if profile is None:
#         raise HTTPException(status_code=404, detail="Profile somehow non existing, but the task exists")
#     # get followees
#     posts = await get_posts_by_username(db_session, profile.username)
#     posts = convert_posts(posts)

#     review, err = submit_instagram_review(profile, posts)
#     # review = "test_query"
#     # err = {
#     #     "status": 404,
#     #     "reason": "Not found."
#     # }
#     rev = LLMRewviewModel(
#         id=None,
#         username=username,
#         platform="instagram",
#         review=review,
#         status_code=err["status"],
#         error=err["reason"]
#     )
#     rev_id = await insert_review(db_session, rev)
#     return GeneralResponse(status=200, error=None)


# @router.get("/review/{username}/{platform}")
# async def get_profile_review(
#     db_session: DBSessionDep,
#     username: str,
#     platform: str,
# ) -> LLMRewviewModel:
#     review = await get_review(db_session, username, platform)
#     if review is None:
#         raise HTTPException(status_code=404, detail="Review not found")
#     return review
