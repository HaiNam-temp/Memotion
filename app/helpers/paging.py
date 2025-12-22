import logging
from pydantic import BaseModel, conint
from abc import ABC, abstractmethod
from typing import Optional, Generic, Sequence, Type, TypeVar, List

from sqlalchemy import asc, desc
from sqlalchemy.orm import Query
from pydantic.generics import GenericModel
from contextvars import ContextVar

from app.schemas.sche_base import ResponseSchemaBase, MetadataSchema
from app.helpers.exception_handler import CustomException

T = TypeVar("T")
C = TypeVar("C")

logger = logging.getLogger()


class PaginationParams(BaseModel):
    page_size: Optional[conint(gt=0, lt=1001)] = 10
    page: Optional[conint(gt=0)] = 1
    sort_by: Optional[str] = 'created_at'
    order: Optional[str] = 'desc'


class Page(GenericModel, Generic[T]):
    code: str = ''
    message: str = ''
    data: List[T]
    metadata: MetadataSchema

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def create(cls, code: str, message: str, data: List[T], metadata: MetadataSchema) -> "Page[T]":
        return cls(
            code=code,
            message=message,
            data=data,
            metadata=metadata
        )

PageType: ContextVar[Type[Page]] = ContextVar("PageType", default=Page)


def paginate(model, query: Query, params: Optional[PaginationParams]) -> Page:
    code = '200'
    message = 'Success'

    try:
        total = query.count()

        if params.order:
            direction = desc if params.order == 'desc' else asc
            if hasattr(model, params.sort_by):
                query = query.order_by(direction(getattr(model, params.sort_by)))
            else:
                 # Fallback or ignore if sort_by field doesn't exist
                 pass

        data = query.limit(params.page_size).offset(params.page_size * (params.page-1)).all()

        metadata = MetadataSchema(
            current_page=params.page,
            page_size=params.page_size,
            total_items=total
        )

    except Exception as e:
        raise CustomException(http_code=500, code='500', message=str(e))

    return Page.create(code, message, data, metadata)
