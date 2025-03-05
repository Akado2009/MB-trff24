from pydantic import BaseModel
from typing import (
    Optional,
)
from schemas.general import PlatformEnum
import datetime


class ParsingTask(BaseModel):
    id: Optional[int] = None
    username: str
    platform: PlatformEnum
    status: str
    error_message: Optional[str] = ''
    is_reviewed: Optional[bool] = False
    is_id: Optional[bool] = False
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class LLMTask(BaseModel):
    id: Optional[int] = None
    username: str
    platform: PlatformEnum
    status: str
    error_message: Optional[str] = ''
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True
