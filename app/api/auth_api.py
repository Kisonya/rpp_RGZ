# Импортируем функцию Blueprint из Flask.
# Blueprint — это способ логически разделить наше приложение на отдельные "модули" (разделы).
# В данном случае у нас будет отдельный модуль для API авторизации (регистрация, вход, выход).
from flask import Blueprint, request, jsonify

# Импортируем функции из Flask-Login:
# - login_user — "залогинить" пользователя, то есть сохранить информацию о входе в систему.
# - logout_user — "разлогинить", то есть удалить информацию о входе.
# - login_required — специальный декоратор, который не пускает на маршрут, если пользователь не авторизован.
from flask_login import login_user, logout_user, login_required

# Импортируем объект db — это наша база данных, через которую мы будем сохранять и читать данные.
from app.extensions import db

# Импортируем модель User — это класс, который описывает таблицу пользователей в базе.
from app.models import User


# Создаём Blueprint с именем "auth_api".
# "auth_api" — это внутреннее имя этого модуля.
# __name__ — технический параметр, который Flask использует, чтобы понимать, откуда загружен этот Blueprint.
auth_api = Blueprint("auth_api", __name__)


# ------------ РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ ------------

# Этот декоратор говорит: когда на адрес /register придёт HTTP-запрос с методом POST,
# нужно вызвать функцию register().
@auth_api.post("/register")
def register():
    # Получаем JSON-данные из тела запроса: например {"username": "ivan", "password": "123"}.
    # request.get_json() — это метод, который достаёт JSON из запроса.
    # Если данных нет (None), то мы подставляем пустой словарь {} с помощью "or {}".
    data = request.get_json() or {}

    # Достаём имя пользователя из словаря data.
    # data.get("username") — берём значение по ключу "username". Если ключа нет, вернётся None.
    # (data.get("username") or "") — если значение пустое (None или пустая строка), подставляем "" (пустая строка),
    # чтобы не вызвать ошибку при .strip().
    # .strip() — метод строки, который убирает пробелы в начале и в конце (например "  ivan  " → "ivan").
    username = (data.get("username") or "").strip()

    # Аналогично достаём пароль.
    password = (data.get("password") or "").strip()

    # Проверяем, что пользователь действительно прислал и логин, и пароль.
    # Если username пустой ИЛИ password пустой, значит данные введены некорректно.
    if not username or not password:
        # jsonify(...) — превращает словарь в JSON-ответ.
        # Возвращаем ошибку и HTTP-код 400 (Bad Request — неправильный запрос).
        return jsonify({"error": "username and password required"}), 400

    # Проверяем, существует ли уже пользователь с таким именем.
    # User.query.filter_by(username=username).first() — поиск в базе по полю username.
    # Если пользователь найден — выражение вернёт объект User, если нет — None.
    if User.query.filter_by(username=username).first():
        # Если такой пользователь уже есть — возвращаем ошибку.
        return jsonify({"error": "user exists"}), 400

    # Если всё хорошо — создаём нового пользователя.
    # Передаём username и роль. По условию — при регистрации обычный пользователь всегда
    # должен иметь роль "user" (не администратор).
    user = User(username=username, role="user")

    # Устанавливаем пароль пользователю.
    # user.set_password(password) — это не просто сохранение пароля, а его шифрование (хеширование).
    # В базе хранится не сам пароль, а его зашифрованная версия — это безопаснее.
    user.set_password(password)

    # Добавляем нового пользователя в сессию базы данных.
    # Пока это только "подготовка" к сохранению.
    db.session.add(user)

    # Сохраняем изменения окончательно — теперь запись реально попадает в базу.
    db.session.commit()

    # Формируем JSON-ответ с данными созданного пользователя.
    # Мы возвращаем id, username и role — чтобы клиент (например, Postman или фронтенд) понимал,
    # кто был создан.
    # HTTP-код 201 означает "Created" — успешно создан новый ресурс.
    return jsonify(
        {"id": user.id, "username": user.username, "role": user.role}
    ), 201


# ------------ ВХОД ПОЛЬЗОВАТЕЛЯ (АВТОРИЗАЦИЯ) ------------

# Обрабатываем POST-запросы на /login.
@auth_api.post("/login")
def login():
    # Аналогично, достаём JSON-данные из запроса.
    data = request.get_json() or {}

    # Берём имя пользователя, обрезаем пробелы.
    username = (data.get("username") or "").strip()

    # Берём пароль, обрезаем пробелы.
    password = (data.get("password") or "").strip()

    # Проверяем, что оба поля заполнены.
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    # Ищем пользователя в базе по имени.
    user = User.query.filter_by(username=username).first()

    # Проверяем:
    # 1) Нашёлся ли пользователь (user не None)
    # 2) Совпадает ли пароль (user.check_password(password) возвращает True, если пароль правильный)
    if not user or not user.check_password(password):
        # Если либо пользователя нет, либо пароль неправильный — возвращаем ошибку.
        return jsonify({"error": "invalid credentials"}), 400

    # Если всё хорошо — "логиним" пользователя.
    # login_user(user) создаёт для пользователя сессию (запоминает, что он сейчас авторизован).
    login_user(user)

    # Возвращаем успешный ответ: message = "ok" и роль пользователя.
    # Роль может быть "user" или "admin" — её можно использовать на фронтенде.
    return jsonify({"message": "ok", "role": user.role}), 200


# ------------ ВЫХОД ПОЛЬЗОВАТЕЛЯ ------------

# Выход из системы — POST-запрос на /logout.
@auth_api.post("/logout")
@login_required  # Этот маршрут доступен только если пользователь уже залогинен.
def logout():
    # Вызываем logout_user(), чтобы удалить информацию о входе.
    logout_user()

    # Возвращаем простой JSON-ответ, что выход выполнен.
    return jsonify({"message": "logged out"}), 200
