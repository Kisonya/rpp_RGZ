# Импортируем нужные инструменты Flask
from flask import Blueprint, request, jsonify

# Импортируем login_required и current_user:
# - login_required — не пускает неавторизованных пользователей
# - current_user — объект, который хранит данные о вошедшем пользователе
from flask_login import login_required, current_user

# Импортируем доступ к базе данных
from app.extensions import db

# Импортируем модель Ticket — таблица заявок
from app.models import Ticket

# Создаём Blueprint для работы с заявками
tickets_api = Blueprint("tickets_api", __name__)


# ============================================================
# 1. СОЗДАНИЕ НОВОЙ ЗАЯВКИ
# ============================================================

@tickets_api.post("/tickets")  # POST — создать новый объект
@login_required                 # Только авторизованный пользователь может создать заявку
def create_ticket():
    # Получаем JSON из запроса. Если данных нет — подставляем пустой словарь.
    data = request.get_json() or {}

    # Получаем и очищаем (strip) поля title и description.
    # data.get("title") — достаём значение по ключу (если его нет — None).
    # ( ... or "" ) — если нет значения, подставить пустую строку.
    # .strip() — удалить пробелы в начале и конце.
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()

    # Название — обязательное поле. Если его нет — ошибка.
    if not title:
        return jsonify({"error": "title required"}), 400

    # Создаём новый объект таблицы Ticket
    # author_id=current_user.id — заявка принадлежит пользователю, который вошёл в систему
    t = Ticket(title=title, description=description, author_id=current_user.id)

    # Добавляем объект в базу (пока без сохранения)
    db.session.add(t)

    # Окончательно сохраняем
    db.session.commit()

    # Возвращаем id созданной заявки и её статус (например, "open")
    return jsonify({"id": t.id, "status": t.status}), 201  # 201 — объект создан


# ============================================================
# 2. СПИСОК ВСЕХ ЗАЯВОК
# ============================================================

@tickets_api.get("/tickets")
@login_required
def list_tickets():
    # Администратор видит все заявки
    if current_user.role == "admin":
        query = Ticket.query
    else:
        # Обычный пользователь — только свои
        query = Ticket.query.filter_by(author_id=current_user.id)

    # Собираем заявки в список словарей
    items = []
    for t in query.order_by(Ticket.updated_at.desc()).all():
        items.append(
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "author_id": t.author_id,
            }
        )

    return jsonify(items), 200


# ============================================================
# 3. ПОЛУЧЕНИЕ ДЕТАЛЕЙ КОНКРЕТНОЙ ЗАЯВКИ
# ============================================================

@tickets_api.get("/tickets/<int:ticket_id>")
@login_required
def get_ticket(ticket_id: int):
    # Получаем заявку по ID или выдаём 404, если её нет
    t = Ticket.query.get_or_404(ticket_id)

    # Если пользователь НЕ администратор и заявка НЕ его, значит ему нельзя её видеть
    if current_user.role != "admin" and t.author_id != current_user.id:
        return jsonify({"error": "forbidden"}), 403

    # Возвращаем данные заявки
    return jsonify(
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "author_id": t.author_id,
        }
    ), 200


# ============================================================
# 4. РЕДАКТИРОВАНИЕ ЗАЯВКИ
# ============================================================

@tickets_api.put("/tickets/<int:ticket_id>")
@login_required
def update_ticket_api(ticket_id: int):
    # Получаем заявку
    t = Ticket.query.get_or_404(ticket_id)

    # Проверка доступа: админ или автор заявки
    if current_user.role != "admin" and t.author_id != current_user.id:
        return jsonify({"error": "forbidden"}), 403

    # Получаем JSON с изменениями
    data = request.get_json() or {}

    # Изменяем только те поля, которые клиент действительно отправил
    for field in ("title", "description", "status"):
        if field in data and data[field] is not None:
            setattr(t, field, data[field])  # setattr — записывает значение в атрибут объекта

    db.session.commit()

    return jsonify({"message": "updated"}), 200


# ============================================================
# 5. УДАЛЕНИЕ ЗАЯВКИ
# ============================================================

@tickets_api.delete("/tickets/<int:ticket_id>")
@login_required
def delete_ticket_api(ticket_id: int):
    # Ищем заявку
    t = Ticket.query.get_or_404(ticket_id)

    # Проверка доступа
    if current_user.role != "admin" and t.author_id != current_user.id:
        return jsonify({"error": "forbidden"}), 403

    # Удаляем запись
    db.session.delete(t)
    db.session.commit()

    return jsonify({"message": "deleted"}), 200
