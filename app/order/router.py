import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.api_limiter import limiter, REQUEST_LIMIT
from app.courier.models import Courier
from app.courier.schemas import BadRequestResponse, NotFoundResponse
from app.database import get_async_session
from app.order.models import Order, CompletedOrder
from app.order.schemas import CreateOrderRequest, CompleteOrderRequest, OrderDto

order_router = APIRouter(prefix="/orders")


@order_router.get('/',
                  response_model=List[OrderDto | None],
                  responses={'400': {'model': BadRequestResponse}},
                  tags=['order-controller'])
@limiter.limit(REQUEST_LIMIT)
async def get_orders(request: Request, offset: Optional[int] = 0, limit: Optional[int] = 1,
                     session: AsyncSession = Depends(get_async_session)):
    query = select(Order).offset(offset).limit(limit)
    result = await session.execute(query)
    orders = result.all()
    response = []
    if not orders:
        return []
    for order in orders:
        query = select(CompletedOrder.complete_time).where(CompletedOrder.order_id == order[0].id)
        result = await session.execute(query)
        completed_time = result.scalar()
        if not completed_time:
            completed_time = None
        response.append(OrderDto(order_id=order[0].id, weight=order[0].weight,
                                 regions=order[0].regions, delivery_hours=order[0].delivery_hours,
                                 cost=order[0].cost, completed_time=completed_time))
    return response


@order_router.get('/{order_id}',
                  response_model=OrderDto,
                  responses={
                      '400': {'model': BadRequestResponse},
                      '404': {'model': NotFoundResponse}},
                  tags=['order-controller'])
@limiter.limit(REQUEST_LIMIT)
async def get_order_by_id(request: Request, order_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(Order).where(Order.id == order_id)
    result = await session.execute(query)
    order = result.scalar()

    query = select(CompletedOrder.complete_time).where(CompletedOrder.order_id == order_id)
    result = await session.execute(query)
    if not order:
        return JSONResponse(status_code=404, content={"message": "Item not found"})
    completed_time = result.all()
    if not completed_time:
        completed_time = None
    else:
        completed_time = completed_time[0].complete_time

    return OrderDto(order_id=order.id, weight=order.weight,
                    regions=order.regions, delivery_hours=order.delivery_hours,
                    cost=order.cost, completed_time=completed_time)


@order_router.post('/',
                   response_model=List[OrderDto],
                   responses={'400': {'model': BadRequestResponse}},
                   tags=['order-controller'])
@limiter.limit(REQUEST_LIMIT)
async def add_order(request: Request, new_orders: CreateOrderRequest,
                    session: AsyncSession = Depends(get_async_session)):
    # logging.warning(new_orders)
    try:
        query = insert(Order).values([order.dict() for order in new_orders.orders]).returning(Order)
        result = await session.execute(query)
    except Exception as e:
        logging.warning(e)
        return JSONResponse(status_code=400, content={"message": "bad request"})
    else:
        result = [OrderDto(order_id=order.id, weight=order.weight,
                           regions=order.regions, delivery_hours=order.delivery_hours,
                           cost=order.cost) for order in result.all()]

        await session.commit()
        return result


@order_router.post('/complete',
                   response_model=List[OrderDto],
                   responses={'400': {'model': BadRequestResponse}},
                   tags=['order-controller'])
@limiter.limit(REQUEST_LIMIT)
async def set_complete(request: Request, completed_orders_list: CompleteOrderRequest,
                       session: AsyncSession = Depends(get_async_session)):
    completed_orders_id_list = []
    for complete_order in completed_orders_list.complete_info:
        query = select(Order).where(Order.id == complete_order.order_id)
        result = await session.execute(query)
        error_1 = not bool(result.scalar())

        query = select(CompletedOrder).where(CompletedOrder.order_id == complete_order.order_id)
        result = await session.execute(query)
        error_2 = bool(result.scalar())

        query = select(Courier).where(Courier.id == complete_order.courier_id)
        result = await session.execute(query)
        error_3 = not bool(result.scalar())

        # TODO: Сделать нормальную обработку статусов
        if error_1:
            return JSONResponse(status_code=400,
                                content={"message": f"Заказа {complete_order.order_id} не нашлось в таблице заказов"})
        elif error_2:
            return JSONResponse(status_code=400, content={"status": f"Этот заказ уже выполнен курьером"})
        elif error_3:
            return JSONResponse(status_code=400, content={
                "status": f"Курьера {complete_order.courier_id} не нашлось в таблице курьеров"})

        query = insert(CompletedOrder).values(**complete_order.dict()).returning(CompletedOrder.order_id)
        result = await session.execute(query)
        completed_orders_id_list.append(result.scalar())

    query = select(Order, CompletedOrder).where(Order.id == CompletedOrder.order_id).where(Order.id.in_(completed_orders_id_list))
    result = await session.execute(query)
    result = result.all()
    result = [OrderDto(order_id=order.id, weight=order.weight,
                       regions=order.regions, delivery_hours=order.delivery_hours,
                       cost=order.cost, completed_time=completion.complete_time) for order, completion in result]
    await session.commit()
    return result
