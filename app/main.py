from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api_limiter import limiter
from app.courier.router import courier_router
from app.database import engine, Base
from app.order.router import order_router


def get_application() -> FastAPI:
    application = FastAPI()
    application.include_router(order_router)
    application.include_router(courier_router)

    return application


app = get_application()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
