# -------------------------------------------------------------
# Импортируем нужные элементы из Flask:
# - Blueprint — позволяет разделять проект на независимые модули.
#   То есть весь веб-интерфейс вынесен в отдельный "раздел".
# - render_template — функция, которая показывает HTML-файлы.
# - request — объект, через который мы получаем данные от пользователя
#   (например, логин, пароль или данные формы).
# - redirect — выполняет переадресацию на другую страницу.
# - url_for — генерирует правильные ссылки на страницы по имени функции.
# - flash — позволяет показывать пользователю всплывающее сообщение.
# - abort — позволяет прервать обработку и вернуть ошибку (например, 404).
# - jsonify — превращает данные в формат JSON (для возврата в API).
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify

# Импортируем механизмы логина:
# - login_user — выполняет вход пользователя в систему.
# - logout_user — выполняет выход.
# - login_required — защита маршрутов: если не вошёл — не пустит.
# - current_user — объект, содержащий текущего авторизованного пользователя.
from flask_login import login_user, logout_user, login_required, current_user

# Импортируем модели User и Ticket, чтобы работать с пользователями и заявками.
from .models import User, Ticket

# Импортируем базу данных и шифровщик паролей.
from .extensions import db, bcrypt


# -------------------------------------------------------------
# Создаём Blueprint — это как отдельный мини-приложение.
# Все маршруты будут иметь имя "web.<название функции>".
# Это помогает разделять API и обычные веб-страницы.
web_bp = Blueprint("web", __name__)


# =============================================================
#                     ГЛАВНАЯ СТРАНИЦА
# =============================================================

@web_bp.route("/", methods=["GET"])
def index():
    # current_user.is_authenticated — проверка:
    #  - True, если человек уже вошёл в систему.
    #  - False, если он гость.

    if current_user.is_authenticated:
        # Если пользователь вошёл — перенаправляем сразу к заявкам.
        return redirect(url_for("web.tickets"))

    # Если не вошёл — показываем страницу index.html.
    return render_template("index.html")


# =============================================================
#                     ВХОД В СИСТЕМУ (WEB)
# =============================================================

@web_bp.route("/web_login", methods=["GET", "POST"])
def web_login():
    # Если пользователь нажал кнопку "Войти",
    # значит, форма отправлена методом POST.
    if request.method == "POST":

        # request.form.get(...) — получает данные из HTML-формы.
        # "" — значение по умолчанию, если поле отсутствует.
        # .strip() — убирает пробелы слева и справа.
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Ищем пользователя в базе по имени.
        user = User.query.filter_by(username=username).first()

        # Если пользователь существует и пароль подходит:
        if user and user.check_password(password):
            # login_user — "залогинивает" пользователя.
            login_user(user)

            # Отправляем его к списку заявок.
            return redirect(url_for("web.tickets"))

        # Если логин или пароль неверный — показываем сообщение.
        flash("Неверный логин или пароль")

    # Если GET — просто показываем форму входа.
    return render_template("login.html")


# =============================================================
#                     ВЫХОД ИЗ СИСТЕМЫ
# =============================================================

@web_bp.route("/web_logout")
@login_required  # Защита: нельзя выйти, если не вошёл.
def web_logout():
    # logout_user — удаляет данные о авторизации.
    logout_user()

    # Перенаправляем на страницу входа.
    return redirect(url_for("web.web_login"))


# =============================================================
#                     РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ
# =============================================================

@web_bp.route("/web_register", methods=["GET", "POST"])
def web_register():

    # Если форма отправлена (POST):
    if request.method == "POST":

        # Забираем логин и пароль.
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Проверяем пустые поля.
        if not username or not password:
            flash("Заполните все поля")
            return redirect(url_for("web.web_register"))

        # Проверяем, существует ли пользователь с таким логином.
        if User.query.filter_by(username=username).first():
            flash("Пользователь уже существует")
            return redirect(url_for("web.web_register"))

        # Создаём нового пользователя.
        user = User(username=username)

        # Устанавливаем пароль (с хешированием).
        user.set_password(password)

        # Добавляем в базу данных.
        db.session.add(user)
        db.session.commit()

        # Сообщаем об успехе.
        flash("Регистрация успешна!")

        # Отправляем на страницу входа.
        return redirect(url_for("web.web_login"))

    # Если GET — показываем форму.
    return render_template("register.html")


# =============================================================
#                        СТРАНИЦА ЗАЯВОК
# =============================================================

@web_bp.route("/tickets", methods=["GET", "POST"])
@login_required  # Только авторизованные могут видеть заявки.
def tickets():

    # Если пользователь создаёт заявку:
    if request.method == "POST":
        # Получаем название и описание.
        title = request.form["title"].strip()
        description = request.form.get("description", "")

        # Название обязательно.
        if not title:
            flash("Название обязательно")
            return redirect(url_for("web.tickets"))

        # Создаём объект заявки.
        t = Ticket(
            title=title,
            description=description,
            author_id=current_user.id  # Текущий пользователь — автор.
        )

        # Сохраняем в базе.
        db.session.add(t)
        db.session.commit()

        flash("Заявка создана")
        return redirect(url_for("web.tickets"))

    # Если GET — показываем список заявок.
    # Администратор видит всё.
    # Обычный пользователь — только свои.
    query = Ticket.query if current_user.role == "admin" else Ticket.query.filter_by(author_id=current_user.id)

    # Получаем список, отсортированный по дате обновления (сначала новые).
    tickets = query.order_by(Ticket.updated_at.desc()).all()

    # Передаём список в HTML-шаблон.
    return render_template("tickets.html", tickets=tickets)


# =============================================================
#                   ПРОСМОТР ОДНОЙ ЗАЯВКИ
# =============================================================

