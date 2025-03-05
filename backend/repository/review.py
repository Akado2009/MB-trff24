from models.review import (
    LLMReview as DBLLMReview
)
from schemas.review import (
    LLMReview
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
    convert_review_raw,
)
from logger import LOGURU_LOGGER
from prom.prometheus import PROM_HANDLERS


async def insert_review(
    db_session: AsyncSession,
    review: LLMReview,
) -> Union[int, None]:
    try:
        ins_stmt = insert(DBLLMReview).values([
            review.model_dump(exclude_none=True)
        ])
        do_update_stmt = ins_stmt.on_conflict_do_update(
            constraint="llm_review_pkey",
            set_=dict(
                status_code=ins_stmt.excluded.status_code,
                profile_section=ins_stmt.excluded.profile_section,
                market_section=ins_stmt.excluded.market_section,
                psycho_section=ins_stmt.excluded.psycho_section,
                socio_section=ins_stmt.excluded.socio_section,
                client_section=ins_stmt.excluded.client_section,
                tags_section=ins_stmt.excluded.tags_section,
                final_review_section=ins_stmt.excluded.final_review_section,
                error=ins_stmt.excluded.error,
            )
        ).returning(
            DBLLMReview.id
        )
        result = await db_session.execute(statement=do_update_stmt)
        await db_session.commit()
        # unsafe code :)
        return result.first()[0]
    except Exception as e:
        await db_session.rollback()
        LOGURU_LOGGER.error(f"Error inserting a review {review.username} on platform {review.platform}: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('insert_review').inc()
        return None


async def get_review(
    db_session: AsyncSession,
    username: str,
    platform: str,
) -> Union[LLMReview, None]:
    try:
        statement = select(DBLLMReview).where(
            DBLLMReview.platform == platform,
            DBLLMReview.username == username,
        )
        result = await db_session.execute(statement=statement)
        result = result.first()[0]
        return convert_review_raw(result)
    except Exception as e:
        LOGURU_LOGGER.error(f"Error getting a review: {e}")
        PROM_HANDLERS['failed_db_queries'].labels('get_review').inc()
        return None
