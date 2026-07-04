from sqlalchemy import Column, Integer, String
from database import Base
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    role = Column(String)
class Property(Base):
    __tablename__ = "properties"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    location = Column(String)
    price = Column(String)
    property_type = Column(String)
    bedrooms = Column(Integer)
    description = Column(String)
    broker = Column(String)
    image = Column(String)
    status = Column(String, default="Active") 