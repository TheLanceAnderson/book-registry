from typing import Literal

from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=255)
    bought_by: str = Field(min_length=1, max_length=100)
    language: Literal["English", "Spanish"]