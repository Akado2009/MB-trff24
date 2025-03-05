from pydantic import BaseModel
from typing import (
    Optional,
    List,
)
import datetime
from schemas.general import PlatformEnum


class MultipleReviewRequest(BaseModel):
    links: List[str]


class   LLMReview(BaseModel):
    id: Optional[int] = None
    platform: PlatformEnum
    username: str

    profile_section: Optional[str] = ''
    market_section: Optional[str] = ''
    psycho_section: Optional[str] = ''
    socio_section: Optional[str] = ''
    client_section: Optional[str] = ''
    tags_section: Optional[str] = ''

    # market_score_section: Optional[str] = ''
    # psycho_score_section: Optional[str] = ''
    # socio_score_section: Optional[str] = ''
    # client_score_section: Optional[str] = ''
    final_review_section: Optional[str] = ''

    status_code: Optional[int] = 200
    error: Optional[str] = ''

    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True