@web_bp.route("/tickets/<int:ticket_id>", methods=["GET"])
@login_required
def ticket_detail(ticket_id):

    # Ищем заявку по ID.
    # Если нет — автоматически выдаст ошибку 404.
    t = Ticket.query.get_or_404(ticket_id)

    # Проверка доступа:
    #  - админ может смотреть всё
    #  - обычный пользователь — только свои
    if current_user.role != "admin" and t.author_id != current_user.id:
        flash("Нет доступа к этой заявке")
        return redirect(url_for("web.tickets"))

    # Показываем страницу заявки.
    return render_template("ticket_detail.html", t=t)


# =============================================================
#                ИЗМЕНЕНИЕ СТАТУСА ЗАЯВКИ
# =============================================================

@web_bp.route("/tickets/<int:ticket_id>/update", methods=["POST", "PUT"])
@login_required
def update_ticket(ticket_id):

    # Ищем заявку.
    t = Ticket.query.get_or_404(ticket_id)

    # Проверяем права.
    if t.author_id != current_user.id and current_user.role != "admin":
        flash("Нет прав для изменения этой заявки")
        return redirect(url_for("web.ticket_detail", ticket_id=t.id))

    # new_status будет:
    #  - из формы (если HTML)
    #  - из JSON (если обращается API)
    new_status = request.form.get("status") or (request.json.get("status") if request.is_json else None)

    # Если статус передали — обновляем.
    if new_status:
        t.status = new_status
        db.session.commit()
        flash(f"Статус заявки {t.title} обновлен")

    return redirect(url_for("web.ticket_detail", ticket_id=t.id))


# =============================================================
#                   УДАЛЕНИЕ ЗАЯВКИ
# =============================================================

@web_bp.route("/tickets/<int:ticket_id>/delete", methods=["POST", "DELETE"])
@login_required
def delete_ticket(ticket_id):

    # Ищем заявку.
    t = Ticket.query.get_or_404(ticket_id)

    # Проверяем доступ (как всегда).
    if t.author_id != current_user.id and current_user.role != "admin":
        flash("Нет прав для удаления заявки")
        return redirect(url_for("web.ticket_detail", ticket_id=t.id))

    # Удаляем.
    db.session.delete(t)
    db.session.commit()

    # Если это API-запрос (DELETE) — возвращаем JSON.
    if request.method == "DELETE":
        return jsonify({"message": "ticket deleted"}), 200

    # Иначе — HTML.
    flash(f"Заявка {t.title} была удалена")
    return redirect(url_for("web.tickets"))


# =============================================================
#                   СТРАНИЦА ВСЕХ ПОЛЬЗОВАТЕЛЕЙ (АДМИН)
# =============================================================

@web_bp.route("/users", methods=["GET"])
@login_required
def users():

    # Только администратор может смотреть всех пользователей.
    if current_user.role != "admin":
        flash("Нет доступа к этой странице")
        return redirect(url_for("web.index"))

    # Передаём список пользователей в шаблон users.html.
    return render_template("users.html", users=User.query.all())


# =============================================================
#                 ИЗМЕНЕНИЕ РОЛИ ПОЛЬЗОВАТЕЛЯ
# =============================================================

@web_bp.route("/users/<int:user_id>/update_role", methods=["POST", "PUT"])
@login_required
def update_user_role(user_id):

    # Проверка, что это админ.
    if current_user.role != "admin":
        flash("Нет доступа")
        return redirect(url_for("web.index"))

    # Получаем пользователя.
    user = User.query.get_or_404(user_id)

    # Роль может приходить как из формы, так и из JSON.
    new_role = request.form.get("role") or (request.json.get("role") if request.is_json else None)

    # Проверяем корректность роли.
    if new_role not in ["user", "admin"]:
        flash("Некорректная роль")
        return redirect(url_for("web.users"))

    # Обновляем роль.
    user.role = new_role
    db.session.commit()

    # Если PUT — это API, возвращаем JSON.
    if request.method == "PUT":
        return jsonify({"message": "role updated"}), 200

    # Иначе HTML-ответ.
    flash(f"Роль пользователя {user.username} обновлена")
    return redirect(url_for("web.users"))


# =============================================================
#                   УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ (АДМИН)
# =============================================================

@web_bp.route("/users/<int:user_id>/delete", methods=["POST", "DELETE"])
@login_required
def delete_user(user_id):

    if current_user.role != "admin":
        flash("Нет доступа")
        return redirect(url_for("web.users"))

    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    if request.method == "DELETE":
        return jsonify({"message": "user deleted"}), 200

    flash(f"Пользователь {user.username} был удален")
    return redirect(url_for("web.users"))


# =============================================================
#                   РЕДАКТИРОВАНИЕ ЗАЯВКИ
# =============================================================

@web_bp.route("/tickets/<int:ticket_id>/edit", methods=["GET", "POST"])
@login_required
def edit_ticket(ticket_id):

    # Ищем заявку.
    t = Ticket.query.get_or_404(ticket_id)

    # Проверяем, что либо:
    #  - автор,
    #  - либо администратор.
    if current_user.role != "admin" and t.author_id != current_user.id:
        flash("Нет прав для изменения заявки")
        return redirect(url_for("web.ticket_detail", ticket_id=t.id))

    # Если форма была отправлена:
    if request.method == "POST":

        # Получаем данные.
        title = request.form["title"].strip()
        description = request.form["description"].strip()

        # Обновляем поля.
        t.title = title or t.title
        t.description = description or t.description

        # Сохраняем.
        db.session.commit()

        flash("Заявка обновлена")
        return redirect(url_for("web.ticket_detail", ticket_id=t.id))

    # Если GET — показываем форму редактирования.
    return render_template("edit_ticket.html", ticket=t)
