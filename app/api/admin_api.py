# Импортируем инструменты из Flask:
# Blueprint — позволяет создавать отдельные "разделы" API.
# request — содержит данные, которые прислал клиент.
# jsonify — превращает данные Python в JSON для ответа.
from flask import Blueprint, request, jsonify

# Импортируем инструменты Flask-Login:
# login_required — не пускает на маршрут, если пользователь не авторизован.
# current_user — объект, который хранит информацию о том, кто сейчас вошёл в систему.
from flask_login import login_required, current_user

# Подключаем объект базы данных, чтобы читать и изменять записи в таблицах
from app.extensions import db

# Импортируем модель User — класс, который соответствует таблице пользователей
from app.models import User

# Создаём новый API-раздел (Blueprint) под названием "admin_api".
# Это отдельный логический модуль для маршрутов администратора.
admin_api = Blueprint("admin_api", __name__)


# ============================================================
# 1. Маршрут: ПОЛУЧЕНИЕ СПИСКА ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================

# @admin_api.get("/users") означает:
# "Когда приходит GET-запрос по адресу /users, вызывай эту функцию".
@admin_api.get("/users")
@login_required  # Этот маршрут закрыт — его может вызвать только авторизованный пользователь
def list_users():
    # Проверяем: является ли текущий пользователь администратором?
    # Если его роль не 'admin', то он не имеет прав видеть список всех пользователей.
    if current_user.role != "admin":
        return jsonify({"error": "forbidden"}), 403  # 403 означает "Доступ запрещён"

    # Если администратор — получаем всех пользователей из базы
    # User.query.all() — выбирает *все строки* из таблицы User
    # Далее в цикле формируем список словарей (id, имя, роль)
    users = [
        {"id": u.id, "username": u.username, "role": u.role}
        for u in User.query.all()
    ]

    # Возвращаем список пользователей в формате JSON
    return jsonify(users), 200  # 200 — успешный код ответа


# ============================================================
# 2. Маршрут: ИЗМЕНЕНИЕ РОЛИ ПОЛЬЗОВАТЕЛЯ
# ============================================================

# @admin_api.put("/users/<int:user_id>"):
# <int:user_id> — означает, что часть адреса — это число.
# Например: PUT /users/5 — изменить пользователя с ID=5.
@admin_api.put("/users/<int:user_id>")
@login_required
def update_user_role_api(user_id: int):

    # Проверяем, что текущий пользователь — администратор.
    if current_user.role != "admin":
        return jsonify({"error": "forbidden"}), 403

    # Ищем пользователя в базе по ID.
    # get_or_404 выдаёт ошибку 404, если пользователь не найден.
    user = User.query.get_or_404(user_id)

    # Получаем JSON-данные из запроса.
    # Если данных нет, то подставляем пустой словарь.
    data = request.get_json() or {}

    # Берём новое значение роли, которое указал клиент.
    new_role = data.get("role")

    # Проверяем, корректно ли указана роль.
    # Допускаются только "admin" и "user".
    if new_role not in ("user", "admin"):
        return jsonify({"error": "invalid role"}), 400

    # Записываем новую роль пользователю
    user.role = new_role

    # Сохраняем изменения в базе данных
    db.session.commit()

    # Возвращаем обновлённые данные пользователя
    return jsonify(
        {"id": user.id, "username": user.username, "role": user.role}
    ), 200
