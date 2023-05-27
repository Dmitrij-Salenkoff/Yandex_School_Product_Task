from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class CreateOrderDto(BaseModel):
    weight: float
    regions: int
    delivery_hours: List[str]
    cost: int


class OrderDto(BaseModel):
    order_id: int
    weight: float
    regions: int
    delivery_hours: List[str]
    cost: int
    completed_time: Optional[datetime] = None


class CreateOrderResponse(BaseModel):
    orders: List[OrderDto]


class GetOrderResponse(BaseModel):
    order: OrderDto


class CreateOrderRequest(BaseModel):
    orders: List[CreateOrderDto]


class GroupOrders(BaseModel):
    group_order_id: int
    orders: List[OrderDto]


class CouriersGroupOrders(BaseModel):
    courier_id: int
    orders: List[GroupOrders]


class OrderAssignResponse(BaseModel):
    date: date
    couriers: List[CouriersGroupOrders]


class CompleteOrder(BaseModel):
    courier_id: int
    order_id: int
    complete_time: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
        }


class CompleteOrderRequest(BaseModel):
    complete_info: List[CompleteOrder]
