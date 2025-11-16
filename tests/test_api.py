import pytest
from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()

        # создаём администратора
        admin = User(username="admin", role="admin")
        admin.set_password("adminpass")
        db.session.add(admin)
        db.session.commit()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_register_and_login(client):
    # 1) POST /register - пользователь
    r = client.post("/register", json={"username": "alice", "password": "pw"})
    assert r.status_code == 201

    # 2) POST /login - корректная авторизация
    r = client.post("/login", json={"username": "alice", "password": "pw"})
    assert r.status_code == 200
    assert r.get_json()["role"] == "user"


def test_create_and_view_tickets(client):
    client.post("/register", json={"username": "bob", "password": "pw"})
    client.post("/login", json={"username": "bob", "password": "pw"})

    # 3) POST /tickets — создание заявки
    r = client.post("/tickets", json={"title": "Broken PC", "description": "No boot"})
    assert r.status_code == 201
    tid = r.get_json()["id"]

    # 4) GET /tickets — пользователь видит только свои заявки
    lst = client.get("/tickets").get_json()
    assert any(t["id"] == tid for t in lst)


def test_user_cannot_view_others_ticket(client):
    # user A
    client.post("/register", json={"username": "u1", "password": "pw"})
    client.post("/login", json={"username": "u1", "password": "pw"})

    r = client.post("/tickets", json={"title": "A", "description": "B"})
    tid = r.get_json()["id"]

    client.post("/logout")

    # user B
    client.post("/register", json={"username": "u2", "password": "pw"})
    client.post("/login", json={"username": "u2", "password": "pw"})

    # 5) GET /tickets/<id> — пользователь НЕ может видеть чужое
    r = client.get(f"/tickets/{tid}")
    assert r.status_code == 403


def test_put_and_delete_ticket(client):
    client.post("/register", json={"username": "x", "password": "pw"})
    client.post("/login", json={"username": "x", "password": "pw"})

    r = client.post("/tickets", json={"title": "T", "description": "D"})
    tid = r.get_json()["id"]

    # 6) PUT /tickets/<id> — обновление заявки
    r = client.put(f"/tickets/{tid}", json={"title": "NewT", "description": "NewD"})
    assert r.status_code == 200

    # 7) DELETE /tickets/<id>
    r = client.delete(f"/tickets/{tid}")
    assert r.status_code == 200


def test_admin_role_update(client):
    # логин админом (созданным в фикстуре)
    r = client.post("/login", json={"username": "admin", "password": "adminpass"})
    assert r.status_code == 200

    # создаём пользователя
    client.post("/register", json={"username": "bob", "password": "pw"})

    # 8) GET /users — админ видит всех
    users = client.get("/users").get_json()
    bob = next(u for u in users if u["username"] == "bob")

    # 9) PUT /users/<id> — изменение роли
    r = client.put(f"/users/{bob['id']}", json={"role": "admin"})
    assert r.status_code == 200
    assert r.get_json()["role"] == "admin"
