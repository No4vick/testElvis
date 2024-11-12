from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

import db_functions as db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start db
    db.create_db()
    yield

app = FastAPI(lifespan=lifespan)

class User(BaseModel):
    id: Optional[int]
    username: str
    language: db.Language

class AchievementBase(BaseModel):
    id: Optional[int]
    score: int

class AchievementTranslation(BaseModel):
    language: db.Language
    title: Optional[str]
    description: Optional[str]

class Achievement(AchievementBase):
    translation: Optional[AchievementTranslation]

class AchievementFull(AchievementBase):
    translations: list[AchievementTranslation]


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
def create_item(user: User):
    return {"id": db.create_user(user.username, user.language)}

@app.post('/achievement/')
def create_achievement(score: int, translations: Optional[list[AchievementTranslation]]) -> AchievementBase:
    id = db.create_achievement(score=score)
    for tl in translations:
        db.translate_achievement(id, tl.language, tl.title, tl.description)
    return AchievementBase(id=id, score=score)

def achievement_db2type(db_achievement, db_translation, language: db.Language):
    if language and language is not db.Lang.ALL:
        if db_translation:
            achievement = Achievement(id=db_achievement.id, score=db_achievement.score, 
                                        translation=AchievementTranslation(language=language, 
                                                                           title=db_translation.title, 
                                                                           description=db_translation.description))
        else:
            achievement = Achievement(id=db_achievement.id, score=db_achievement.score, 
                                        translation=None)
        return achievement
    else:
        tls = []
        langs = [i for i in db.Lang][:-1]
        for lang, tl in zip(langs, db_translation):
            if tl:
                tls.append(AchievementTranslation(language=lang, title=tl.title, description=tl.description))
        achievement = AchievementFull(id=db_achievement.id, score=db_achievement.score, translations=tls)
        return achievement
    

@app.get('/achievement/{achievement_id}')
def get_achievement(id: int, language: Optional[db.Language]):
    if language and language is not db.Lang.ALL:
        db_achievement, db_translation = db.get_achievement(id, language)
        achievement = achievement_db2type(db_achievement, db_translation, language)
        return achievement
    else:
        db_achievement, db_translation = db.get_achievement(id, db.Lang.ALL)
        achievement = achievement_db2type(db_achievement, db_translation, language)
        return achievement

@app.get('/achievement')
def get_achievements(language: Optional[db.Language]):
    db_achievements = db.get_achievements(language if language else db.Lang.ALL)
    achievements = []
    for db_achievement in db_achievements:
        achievements.append(achievement_db2type(db_achievement[0], db_achievement[1], language))
    return achievements

@app.put('/achievement/translate/{achievement_id}')
def update_achievement_translation(id: int, translation: AchievementTranslation):
    db.translate_achievement(id, translation.language, translation.title, translation.description)
    return