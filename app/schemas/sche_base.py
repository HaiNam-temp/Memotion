from typing import Optional, TypeVar, Generic
from pydantic.generics import GenericModel

from pydantic import BaseModel

T = TypeVar("T")


class ResponseSchemaBase(BaseModel):
    __abstract__ = True

    success: bool = True
    message: str = ''

    def custom_response(self, success: bool, message: str):
        self.success = success
        self.message = message
        return self

    def success_response(self):
        self.success = True
        self.message = 'Thành công'
        return self


class DataResponse(GenericModel, Generic[T]):
    success: bool = True
    message: str = ''
    data: Optional[T] = None

    class Config:
        arbitrary_types_allowed = True

    def custom_response(self, success: bool, message: str, data: T):
        self.success = success
        self.message = message
        self.data = data
        return self

    def success_response(self, data: T):
        self.success = True
        self.message = 'Thành công'
        self.data = data
        return self


class MetadataSchema(BaseModel):
    current_page: int
    page_size: int
    total_items: int
