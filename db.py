from peewee import PostgresqlDatabase, CharField, FixedCharField, IntegerField, ForeignKeyField, Check, AutoField, DateTimeField, fn
from playhouse.signals import Model as SignalModel, post_save

database = PostgresqlDatabase('elvis_test', user='elvis_test', password="hackme12345")

class BaseModel(SignalModel):
    """A base model that will use our Postgresql database"""
    class Meta:
        database = database

class User(BaseModel):
    id = AutoField(primary_key=True, index=True, unique=True)
    username = CharField(unique=True)
    language = FixedCharField(4)
    total_score = IntegerField()

class Achievement(BaseModel):
    id = AutoField(primary_key=True, index=True, unique=True)
    score = IntegerField(constraints=[Check('score > 0')])

# Define achievement translations: Ru and En
class AchievementRu(BaseModel):
    id = ForeignKeyField(Achievement, backref='achievement', column_name='id', primary_key=True)
    title = CharField()
    description = CharField()

class AchievementEn(BaseModel):
    id = ForeignKeyField(Achievement, backref='achievement', column_name='id', primary_key=True)
    title = CharField()
    description = CharField()

# Define Many-to-Many relationship between User and Achievement
class UserAchievement(BaseModel):
    user = ForeignKeyField(User, backref='user')
    achievement = ForeignKeyField(Achievement, backref='achievement')
    date = DateTimeField()

@post_save(sender=UserAchievement)
def recount_user_score(sender, instance, created):
    if created:
        user = instance.user
        total_score = (UserAchievement
                       .select(fn.SUM(Achievement.score))
                       .join(Achievement)
                       .where(UserAchievement.user == user)
                       .scalar())
        user.total_score = total_score
        user.save()
