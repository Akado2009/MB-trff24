from api.dependencies.core import DBSessionDep
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    Request,
    HTTPException,
)
from fastapi.responses import StreamingResponse
from schemas.parser import (
    SingleParserRequest,
    MultipleParserRequest,
    FileParserRequest,
)
from tasks.parser import (
    parse_social_network,
    multiple_parse_social_network,
)
from schemas.general import (
    PlatformEnum,
    GeneralResponse,
    GeneralResponseMultiple,
    StatusEnum,
)
from api.routers.utils import (
    guess_platform_and_extract_user_id,
    parse_csv,
    parse_excel,
)
from repository.task import (
    insert_task,
    get_task,
    update_task,
    upsert_tasks,
)
from schemas.task import (
    ParsingTask,
)
from prom.prometheus import (
    time_request,
    PROM_HANDLERS,
)
import asyncio
import os
from typing import (
    List,
)


TEMPLATES_DIR = "data/templates"
CSV_CONTENT_TYPE = "text/csv"
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


router = APIRouter(
    prefix="/parser",
    tags=["parser"],
    responses={404: {"description": "Not found"}},
)


@router.post("/submit/single")
@time_request
async def submit_single(
    db_session: DBSessionDep,
    req: SingleParserRequest,
    request: Request,
) -> GeneralResponse:
    user_guess = guess_platform_and_extract_user_id(req.link)
    if user_guess is None:
        PROM_HANDLERS['request_count'].labels(
            "POST", "/parser/submit/single", 422,
        ).inc()
        raise HTTPException(
            status_code=422,
            detail="Wrong link provided for parsing.",
        )
    # create/update task here
    task = await get_task(
        db_session,
        username=user_guess.user_id,
        platform=user_guess.platform,
    )
    task_id = None
    if task is None:
        task_id = await insert_task(
            db_session,
            ParsingTask(
                username=user_guess.user_id,
                platform=user_guess.platform,
                status=StatusEnum.running,
                is_id=user_guess.is_id,
            )
        )
    else:
        task_id = await update_task(
            db_session,
            task_id=task.id,
            task_status="running"
        )

    loop = asyncio.get_event_loop()
    loop.create_task(parse_social_network(user_guess, db_session, task_id))
    PROM_HANDLERS['request_count'].labels(
        "POST", "/parser/submit/single", 200,
    ).inc()
    return GeneralResponse(
        status=200,
        id=task_id,
        error=''
    )


@router.post("/submit/multiple")
@time_request
async def submit_multiple(
    db_session: DBSessionDep,
    req: MultipleParserRequest,
    request: Request,
) -> GeneralResponseMultiple:
    guesses = []
    for link in req.links:
        user_guess = guess_platform_and_extract_user_id(link)
        if user_guess is not None:
            guesses.append(user_guess)
    actual_tasks = [
        ParsingTask(
            username=guess.user_id,
            platform=guess.platform,
            is_id=guess.is_id,
            status=StatusEnum.pending,
        )
        for guess in guesses
    ]
    task_ids = await upsert_tasks(db_session, actual_tasks)
    if task_ids is None:
        PROM_HANDLERS['request_count'].labels(
            "POST", "/parser/submit/multiple", 500,
        ).inc()
        raise HTTPException(
            status_code=500,
            detail='Failed to create the specified tasks'
        )
    loop = asyncio.get_event_loop()
    loop.create_task(multiple_parse_social_network(task_ids, db_session))
    PROM_HANDLERS['request_count'].labels(
        "POST", "/parser/submit/multiple", 200,
    ).inc()
    return GeneralResponseMultiple(
        status=200,
        error='',
        ids=task_ids
    )


@router.post("/submit/file")
@time_request
async def submit_file(
    db_session: DBSessionDep,
    request: Request,
    req: FileParserRequest = Depends(),
    links_file: UploadFile = File(...)
) -> GeneralResponseMultiple:
    if links_file.content_type not in [
        XLSX_CONTENT_TYPE,
        CSV_CONTENT_TYPE,
    ]:
        PROM_HANDLERS['request_count'].labels(
            "POST", "/parser/submit/file", 400,
        ).inc()
        raise HTTPException(
            status_code=400,
            detail="Only support csv and xlsx.",
        )
    task_ids = []
    try:
        content = links_file.file.read()
        guesses = []
        if links_file.content_type == CSV_CONTENT_TYPE:
            guesses = parse_csv(content)
        if links_file.content_type == XLSX_CONTENT_TYPE:
            guesses = parse_excel(content)
        actual_tasks = [
            ParsingTask(
                username=guess.user_id,
                platform=guess.platform,
                is_id=guess.is_id,
                status=StatusEnum.pending,
            )
            for guess in guesses
        ]
        task_ids = await upsert_tasks(db_session, actual_tasks)
        if task_ids is None:
            raise HTTPException(
                status_code=500,
                detail='Failed to create the specified tasks'
            )
        loop = asyncio.get_event_loop()
        loop.create_task(multiple_parse_social_network(task_ids, db_session))
    except Exception as e:
        print(e)

        PROM_HANDLERS['request_count'].labels(
            "POST", "/parser/submit/file", 500,
        ).inc()
        return

    PROM_HANDLERS['request_count'].labels(
        "POST", "/parser/submit/file", 200,
    ).inc()
    return GeneralResponseMultiple(
        status=200,
        error='',
        ids=task_ids,
    )


@router.get("/template/csv")
@time_request
async def get_csv_template(
    request: Request,
) -> StreamingResponse:
    file = open(
        os.path.join(
            TEMPLATES_DIR,
            "template.csv",
        ),
        "rb"
    )
    PROM_HANDLERS['request_count'].labels(
        "GET", "/parser/template/csv", 200,
    ).inc()
    return StreamingResponse(
        iter([file.read()]),
        media_type=CSV_CONTENT_TYPE,
        headers={"Content-Disposition": f"attachment; filename=template.csv"}
    )


@router.get("/template/xlsx")
@time_request
async def get_xlsx_template(
    request: Request,
) -> StreamingResponse:
    file = open(
        os.path.join(
            TEMPLATES_DIR,
            "template.xlsx",
        ),
        "rb"
    )
    PROM_HANDLERS['request_count'].labels(
        "GET", "/parser/template/xlsx", 200,
    ).inc()
    return StreamingResponse(
        iter([file.read()]),
        media_type=XLSX_CONTENT_TYPE,
        headers={"Content-Disposition": f"attachment; filename=template.xlsx"}
    )
