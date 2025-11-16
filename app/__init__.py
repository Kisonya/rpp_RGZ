from flask import Flask
from .extensions import db, bcrypt, login_manager
from .models import User, Ticket


def create_app(testing=False):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:" if testing else "sqlite:///data.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Init
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Flask-Login → НЕ ДЕЛАТЬ РЕДИРЕКТЫ НА /login
    login_manager.login_view = None
    login_manager.session_protection = None

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return {"error": "unauthorized"}, 401

    # --- API ---
    from app.api.auth_api import auth_api
    from app.api.tickets_api import tickets_api
    from app.api.admin_api import admin_api

    app.register_blueprint(auth_api)
    app.register_blueprint(tickets_api)
    app.register_blueprint(admin_api)

    # --- WEB ---
    from .web import web_bp
    app.register_blueprint(web_bp)

    return app
