from typing import Union
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start db
    db.create_db()
    yield

app = FastAPI(lifespan=lifespan)

class User(BaseModel):
    username: str
    language: str


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/user/{user_id}")
def read_item(user_id: int):
    with db.database:
        user = db.User.get_by_id(user_id)
        got_user = User(username=user.username, language=user.language)
    return got_user


@app.post("/user/")
def update_item(user: User):
    db.database.connect()
    new_user = db.User.create(username=user.username, language=user.language)
    new_user_id = new_user.id
    db.database.close()
    return new_user_id