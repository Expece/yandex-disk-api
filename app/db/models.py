from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum


from app.config import DATABASE_URL


Base = declarative_base()


def connection_db():
    engine = create_engine(DATABASE_URL, connect_args={})
    session = Session(bind=engine.connect())
    return session


class Type(Enum):
    FILE = 'FILE'
    FOLDER = 'FOLDER'


class Item(Base):
    """Класс для предствления таблицы items"""
    __tablename__ = 'items'

    id = Column(String, primary_key=True)
    parentId = Column(String)
    url = Column(String(255), nullable=True)
    size = Column(Integer, nullable=True)
    type = Column(String)
    updateDate = Column(String)
