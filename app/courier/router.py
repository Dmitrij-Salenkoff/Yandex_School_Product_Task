import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.api_limiter import limiter, REQUEST_LIMIT
from app.courier.models import Courier
from app.courier.schemas import CreateCouriersResponse, BadRequestResponse, CreateCourierRequest, CourierDto, \
    NotFoundResponse, GetCouriersResponse, GetCourierMetaInfoResponse
from app.database import get_async_session
from app.order.models import Order, CompletedOrder

coef_payement = {'FOOT': 2, 'BIKE': 3, 'AUTO': 4}
coef_rating = {'FOOT': 3, 'BIKE': 2, 'AUTO': 1}

courier_router = APIRouter(prefix="/couriers")


@courier_router.post('/', tags=['courier-controller']
    , response_model=CreateCouriersResponse
    , responses={'400': {'model': BadRequestResponse}})
@limiter.limit(REQUEST_LIMIT)
async def add_courier(request: Request, new_couriers: CreateCourierRequest,
                      session: AsyncSession = Depends(get_async_session)):
    try:
        query = insert(Courier).values([courier.dict() for courier in new_couriers.couriers]).returning(Courier)
        result = await session.execute(query)
    # TODO: Возможно стоит поменять вид исключения
    except Exception as e:
        logging.warning(e)
        return JSONResponse(status_code=400, content={"message": "bad request"})
    else:
        await session.commit()
        return CreateCouriersResponse(couriers=[CourierDto(id=courier.id,
                                                           type=courier.type,
                                                           regions=courier.regions,
                                                           working_hours=courier.working_hours)
                                                for courier in result.all()])


@courier_router.get('/{courier_id}', tags=['courier-controller']
    , response_model=CourierDto
    , responses={'400': {'model': BadRequestResponse},
                 '404': {'model': NotFoundResponse}})
@limiter.limit(REQUEST_LIMIT)
async def get_courier_by_id(request: Request, courier_id: int, session: AsyncSession = Depends(get_async_session)):
    try:
        query = select(Courier).where(Courier.id == courier_id)
        result = await session.execute(query)
        result = result.scalar()
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": "bad request"})
    else:
        if result:
            return result
        return JSONResponse(status_code=404, content={"message": "Item not found"})


@courier_router.get('/', tags=['courier-controller']
    , response_model=GetCouriersResponse
    , responses={'400': {'model': BadRequestResponse}})
@limiter.limit(REQUEST_LIMIT)
async def get_couriers(request: Request, offset: Optional[int] = 0, limit: Optional[int] = 1,
                       session: AsyncSession = Depends(get_async_session)):
    if limit < 0 or offset < 0:
        return JSONResponse(status_code=400, content={"message": "Недопустимые значения параметров"})
    query = select(Courier).offset(offset).limit(limit)
    result = await session.execute(query)
    result = result.all()
    if not result:
        return GetCouriersResponse(limit=limit,
                                   offset=offset)
    return GetCouriersResponse(limit=limit,
                               offset=offset,
                               couriers=[CourierDto(id=courier[0].id,
                                                    type=courier[0].type,
                                                    regions=courier[0].regions,
                                                    working_hours=courier[0].working_hours)
                                         for courier in result])


@courier_router.get(
    '/meta-info/{courier_id}',
    response_model=GetCourierMetaInfoResponse,
    tags=['courier-controller'])
@limiter.limit(REQUEST_LIMIT)
async def get_meta_info(request: Request, courier_id: int, start_date: str, end_date: str,
                        session: AsyncSession = Depends(get_async_session)):
    t0, t1 = datetime.strptime(start_date, "%Y-%m-%d").date(), datetime.strptime(end_date, "%Y-%m-%d").date()

    query = select(Order, Courier, CompletedOrder) \
        .where(CompletedOrder.order_id == Order.id) \
        .where(CompletedOrder.courier_id == Courier.id) \
        .where(CompletedOrder.courier_id == courier_id) \
        .where(CompletedOrder.complete_time >= t0) \
        .where(CompletedOrder.complete_time < t1)

    result = await session.execute(query)
    result = result.all()

    if result:
        total_earnings = 0
        for order, courier, completed_order in result:
            total_earnings += order.cost * coef_payement[courier.type]

        courier_one = result[0][1]
        total_rating = len(result) / ((t1 - t0).total_seconds() / (60 * 60)) * coef_rating[courier_one.type]

        return GetCourierMetaInfoResponse(courier_id=courier_one.id, courier_type=courier_one.type,
                                          regions=courier_one.regions, working_hours=courier_one.working_hours,
                                          rating=total_rating, earnings=total_earnings)
    else:
        query = select(Courier).where(Courier.id == courier_id)
        result = await session.execute(query)
        result = result.scalar()

        return GetCourierMetaInfoResponse(courier_id=result.id, courier_type=result.type,
                                          regions=result.regions, working_hours=result.working_hours)
