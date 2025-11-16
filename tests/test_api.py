# Подключаем библиотеку pytest, которая позволяет удобно писать и запускать тесты.
import pytest

# Импортируем функцию create_app из нашего приложения.
# Она создаёт и настраивает объект Flask-приложения.
from app import create_app

# Импортируем объект db (база данных) из расширений.
from app.extensions import db

# Импортируем модель пользователя, чтобы в тестах можно было создавать админа.
from app.models import User


# Фикстура pytest с именем app.
# Фикстура — это такая "заготовка", которая подготавливает окружение для тестов.
@pytest.fixture
def app():
    # Создаём приложение во "внутреннем" тестовом режиме (testing=True).
    # В этом режиме используется отдельная тестовая база данных в памяти.
    app = create_app(testing=True)

    # Открываем контекст приложения.
    # Это нужно, чтобы можно было работать с базой данных и настройками приложения.
    with app.app_context():
        # Создаём все таблицы в тестовой базе (user, ticket и др.).
        db.create_all()

        # ---- создаём администратора ----
        # Создаём объект пользователя с логином "admin" и ролью "admin".
        admin = User(username="admin", role="admin")

        # Вызываем метод set_password, который хеширует пароль "adminpass".
        admin.set_password("adminpass")

        # Добавляем объект администратора в сессию базы данных.
        db.session.add(admin)

        # Сохраняем изменения в базе (вставляем запись в таблицу user).
        db.session.commit()

    # Передаём созданное приложение "наружу" в тесты.
    # Всё, что написано после yield, выполнится ПОСЛЕ завершения тестов (если нужно).
    yield app


# Вторая фикстура pytest — создаёт тестовый клиент.
# Клиент имитирует запросы к серверу, как будто это браузер или другая программа.
@pytest.fixture
def client(app):
    # Возвращаем специальный объект, с помощью которого можно делать запросы:
    # client.post(...), client.get(...) и т.п.
    return app.test_client()


# Тест №1: проверка регистрации и входа пользователя.
def test_register_and_login(client):
    # 1) Отправляем POST-запрос на маршрут /register для регистрации нового пользователя.
    # json={...} — это тело запроса в формате JSON, как будто работает фронтенд или мобильное приложение.
    r = client.post("/register", json={"username": "alice", "password": "pw"})

    # Проверяем, что сервер вернул статус 201 (Created — ресурс создан).
    assert r.status_code == 201

    # 2) Отправляем POST-запрос на /login — вход с теми же логином и паролем.
    r = client.post("/login", json={"username": "alice", "password": "pw"})

    # Ожидаем, что логин успешен, и сервер вернул статус 200 (OK).
    assert r.status_code == 200

    # Ответ сервера — JSON. Получаем его в виде словаря.
    # Проверяем, что роль у нового пользователя — "user".
    assert r.get_json()["role"] == "user"


# Тест №2: создание заявки и просмотр списка заявок.
def test_create_and_view_tickets(client):
    # Сначала регистрируем пользователя "bob".
    client.post("/register", json={"username": "bob", "password": "pw"})

    # Затем логинимся под пользователем "bob".
    client.post("/login", json={"username": "bob", "password": "pw"})

    # 3) Создаём заявку через POST /tickets.
    # В теле запроса передаём название и описание проблемы.
    r = client.post(
        "/tickets",
        json={"title": "Broken PC", "description": "No boot"},
    )

    # Ожидаем, что заявка успешно создана, и сервер ответит 201 (Created).
    assert r.status_code == 201

    # Достаём id созданной заявки из ответа JSON.
    tid = r.get_json()["id"]

    # 4) Запрашиваем список всех заявок текущего пользователя через GET /tickets.
    lst = client.get("/tickets").get_json()

    # Проверяем, что среди вернувшегося списка есть заявка с нужным id.
    # any(...) — проверяет, есть ли хотя бы один элемент, удовлетворяющий условию.
    assert any(t["id"] == tid for t in lst)


# Тест №3: проверяем, что один пользователь не может смотреть чужую заявку.
def test_user_cannot_view_others_ticket(client):
    # -------- Пользователь A --------
    # Регистрируем пользователя "u1".
    client.post("/register", json={"username": "u1", "password": "pw"})

    # Логинимся под "u1".
    client.post("/login", json={"username": "u1", "password": "pw"})

    # Создаём заявку от лица пользователя "u1".
    r = client.post("/tickets", json={"title": "A", "description": "B"})

    # Получаем id созданной заявки.
    tid = r.get_json()["id"]

    # Выходим из системы (logout).
    client.post("/logout")

    # -------- Пользователь B --------
    # Регистрируем второго пользователя "u2".
    client.post("/register", json={"username": "u2", "password": "pw"})

    # Логинимся под "u2".
    client.post("/login", json={"username": "u2", "password": "pw"})

    # 5) Пользователь B пытается получить доступ к заявке пользователя A.
    r = client.get(f"/tickets/{tid}")

    # Ожидаем, что сервер вернёт 403 (Forbidden — доступ запрещён).
    assert r.status_code == 403


# Тест №4: обновление и удаление заявки своим автором.
def test_put_and_delete_ticket(client):
    # Регистрируем пользователя "x".
    client.post("/register", json={"username": "x", "password": "pw"})

    # Логинимся под "x".
    client.post("/login", json={"username": "x", "password": "pw"})

    # Создаём заявку от пользователя "x".
    r = client.post("/tickets", json={"title": "T", "description": "D"})

    # Забираем id созданной заявки.
    tid = r.get_json()["id"]

    # 6) Обновляем заявку через PUT /tickets/<id>.
    # Передаём новое название и описание.
    r = client.put(
        f"/tickets/{tid}",
        json={"title": "NewT", "description": "NewD"},
    )

    # Ожидаем статус 200 (успешное обновление).
    assert r.status_code == 200

    # 7) Удаляем заявку через DELETE /tickets/<id>.
    r = client.delete(f"/tickets/{tid}")

    # Ожидаем статус 200 (успешное удаление).
    assert r.status_code == 200


# Тест №5: администратор может менять роль пользователя.
def test_admin_role_update(client):
    # Сначала логинимся под администратором.
    # Админ создаётся заранее в фикстуре app.
    r = client.post("/login", json={"username": "admin", "password": "adminpass"})

    # Проверяем, что логин успешен.
    assert r.status_code == 200

    # Создаём обычного пользователя "bob".
    client.post("/register", json={"username": "bob", "password": "pw"})

    # 8) Администратор запрашивает список всех пользователей через GET /users.
    users = client.get("/users").get_json()

    # Находим в списке пользователя с логином "bob".
    # next(...) берёт первый подходящий элемент из списка users.
    bob = next(u for u in users if u["username"] == "bob")

    # 9) Администратор отправляет запрос на изменение роли "bob" на "admin".
    r = client.put(f"/users/{bob['id']}", json={"role": "admin"})

    # Ожидаем, что сервер вернул 200 (успех).
    assert r.status_code == 200

    # Проверяем, что в ответе роль пользователя действительно стала "admin".
    assert r.get_json()["role"] == "admin"
