from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Ticket
from .extensions import db, bcrypt

web_bp = Blueprint("web", __name__)

# Главная страница
@web_bp.route("/", methods=["GET"])
def index():
    if current_user.is_authenticated:
        return redirect(url_for("web.tickets"))
    return render_template("index.html")

# Страница логина (ОСТАВЛЯЕМ ЭТУ)
@web_bp.route("/login", methods=["GET", "POST"])
def web_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("web.tickets"))
        flash("Неверные имя пользователя или пароль")
    return render_template("login.html")

# Выход (ОСТАВЛЯЕМ ЭТУ)
@web_bp.route("/logout")
@login_required
def web_logout():
    logout_user()
    return redirect(url_for("web.index"))

# Создание и просмотр всех заявок
@web_bp.route("/tickets", methods=["GET", "POST"])
@login_required
def tickets():
    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form.get("description", "")
        if not title:
            flash("Название обязательно")
            return redirect(url_for("web.tickets"))
        t = Ticket(title=title, description=description, author_id=current_user.id)
        db.session.add(t)
        db.session.commit()
        flash("Заявка создана")
        return redirect(url_for("web.tickets"))

    query = Ticket.query if current_user.role == "admin" else Ticket.query.filter_by(author_id=current_user.id)
    tickets = query.order_by(Ticket.updated_at.desc()).all()
    return render_template("tickets.html", tickets=tickets)

# Просмотр конкретной заявки
@web_bp.route("/tickets/<int:ticket_id>", methods=["GET"])
@login_required
def ticket_detail(ticket_id):
    t = Ticket.query.get_or_404(ticket_id)
    if current_user.role != "admin" and t.author_id != current_user.id:
        flash("Нет доступа к этой заявке")
        return redirect(url_for("web.tickets"))
    return render_template("ticket_detail.html", t=t)

# Обновление статуса заявки
@web_bp.route("/tickets/<int:ticket_id>/update", methods=["POST", "PUT"])
@login_required
def update_ticket(ticket_id):
    t = Ticket.query.get_or_404(ticket_id)

    if t.author_id != current_user.id and current_user.role != "admin":
        flash("Нет прав для изменения этой заявки")
        return redirect(url_for("web.ticket_detail", ticket_id=t.id))

    new_status = request.form.get("status") or (request.json.get("status") if request.is_json else None)

    if new_status:
        t.status = new_status
        db.session.commit()
        flash(f"Статус заявки {t.title} обновлен")
    
    return redirect(url_for("web.ticket_detail", ticket_id=t.id))

# Удаление заявки
@web_bp.route("/tickets/<int:ticket_id>/delete", methods=["POST", "DELETE"])
@login_required
def delete_ticket(ticket_id):
    t = Ticket.query.get_or_404(ticket_id)

    if t.author_id != current_user.id and current_user.role != "admin":
        flash("Нет прав для удаления заявки")
        return redirect(url_for("web.ticket_detail", ticket_id=t.id))

    db.session.delete(t)
    db.session.commit()

    if request.method == "DELETE":
        return jsonify({"message": "ticket deleted"}), 200

    flash(f"Заявка {t.title} была удалена")
    return redirect(url_for("web.tickets"))

# Страница пользователей
@web_bp.route("/users", methods=["GET"])
@login_required
def users():
    if current_user.role != "admin":
        flash("Нет доступа к этой странице")
        return redirect(url_for("web.index"))
    return render_template("users.html", users=User.query.all())

# Обновление роли
@web_bp.route("/users/<int:user_id>/update_role", methods=["POST", "PUT"])
@login_required
def update_user_role(user_id):
    if current_user.role != "admin":
        flash("Нет доступа")
        return redirect(url_for("web.index"))

    user = User.query.get_or_404(user_id)

    new_role = request.form.get("role") or (request.json.get("role") if request.is_json else None)

    if new_role not in ["user", "admin"]:
        flash("Некорректная роль")
        return redirect(url_for("web.users"))

    user.role = new_role
    db.session.commit()

    if request.method == "PUT":
        return jsonify({"message": "role updated"}), 200

    flash(f"Роль пользователя {user.username} обновлена")
    return redirect(url_for("web.users"))

# Удаление пользователя
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

# Редактирование заявки
@web_bp.route("/tickets/<int:ticket_id>/edit", methods=["GET", "POST"])
@login_required
def edit_ticket(ticket_id):
    t = Ticket.query.get_or_404(ticket_id)

    if current_user.role != "admin" and t.author_id != current_user.id:
        flash("Нет прав для изменения заявки")
        return redirect(url_for("web.ticket_detail", ticket_id=t.id))

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form["description"].strip()

        t.title = title or t.title
        t.description = description or t.description
        db.session.commit()

        flash("Заявка обновлена")
        return redirect(url_for("web.ticket_detail", ticket_id=t.id))

    return render_template("edit_ticket.html", ticket=t)

# 🆕 Регистрация (оставляем)
@web_bp.route("/register", methods=["GET", "POST"])
def web_register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Заполните все поля")
            return redirect(url_for("web.web_register"))

        if User.query.filter_by(username=username).first():
            flash("Пользователь уже существует")
            return redirect(url_for("web.web_register"))

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Регистрация успешна!")
        return redirect(url_for("web.web_login"))

    return render_template("register.html")
