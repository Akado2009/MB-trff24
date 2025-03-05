from sqlalchemy.orm import (
    Mapped,
    mapped_column
)
from sqlalchemy import (
    func,
    DateTime,
    String,
)
import datetime
from . import Base


class ParsingTask(Base):
    __tablename__ = 'parsing_task'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(String(30), primary_key=True,  index=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(30), server_default='', nullable=False, index=True)
    status: Mapped[str] = mapped_column(default='')
    error_message: Mapped[str] = mapped_column(default='')
    is_reviewed: Mapped[bool] = mapped_column(default=False)
    is_id: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())


class LLMTask(Base):
    __tablename__ = 'llm_task'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(String(30), primary_key=True,  index=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(30), server_default='', nullable=False, index=True)
    status: Mapped[str] = mapped_column(default='')
    error_message: Mapped[str] = mapped_column(default='')

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.utcnow())
