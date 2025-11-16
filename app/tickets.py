from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from .extensions import db
from .models import Ticket

tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")

@tickets_bp.post("")
@login_required
def create_ticket():
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description", "")
    if not title:
        return jsonify({"message": "title required"}), 400
    t = Ticket(title=title, description=description, author_id=current_user.id)
    db.session.add(t)
    db.session.commit()
    return jsonify({"id": t.id, "status": t.status}), 201

@tickets_bp.get("")
@login_required
def list_tickets():
    query = Ticket.query if current_user.role == "admin" else Ticket.query.filter_by(author_id=current_user.id)
    items = [{
        "id": t.id, "title": t.title, "status": t.status,
        "author_id": t.author_id, "updated_at": (t.updated_at or t.created_at).isoformat()
    } for t in query.order_by(Ticket.updated_at.desc()).all()]
    return jsonify(items), 200

@tickets_bp.get("/<int:ticket_id>")
@login_required
def get_ticket(ticket_id: int):
    t = Ticket.query.get_or_404(ticket_id)
    if current_user.role != "admin" and t.author_id != current_user.id:
        abort(403)
    return jsonify({
        "id": t.id, "title": t.title, "description": t.description,
        "status": t.status, "author_id": t.author_id
    }), 200

@tickets_bp.put("/<int:ticket_id>")
@login_required
def update_ticket(ticket_id: int):
    t = Ticket.query.get_or_404(ticket_id)
    if current_user.role != "admin" and t.author_id != current_user.id:
        abort(403)
    data = request.get_json() or {}
    for field in ("title", "description", "status"):
        if field in data and data[field] is not None:
            setattr(t, field, data[field])
    db.session.commit()
    return jsonify({"message": "updated"}), 200

@tickets_bp.delete("/<int:ticket_id>")
@login_required
def delete_ticket(ticket_id: int):
    t = Ticket.query.get_or_404(ticket_id)
    if current_user.role != "admin" and t.author_id != current_user.id:
        abort(403)
    db.session.delete(t)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200
