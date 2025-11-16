from flask import Flask
from .config import Config
from .extensions import db, login_manager, bcrypt
from .models import User
from .auth import auth_bp
from .tickets import tickets_bp
from .admin import admin_bp
from .web import web_bp

def create_app(testing: bool = False):
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    if testing:
        app.config.update(
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            TESTING=True,
            SECRET_KEY="test-secret",
            WTF_CSRF_ENABLED=False,
            LOGIN_DISABLED=False,
        )

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Регистрируем все модули (Blueprint'ы)
    app.register_blueprint(web_bp)      # веб-страницы (HTML)
    app.register_blueprint(auth_bp)     # /register, /login (REST)
    app.register_blueprint(tickets_bp)  # /tickets* (REST)
    app.register_blueprint(admin_bp)    # /users* (REST)


    with app.app_context():
        db.create_all()

    return app

# Эта строка просто подавляет предупреждение IDE
app = None  # type: ignore
