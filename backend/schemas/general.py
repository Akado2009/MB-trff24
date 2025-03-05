from pydantic import BaseModel
from typing import (
    List,
    Optional,
)
from enum import Enum


class StatusEnum(str, Enum):
    pending = 'pending'
    running = 'running'
    failed = 'failed'
    parsing_profile = 'parsing_profile'
    parsing_posts = 'parsing_posts'
    finished = 'finished'
    skipped = 'skipped'


class PlatformEnum(str, Enum):
    instagram = 'instagram'
    facebook = 'facebook'


class GeneralResponse(BaseModel):
    status: int
    error: Optional[str]
    id: Optional[int] = None


class GeneralResponseMultiple(BaseModel):
    status: int
    error: Optional[str]
    ids: Optional[List[int]] = []
