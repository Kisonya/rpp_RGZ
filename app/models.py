# Импортируем класс datetime, чтобы хранить дату и время создания/обновления заявок.
from datetime import datetime

# UserMixin — вспомогательный класс от Flask-Login.
# Он добавляет в модель пользователя стандартные методы и свойства:
# is_authenticated, is_active, get_id() и т.п.
from flask_login import UserMixin

# Импортируем уже созданные в extensions объекты db (база) и bcrypt (хеширование паролей).
from .extensions import db, bcrypt


# Класс User описывает таблицу "user" в базе данных.
# Каждый объект этого класса — одна строка в таблице "user".
class User(UserMixin, db.Model):
    # Уникальный идентификатор пользователя (целое число, первичный ключ).
    id = db.Column(db.Integer, primary_key=True)

    # Логин пользователя: строка до 80 символов, должен быть уникальным и не может быть пустым.
    username = db.Column(db.String(80), unique=True, nullable=False)

    # Хеш пароля: здесь хранится НЕ сам пароль, а его "зашифрованная" версия.
    # Длина строки до 128 символов, поле обязательное.
    password_hash = db.Column(db.String(128), nullable=False)

    # Роль пользователя: обычный пользователь ("user") или администратор ("admin").
    # По умолчанию — "user". Поле обязательно.
    role = db.Column(db.String(20), default="user", nullable=False)  # 'user' | 'admin'

    # Метод для установки пароля.
    # На вход принимает обычный текстовый пароль (str).
    def set_password(self, password: str):
        # bcrypt.generate_password_hash(password) — создаёт хеш пароля (байты).
        # .decode("utf-8") — переводит байты в строку для удобного хранения в базе.
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    # Метод для проверки пароля при входе.
    # Возвращает True, если введённый пароль совпадает с хешем в базе, иначе False.
    def check_password(self, password: str) -> bool:
        # bcrypt.check_password_hash сравнивает хеш из базы и введённый пароль.
        return bcrypt.check_password_hash(self.password_hash, password)


# Класс Ticket описывает таблицу "ticket" — это "заявка в техподдержку".
class Ticket(db.Model):
    # Уникальный идентификатор заявки.
    id = db.Column(db.Integer, primary_key=True)

    # Краткое название заявки. Обязательно для заполнения.
    title = db.Column(db.String(200), nullable=False)

    # Подробное описание проблемы. Может быть пустым (nullable=True).
    description = db.Column(db.Text, nullable=True)

    # Статус заявки: "open" (открыта), "in-progress" (в работе), "closed" (закрыта).
    # По умолчанию — "open". Поле обязательно.
    status = db.Column(db.String(30), default="open", nullable=False)  # open|in_progress|closed

    # Дата и время создания заявки.
    # default=datetime.utcnow — автоматически берётся текущее время (по UTC) при создании записи.
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Дата и время последнего обновления заявки.
    # default=datetime.utcnow — стартовое значение при создании.
    # onupdate=datetime.utcnow — при каждом изменении записи поле обновляется на текущее время.
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Внешний ключ на пользователя (автора заявки).
    # В таблице ticket будет колонка author_id, которая "ссылается" на user.id.
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Связь с моделью User.
    # Позволяет из заявки обратиться к пользователю: t.author.username.
    # backref создаёт обратную связь: из пользователя можно обратиться к его заявкам: user.tickets.
    author = db.relationship(
        "User",
        backref=db.backref("tickets", lazy=True),
    )
