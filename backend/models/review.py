from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from sqlalchemy import (
    func,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import (
    TEXT,
)
import datetime
from . import Base


class LLMReview(Base):
    __tablename__ = 'llm_review'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    platform: Mapped[str] = mapped_column(String(30), server_default='', nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(30), nullable=False)

    profile_section: Mapped[str] = mapped_column(TEXT, server_default='')
    market_section: Mapped[str] = mapped_column(TEXT, server_default='')
    psycho_section: Mapped[str] = mapped_column(TEXT, server_default='')
    socio_section: Mapped[str] = mapped_column(TEXT, server_default='')
    client_section: Mapped[str] = mapped_column(TEXT, server_default='')
    tags_section: Mapped[str] = mapped_column(TEXT, server_default='')

    # market_score_section: Mapped[str] = mapped_column(TEXT, server_default='')
    # psycho_score_section: Mapped[str] = mapped_column(TEXT, server_default='')
    # socio_score_section: Mapped[str] = mapped_column(TEXT, server_default='')
    # client_score_section: Mapped[str] = mapped_column(TEXT, server_default='')
    final_review_section: Mapped[str] = mapped_column(TEXT, server_default='')

    status_code: Mapped[int] = mapped_column(Integer, default=200)
    error: Mapped[str] = mapped_column(TEXT, server_default='')

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())
