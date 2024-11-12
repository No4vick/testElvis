import functools
from enum import Enum
from typing import NewType

from db import database, User, Achievement, AchievementRu, AchievementEn, UserAchievement

class Lang(Enum):
    EN = 'en'
    RU = 'ru'
    ALL = 'all'

Language = NewType('Language', Lang)

def db_transaction(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        database.connect()
        res = func(*args, **kwargs)
        database.close()
        return res
    return wrapper


def create_db():
    with database:
        database.create_tables([User, Achievement, AchievementRu, AchievementEn, UserAchievement])

def drop_db():
    with database:
        database.drop_tables([User, Achievement, AchievementRu, AchievementEn, UserAchievement])
    
@db_transaction
def create_user(username: str, language: Language) -> int:
    new_user = User.create(username=username, language=language)
    return new_user.id

@db_transaction
def create_achievement(score: int) -> int:
    achievement = Achievement.create(score=score)
    return achievement.id

@db_transaction
def translate_achievement(id: int, language: Language, title: str, description: str) -> tuple[Achievement, bool]:
    match(language):
        case Lang.EN:
            translation, created = AchievementEn.get_or_create(id=id, defaults={'title': title, 'description': description})
        case Lang.RU:
            translation, created = AchievementRu.get_or_create(id=id, defaults={'title': title, 'description': description})
    if created:
        translation.update(title=title, description=description)
    return translation, created

def get_translation(id: int, language: Language):
    match(language):
        case Lang.EN:
            translation = AchievementEn.get_or_none(id=id)
        case Lang.RU:
            translation = AchievementRu.get_or_none(id=id)
        case Lang.ALL:
            translation = [AchievementEn.get_or_none(id=id), AchievementRu.get_or_none(id=id)]
    return translation

@db_transaction
def get_achievement(id: int, language: Language) -> tuple[Achievement, list]:
    achievement = Achievement.get_by_id(id)
    translation = get_translation(id, language)
    return achievement, translation

def get_achievements(language=Language):
    with database:
        achievements_query = Achievement.select()
        achievements_list = []
        for achievement in achievements_query:
            achievements_list.append((achievement, get_translation(achievement.id, language)))
    return achievements_list

if __name__ == "__main__":
    drop_db()
    create_db()