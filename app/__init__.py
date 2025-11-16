import os
from flask import Flask, jsonify
from .extensions import db, bcrypt, login_manager
from .models import User


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__)

    # Конфиг
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "test-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///:memory:" if testing else "sqlite:///data.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Расширения
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Flask-Login: без редиректов на /login для API
    login_manager.login_view = None
    login_manager.session_protection = None

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        # Для API-тестов
        return jsonify({"error": "unauthorized"}), 401

    # === Режим тестов: только JSON-API ===
    if testing:
        from .api.auth_api import auth_api
        from .api.tickets_api import tickets_api
        from .api.admin_api import admin_api

        app.register_blueprint(auth_api)
        app.register_blueprint(tickets_api)
        app.register_blueprint(admin_api)

    # === Обычный режим: только веб-интерфейс ===
    else:
        from .web import web_bp
        app.register_blueprint(web_bp)

    return app
