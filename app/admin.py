from flask import Blueprint, jsonify, request
from flask_login import login_required
from .extensions import db
from .models import User
from .rbac import admin_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.get("/users")
@login_required
@admin_required
def list_users():
    users = [{"id": u.id, "username": u.username, "role": u.role} for u in User.query.order_by(User.id).all()]
    return jsonify(users), 200

@admin_bp.put("/users/<int:user_id>")
@login_required
@admin_required
def update_user_role(user_id: int):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    role = data.get("role")
    if role not in ("user", "admin"):
        return jsonify({"message": "role must be 'user' or 'admin'"}), 400
    user.role = role
    db.session.commit()
    return jsonify({"message": "role updated", "id": user.id, "role": user.role}), 200
