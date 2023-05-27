from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel


class CourierType(Enum):
    FOOT = 'FOOT'
    BIKE = 'BIKE'
    AUTO = 'AUTO'


class CreateCourier(BaseModel):
    type: CourierType
    regions: List[int]
    working_hours: List[str]

    class Config:
        use_enum_values = True
        orm_mode = True


class CourierDto(CreateCourier):
    id: int


class CreateCourierRequest(BaseModel):
    couriers: List[CreateCourier]


class CreateCouriersResponse(BaseModel):
    couriers: List[CourierDto]


class GetCouriersResponse(BaseModel):
    couriers: List[CourierDto] = []
    limit: int
    offset: int


class GetCourierMetaInfoResponse(BaseModel):
    courier_id: int
    courier_type: CourierType
    regions: List[int]
    working_hours: List[str]
    rating: Optional[int] = None
    earnings: Optional[int] = None


class NotFoundResponse(BaseModel):
    message: str = 'not found'


class BadRequestResponse(BaseModel):
    message: str = 'bad request'
