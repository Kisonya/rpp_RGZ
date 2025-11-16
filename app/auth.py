from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required
from .extensions import db
from .models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/")

@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"message": "username and password required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "username already taken"}), 409
    user = User(username=username, role="user")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id, "username": user.username, "role": user.role}), 201

@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "invalid credentials"}), 401
    login_user(user)
    return jsonify({"message": "logged in", "username": user.username, "role": user.role}), 200

@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"message": "logged out"}), 200
