from pydantic import BaseModel
from typing import (
    List,
    Optional,
)
from schemas.general import (
    PlatformEnum,
)
from enum import Enum


class ParsingStatuses(str, Enum):
    pass


class PlatformGuess(BaseModel):
    platform: PlatformEnum
    user_id: str
    is_id: Optional[bool] = False


class SingleParserRequest(BaseModel):
    link: str


class MultipleParserRequest(BaseModel):
    links: List[str]
    send_to_llm: bool = False


class FileParserRequest(BaseModel):
    separator: str = ','
    send_to_llm: bool = False
