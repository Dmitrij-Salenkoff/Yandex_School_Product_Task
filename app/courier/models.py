from sqlalchemy import Column, INTEGER, Enum, String
from sqlalchemy.dialects.postgresql import ARRAY

from app.database import Base


class Courier(Base):
    __tablename__ = "couriers"

    id = Column('id', INTEGER, primary_key=True, autoincrement=True)
    type = Column('type', Enum('FOOT', 'BIKE', 'AUTO', name='courier_type'), nullable=False)
    regions = Column('regions', ARRAY(INTEGER), nullable=False)
    working_hours = Column('working_hours', ARRAY(String), nullable=False)
