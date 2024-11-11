from peewee import PostgresqlDatabase, Model, CharField, FixedCharField, IntegerField, ForeignKeyField, Check, AutoField

database = PostgresqlDatabase('elvis_test', user='elvis_test', password="hackme12345")

class BaseModel(Model):
    """A base model that will use our Postgresql database"""
    class Meta:
        database = database

class User(BaseModel):
    id = AutoField(primary_key=True, index=True, unique=True)
    username = CharField(unique=True)
    language = FixedCharField(4)

class Achievement(BaseModel):
    id = AutoField(primary_key=True, index=True, unique=True)
    score = IntegerField(constraints=[Check('score > 0')])

# Define achievement translations: Ru and En
class AchievementRu(BaseModel):
    id = ForeignKeyField(Achievement, backref='achievement')
    name = CharField()
    description = CharField()

class AchievementEn(BaseModel):
    id = ForeignKeyField(Achievement, backref='achievement')
    name = CharField()
    description = CharField()

# Define Many-to-Many relation between Users and Achievements
class UserAchievement(BaseModel):
    user = ForeignKeyField(User, backref='user')
    achievement = ForeignKeyField(Achievement, backref='achievement')

def create_db():
    with database:
        database.create_tables([User, Achievement, AchievementRu, AchievementEn, UserAchievement])

def drop_db():
    with database:
        database.drop_tables([User, Achievement, AchievementRu, AchievementEn, UserAchievement])
    
if __name__ == "__main__":
    drop_db()