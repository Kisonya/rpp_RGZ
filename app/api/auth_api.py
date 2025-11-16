from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user
from app.extensions import db, bcrypt
from app.models import User

auth_api = Blueprint("auth_api", __name__, url_prefix="/api/auth")


@auth_api.post("/register")
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "user exists"}), 400

    u = User(username=username, role="user")
    u.set_password(password)
    db.session.add(u)
    db.session.commit()

    return jsonify({"message": "registered"}), 201


@auth_api.post("/login")
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "invalid credentials"}), 400

    login_user(user)
    return jsonify({"message": "logged in", "role": user.role}), 200


@auth_api.post("/logout")
def logout():
    logout_user()
    return jsonify({"message": "logged out"}), 200
