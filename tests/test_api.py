import pytest
from fastapi.testclient import TestClient
from main import app
from db_functions import create_db, drop_db, create_user, grant_user_achievement, create_achievement, Lang
import datetime

from peewee import PostgresqlDatabase
database = PostgresqlDatabase('test_elvis_test', user='elvis_test', password="hackme12345")

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    create_db()
    yield
    drop_db()

@pytest.fixture(autouse=True)
def transaction():
    create_db()
    yield
    database.rollback()
    database.close()

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

def test_create_user():
    response = client.post("/user/", json={"username": "testuser", "language": "en"})
    assert response.status_code == 200
    assert "id" in response.json()

def test_create_achievement():
    response = client.post("/achievement/", json={"score": 10, "translations": [{"language": "en", "title": "Test Achievement", "description": "Test Description"}]})
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["score"] == 10

def test_grant_user_achievement():
    user_id = create_user('testuser', Lang.EN)
    achievement_id = create_achievement(10)
    response = client.post("/achievement/grant", json={"user_id": user_id, "achievement_id": achievement_id, "datetime": None, "translation": None})
    assert response.status_code == 200

def test_get_user_achievements():
    user_id = create_user('testuser', Lang.EN)
    achievement_id = create_achievement(10)
    grant_user_achievement(user_id, achievement_id)
    response = client.get(f"/achievements/{user_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_users_with_streak():
    user_id = create_user('testuser', Lang.EN)
    now = datetime.datetime.now()

    # Create achievements for the last 7 days
    for i in range(7):
        import random
        achievement_id = create_achievement(random.randint(1, 10))
        grant_user_achievement(user_id, achievement_id, now - datetime.timedelta(days=i))

    response = client.get("/statistics/streak", params={"limit": 10})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1
    assert response.json()[0]["id"] == user_id

def test_get_user_with_max_achievements():
    user_id = create_user('testuser', Lang.EN)
    create_user('testuser2', Lang.EN)
    for _ in range(10):
        import random
        achievement_id = create_achievement(random.randint(1, 10))
        grant_user_achievement(user_id, achievement_id)
    response = client.get("/statistics/max_achievements")
    assert response.status_code == 200
    assert "user" in response.json()
    assert "count" in response.json()
    assert response.json()["user"]["id"] == user_id

def test_get_user_with_max_score():
    user_id = create_user('testuser', Lang.EN)
    create_user('testuser2', Lang.EN)
    for _ in range(10):
        import random
        achievement_id = create_achievement(random.randint(1, 10))
        grant_user_achievement(user_id, achievement_id)
    response = client.get("/statistics/max_score")
    assert response.status_code == 200
    assert "id" in response.json()
    assert "username" in response.json()
    assert "total_score" in response.json()

def test_get_users_with_max_diff():
    user_id = create_user('testuser', Lang.EN)
    create_user('testuser2', Lang.EN)
    for _ in range(10):
        import random
        achievement_id = create_achievement(random.randint(1, 10))
        grant_user_achievement(user_id, achievement_id)
    response = client.get("/statistics/max_diff")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_users_with_min_diff():
    user_id = create_user('testuser', Lang.EN)
    create_user('testuser2', Lang.EN)
    for _ in range(10):
        import random
        achievement_id = create_achievement(random.randint(1, 10))
        grant_user_achievement(user_id, achievement_id)
    response = client.get("/statistics/min_diff")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_user():
    user_id = create_user('testuser', Lang.EN)
    response = client.get(f"/user/{user_id}")
    assert response.status_code == 200
    assert "id" in response.json()
    assert "username" in response.json()
    assert "language" in response.json()
    assert "total_score" in response.json()
    assert "achievements" in response.json()