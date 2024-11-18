import functools
import datetime
from enum import Enum
from typing import NewType
from peewee import fn

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
    new_user = User.create(username=username, language=language.value, total_score=0)
    return new_user.id

@db_transaction
def get_user(user_id: int) -> User:
    user = User.get_by_id(user_id)
    return user

@db_transaction
def get_user_language(user_id: int) -> Language:
    user = User.get_by_id(user_id)
    return user.language

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
    match(Lang(language)):
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

@db_transaction
def grant_user_achievement(user_id: int, achievement_id: int, date: datetime.datetime = datetime.datetime.now()) -> None:
    UserAchievement.create(user_id=user_id, achievement_id=achievement_id, date=date)

@db_transaction
def get_user_achievements(user_id: int) -> list:
    user_achievements = [ua.achievement_id for ua in UserAchievement.select().where(UserAchievement.user_id == user_id)]
    return user_achievements

@db_transaction
def get_achievements_translations(achievement_ids: list[int], language: Language) -> list:
    translations = []
    for achievement_id in achievement_ids:
        translation = get_translation(achievement_id, language)
        translations.append(translation)
    return translations

@db_transaction
def get_user_with_max_achievements() -> tuple[User, int]:
    user = (User
            .select(User, fn.Count(UserAchievement.id).alias('achievement_count'))
            .join(UserAchievement)
            .group_by(User.id)
            .order_by(fn.Count(UserAchievement.id).desc())
            .get())
    return user, user.achievement_count

@db_transaction
def get_user_with_max_score() -> User:
    user = User.select().order_by(User.total_score.desc()).get()
    return user

@db_transaction
def get_users_with_min_score_diff() -> list:
    users = User.select().order_by(User.total_score)
    closest_pair = None
    min_difference = float('inf')

    for i in range(len(users) - 1):
        user1 = users[i]
        user2 = users[i + 1]
        score_difference = abs(user1.total_score - user2.total_score)

        if score_difference < min_difference:
            min_difference = score_difference
            closest_pair = (user1, user2)

        if min_difference == 0:
            break

    return closest_pair

@db_transaction
def get_users_with_max_score_diff() -> tuple[User]:
    max_score_user = (User
                      .select()
                      .order_by(User.total_score.desc())
                      .limit(1)
                      .get())
    min_score_user = (User
                      .select()
                      .order_by(User.total_score.asc())
                      .limit(1)
                      .get())
    return max_score_user, min_score_user

@db_transaction
def get_users_achievements(users: list[int]) -> list:
    users_achievements = {}
    for user_id in users:
        user_achievements = get_user_achievements(user_id)
        total_score = User.get_by_id(user_id).total_score
        users_achievements[user_id] = (user_achievements, total_score)
    return users_achievements

@db_transaction
def get_users_with_streak(day_streak: int = 7, limit: int = 100) -> list:
    streak_users = []
    users = User.select().limit(limit) if limit > 0 else User.select()
    for user in users:
        streak = 0
        day_difference = datetime.timedelta(days=0)
        now = datetime.datetime.now()
        for ua in UserAchievement.select().where(UserAchievement.user_id == user.id).order_by(UserAchievement.date.desc()):
            print(ua.date.date())
            if ua.date.date() == (now - day_difference).date():
                streak += 1
                day_difference += datetime.timedelta(days=1)
            else:
                break
        if streak >= day_streak:
            streak_users.append(user)
    return streak_users

if __name__ == "__main__":
    # drop_db()
    # create_db()
    # user_id = create_user('testuser', Lang.EN)
    # now = datetime.datetime.now()
    # for i in range(7):
    #     import random
    #     achievement_id = create_achievement(random.randint(1, 10))
    #     grant_user_achievement(user_id, achievement_id, now - datetime.timedelta(days=i))
    print(get_users_with_min_score_diff())