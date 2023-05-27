from sqlalchemy import Column, INTEGER, String, FLOAT, ForeignKey
from sqlalchemy.dialects.postgresql import TIMESTAMP, ARRAY

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column('id', INTEGER, primary_key=True, autoincrement=True)
    weight = Column('weight', FLOAT, nullable=False)
    regions = Column('regions', INTEGER, nullable=False)
    delivery_hours = Column('delivery_hours', ARRAY(String), nullable=False)
    cost = Column('cost', INTEGER, nullable=False)


class CompletedOrder(Base):
    __tablename__ = 'completed_orders'

    id = Column('id', INTEGER, primary_key=True, autoincrement=True)
    courier_id = Column('courier_id', INTEGER, ForeignKey('couriers.id'), nullable=False)
    order_id = Column('order_id', INTEGER, ForeignKey('orders.id'), nullable=False)
    complete_time = Column('complete_time', TIMESTAMP, nullable=False)
