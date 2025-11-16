from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User

admin_api = Blueprint("admin_api", __name__)


@admin_api.get("/users")
@login_required
def list_users():
    if current_user.role != "admin":
        abort(403)

    return jsonify([
        {"id": u.id, "username": u.username, "role": u.role}
        for u in User.query.all()
    ]), 200


@admin_api.put("/users/<int:user_id>")
@login_required
def update_role(user_id):
    if current_user.role != "admin":
        abort(403)

    data = request.get_json() or {}
    new_role = data.get("role")

    if new_role not in ("user", "admin"):
        return jsonify({"error": "bad role"}), 400

    user = User.query.get_or_404(user_id)
    user.role = new_role
    db.session.commit()

    return jsonify({"id": user.id, "role": user.role}), 200
