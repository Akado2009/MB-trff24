from models.task import (
    ParsingTask as DBParsingTask,
    LLMTask as DBLLMTask,
)
from schemas.task import (
    ParsingTask,
    LLMTask,
)
from sqlalchemy.dialects.postgresql import (
    insert,
)
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import (
    List,
    Union,
)
from repository.utils import (
    convert_task_row,
    convert_llm_task_row,
)
from schemas.general import (
    PlatformEnum,
    StatusEnum,
)
from schemas.parser import (
    PlatformGuess,
)
from datetime import datetime
from logger import LOGURU_LOGGER
from prom.prometheus import PROM_HANDLERS


STRING_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


# parsing task
async def insert_task(
    db_session: AsyncSession,
    task: ParsingTask,
) -> Union[int, None]:
    try:
        statement = insert(DBParsingTask).values([task.model_dump(exclude_none=True)]).returning(
            DBParsingTask.id
        )
        result = await db_session.execute(statement=statement)
        await db_session.commit()
        return result.first()[0]
    except Exception as e:
        LOGURU_LOGGER.error(f"Error inserting a task: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('insert_task').inc()
        await db_session.rollback()
        return None

async def upsert_tasks(
    db_session: AsyncSession,
    tasks: List[ParsingTask]
) -> Union[List[int], None]:
    try:
        ins_stmt = insert(DBParsingTask).values(
            [
                task.model_dump(exclude_none=True)
                for task in tasks
            ]
        )
        do_update_stmt = ins_stmt.on_conflict_do_update(
            constraint="parsing_task_pkey",
            set_=dict(
                status=ins_stmt.excluded.status,
                error_message=ins_stmt.excluded.error_message,
                is_reviewed=ins_stmt.excluded.is_reviewed,
            )
        ).returning(
            DBParsingTask.id,
        )
        result = await db_session.execute(statement=do_update_stmt)
        await db_session.commit()
        return [res[0] for res in result.all()]
        # # unsafe code :)
        # return result.first()[0]
    except Exception as e:
        LOGURU_LOGGER.error(f"Error upserting tasks: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('upsert_tasks').inc()
        await db_session.rollback()
        return None

async def update_task(
    db_session: AsyncSession,
    task_id: int,
    task_status: str = '',
    error_message: str = '',
) -> Union[int, None]:
    try:
        statement = update(DBParsingTask).where(DBParsingTask.id == task_id).values(
            status=task_status,
            error_message=error_message,
        ).returning(DBParsingTask.id)
        result = await db_session.execute(statement=statement)
        await db_session.commit()
        return result.first()[0]
    except Exception as e:
        LOGURU_LOGGER.error(f"Error updating a task: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('update_task').inc()
        await db_session.rollback()
        return None

async def update_task_is_reviewed(
    db_session: AsyncSession,
    task_id: int,
    is_reviewed: bool = False
) -> Union[int, None]:
    try:
        statement = update(DBParsingTask).where(DBParsingTask.id == task_id).values(
            is_reviewed=is_reviewed,
        ).returning(DBParsingTask.id)
        result = await db_session.execute(statement=statement)
        await db_session.commit()
        return result.first()[0]
    except Exception as e:
        LOGURU_LOGGER.error(f"Error updating a task's is_reviewed: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('update_task_is_reviewed').inc()
        await db_session.rollback()
        return None

async def get_task(
    db_session: AsyncSession,
    t_id: int = None,
    username: str = None,
    platform: str = "instagram",
) -> Union[ParsingTask, None]:
    try:
        statement = None
        if t_id is None and username is None:
            LOGURU_LOGGER.warning(f"Provide a username or an id for a task")
            return None
        if t_id is not None:
            statement = select(DBParsingTask).where(
                DBParsingTask.id == t_id,
                DBParsingTask.platform == platform
            )
        else:
            statement = select(DBParsingTask).where(
                DBParsingTask.username == username,
                DBParsingTask.platform == platform,
            )
        result = await db_session.execute(statement=statement)
        result = result.first()[0]
        return convert_task_row(result)
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting a task: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_task').inc()
        return None

async def get_all_tasks(
    db_session: AsyncSession,
    from_date: Union[str, None],
    to_date: Union[str, None],
    platform: Union[str, None],
    status: Union[str, None],
    is_reviewed: Union[bool, None],
    page: Union[int, None],
    rows_per_page: Union[int, None],
) -> Union[List[ParsingTask], None]:
    selectors = []
    if from_date is not None:
        from_date = datetime.strptime(
            from_date,
            STRING_FORMAT
        )
        selectors.append(DBParsingTask.created_at >= from_date)
    if to_date is not None:
        to_date = datetime.strptime(
            to_date,
            STRING_FORMAT
        )
        selectors.append(DBParsingTask.created_at <= to_date)
    if platform is not None and platform  in PlatformEnum:
        selectors.append(DBParsingTask.platform == platform)
    if status is not None and status in StatusEnum:
        selectors.append(DBParsingTask.status == status)
    if is_reviewed in [True, False]:
        selectors.append(DBParsingTask.is_reviewed == is_reviewed)
    try:
        statement = select(DBParsingTask)
        if len(selectors) != 0:
            statement = select(DBParsingTask).where(
                and_(
                    *selectors,
                )
            )

        if page is not None and rows_per_page is not None:
            if page > 0 and rows_per_page > 0:
                statement = statement.limit(rows_per_page).offset(
                    (page - 1) * rows_per_page
                )
        result = await db_session.execute(statement=statement)
        result = result.all()
        return list(map(lambda x: convert_task_row(x[0]), result))
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting all tasks: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_all_tasks').inc()
        return None

async def get_all_tasks_for_platform(
    db_session: AsyncSession,
    platform: str = "instagram"
) -> Union[List[ParsingTask], None]:
    try:
        statement = select(DBParsingTask).where(DBParsingTask.platform == platform)
        result = await db_session.execute(statement=statement)
        result = result.all()
        return list(map(lambda x: convert_task_row(x[0]), result))
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting all tasks for platform: {platform}: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_all_tasks_for_platform').inc()
        return None

async def get_pending_tasks(
    db_session: AsyncSession,
) -> List[ParsingTask]:
    try:
        statement = select(DBParsingTask).where(DBParsingTask.status == StatusEnum.pending)
        result = await db_session.execute(statement=statement)
        result = result.all()
        return list(map(lambda x: convert_task_row(x[0]), result))
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting pending tasks: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_pending_tasks').inc()
        return []

async def get_tasks_by_ids(
    db_session: AsyncSession,
    ids: List[int]
) -> List[ParsingTask]:
    try:
        statement = select(DBParsingTask).where(DBParsingTask.id.in_(tuple(ids)))
        result = await db_session.execute(statement=statement)
        result = result.all()
        return list(map(lambda x: convert_task_row(x[0]), result))
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting tasks by ids: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_tasks_by_ids').inc()
        return []

async def get_tasks_by_guesses(
    db_session: AsyncSession,
    guesses: List[PlatformGuess]
) -> List[ParsingTask]:
    try:
        if len(guesses) == 0:
            return []
        conditions = [
            and_(
                DBParsingTask.username == guess.user_id,
                DBParsingTask.platform == guess.platform
            )
            for guess in guesses
        ]
        statement = select(DBParsingTask).where(
            or_(
                *conditions
            )
        )
        result = await db_session.execute(statement=statement)
        result = result.all()
        return list(map(lambda x: convert_task_row(x[0]), result))
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting tasks by ids: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_tasks_by_guesses').inc()
        return []

# llm tasks
async def insert_llm_task(
    db_session: AsyncSession,
    task: LLMTask,
) -> Union[int, None]:
    try:
        statement = insert(DBLLMTask).values([task.model_dump(exclude_none=True)]).returning(
            DBLLMTask.id
        )
        result = await db_session.execute(statement=statement)
        await db_session.commit()
        return result.first()[0]
    except Exception as e:
        LOGURU_LOGGER.error(f"Error inserting a llm task: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('insert_llm_task').inc()
        return None

async def upsert_llm_tasks(
    db_session: AsyncSession,
    tasks: List[LLMTask]
) -> Union[List[int], None]:
    try:
        ins_stmt = insert(DBLLMTask).values(
            [
                task.model_dump(exclude_none=True)
                for task in tasks
            ]
        )
        do_update_stmt = ins_stmt.on_conflict_do_update(
            constraint="llm_task_pkey",
            set_=dict(
                status=ins_stmt.excluded.status,
                error_message=ins_stmt.excluded.error_message,
            )
        ).returning(
            DBLLMTask.id,
        )
        result = await db_session.execute(statement=do_update_stmt)
        await db_session.commit()
        return [res[0] for res in result.all()]
    except Exception as e:
        LOGURU_LOGGER.error(f"Error upserting llm tasks: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('upsert_llm_tasks').inc()
        await db_session.rollback()
        return None

async def update_llm_task(
    db_session: AsyncSession,
    task_id: int,
    task_status: str = '',
    error_message: str = '',
) -> Union[int, None]:
    try:
        statement = update(DBLLMTask).where(DBLLMTask.id == task_id).values(
            status=task_status,
            error_message=error_message,
        ).returning(DBLLMTask.id)
        result = await db_session.execute(statement=statement)
        await db_session.commit()
        return result.first()[0]
    except Exception as e:
        LOGURU_LOGGER.error(f"Error updating a llm task: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('update_llm_task').inc()
        await db_session.rollback()
        return None

async def get_llm_task(
    db_session: AsyncSession,
    t_id: int = None,
    username: str = None,
    platform: str = "instagram",
) -> Union[ParsingTask, None]:
    try:
        statement = None
        if t_id is None and username is None:
            LOGURU_LOGGER.warning(f"Provide a username or an id for a llm task")
            return None
        if t_id is not None:
            statement = select(DBLLMTask).where(
                DBLLMTask.id == t_id,
                DBLLMTask.platform == platform
            )
        else:
            statement = select(DBLLMTask).where(
                DBLLMTask.username == username,
                DBLLMTask.platform == platform,
            )
        result = await db_session.execute(statement=statement)
        result = result.first()[0]
        return convert_llm_task_row(result)
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting a llm task: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_llm_task').inc()
        return None

async def get_all_llm_tasks(
    db_session: AsyncSession,
    from_date: Union[str, None],
    to_date: Union[str, None],
    platform: Union[str, None],
    status: Union[str, None],
    page: Union[int, None],
    rows_per_page: Union[int, None],
) -> Union[List[ParsingTask], None]:
    selectors = []
    if from_date is not None:
        from_date = datetime.strptime(
            from_date,
            STRING_FORMAT
        )
        selectors.append(DBLLMTask.created_at >= from_date)
    if to_date is not None:
        to_date = datetime.strptime(
            to_date,
            STRING_FORMAT
        )
        selectors.append(DBLLMTask.created_at <= to_date)
    if platform is not None and platform  in PlatformEnum:
        selectors.append(DBLLMTask.platform == platform)
    if status is not None and status in StatusEnum:
        selectors.append(DBLLMTask.status == status)
    try:
        statement = select(DBLLMTask)
        if len(selectors) != 0:
            statement = select(DBLLMTask).where(
                and_(
                    *selectors,
                )
            )

        if page is not None and rows_per_page is not None:
            if page > 0 and rows_per_page > 0:
                statement = statement.limit(rows_per_page).offset(
                    (page - 1) * rows_per_page
                )
        result = await db_session.execute(statement=statement)
        result = result.all()
        return list(map(lambda x: convert_llm_task_row(x[0]), result))
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting all llm tasks: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_all_llm_tasks').inc()
        return None

async def get_llm_tasks_by_ids(
    db_session: AsyncSession,
    ids: List[int]
) -> List[ParsingTask]:
    try:
        statement = select(DBLLMTask).where(DBLLMTask.id.in_(tuple(ids)))
        result = await db_session.execute(statement=statement)
        result = result.all()
        return list(map(lambda x: convert_llm_task_row(x[0]), result))
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting llm tasks by ids: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_llm_tasks_by_ids').inc()
        return []
