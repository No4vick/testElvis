from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

import datetime

import app.db_functions as db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start db
    db.create_db()
    yield

app = FastAPI(lifespan=lifespan)

class User(BaseModel):
    id: Optional[int]
    username: str
    language: Optional[db.Language]

class UserInput(BaseModel):
    username: str
    language: db.Language

class AchievementBase(BaseModel):
    id: Optional[int]
    score: int

class UserStats(User):
    total_score: int
    achievements: Optional[list[AchievementBase]]

class AchievementTranslation(BaseModel):
    language: db.Language
    title: Optional[str]
    description: Optional[str]

class AchievementCreateInput(BaseModel):
    score: int
    translations: Optional[list[AchievementTranslation]]

class Achievement(AchievementBase):
    translation: Optional[AchievementTranslation]

class AchievementFull(AchievementBase):
    translations: list[AchievementTranslation]

class UserAchievement(BaseModel):
    user_id: int
    achievement_id: int
    datetime: Optional[datetime.datetime]
    translation: Optional[AchievementTranslation]

class UserFull(BaseModel):
    id: int
    username: str
    language: db.Language
    total_score: int
    achievements: list[AchievementFull]

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/user")
def create_user(user: UserInput) -> dict:
    user = db.create_user(user.username, user.language)
    return {'id': user}

@app.post('/achievement')
def create_achievement(achievement: AchievementCreateInput) -> AchievementBase:
    score = achievement.score
    translations = achievement.translations
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

def achievement_db2user_type(db_achievement, db_translation, language: db.Language):
    if language and language is not db.Lang.ALL:
        if db_translation:
            achievement = UserAchievement(id=db_achievement.id, score=db_achievement.score, date_granted=db_achievement.date_granted,
                                        translation=AchievementTranslation(language=language, 
                                                                           title=db_translation.title, 
                                                                           description=db_translation.description))
        else:
            achievement = UserAchievement(id=db_achievement.id, score=db_achievement.score, date_granted=db_achievement.date_granted,
                                        translation=None)
        return achievement
    else:
        raise ValueError("Language must be specified")

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

@app.post('/achievement/grant')
def grant_user_achievement(achievement: UserAchievement):
    if achievement.datetime:
        db.grant_user_achievement(achievement.user_id, achievement.achievement_id, achievement.datetime)
    else:
        db.grant_user_achievement(achievement.user_id, achievement.achievement_id)
    return

@app.get('/achievements/{user_id}')
def get_user_achievements(user_id: int):
    db_achievements = db.get_user_achievements(user_id)
    achievements: list[Achievement] = []
    lang = db.get_user_language(user_id)
    for db_achievement in db_achievements:
        db_achievement, db_translation = db.get_achievement(db_achievement, lang)
        achievements.append(achievement_db2type(db_achievement, db_translation, lang))
    return achievements

@app.get('/statistics/max_achievements')
def get_user_with_max_achievements() -> dict:
    user, count = db.get_user_with_max_achievements()
    return {'user': UserStats(id=user.id, username=user.username, language=user.language, total_score=user.total_score, achievements=get_user_achievements(user.id)), 'count': count}

@app.get('/statistics/max_score')
def get_user_with_max_score() -> UserStats:
    user = db.get_user_with_max_score()
    return UserStats(id=user.id, username=user.username, language=user.language, total_score=user.total_score, achievements=get_user_achievements(user.id))

@app.get('/statistics/max_diff')
def get_users_with_max_diff() -> list[UserStats]:
    users = db.get_users_with_max_score_diff()
    return [UserStats(id=user.id, username=user.username, language=user.language, total_score=user.total_score, achievements=get_user_achievements(user.id)) for user in users]

@app.get('/statistics/min_diff')
def get_users_with_min_diff() -> list[UserStats]:
    users = db.get_users_with_min_score_diff()
    return [UserStats(id=user.id, username=user.username, language=user.language, total_score=user.total_score, achievements=None) for user in users]

@app.get('/statistics/streak')
def get_users_with_streak(limit: int = 10) -> list[UserStats]:
    users = db.get_users_with_streak(7, limit)
    return [UserStats(id=user.id, username=user.username, language=user.language, total_score=user.total_score, achievements=get_user_achievements(user.id)) for user in users]

@app.get('/user/{user_id}')
def get_user(user_id: int) -> UserFull:
    user = db.get_user(user_id)
    return UserFull(id=user.id, username=user.username, language=user.language, total_score=user.total_score, achievements=get_user_achievements(user_id))