import os

from fastapi import FastAPI
from app.handlers import router
from app.config import VERSION, PROJECT_NAME, PROJECT_DESCRIPTION, BASE_ROUTER

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.config import DATABASE_URL

def create_db():
    engine = create_engine(DATABASE_URL)
    session = Session(bind=engine.connect())
    session.execute("""create table items(
        id varchar(256) primary key,
        parentId varchar(256),
        url varchar(255) NULL,
        size integer NULL,
        type varchar(6) NULL,
        updateDate varchar(256)
    );""")

    session.close()


def get_application() -> FastAPI:
    if not os.path.exists('fastapi_app.db'):
        create_db()
    application = FastAPI(title=PROJECT_NAME,
                          version=VERSION,
                          description=PROJECT_DESCRIPTION)
    application.include_router(router, tags=[BASE_ROUTER])
    return application



app = get_application()
