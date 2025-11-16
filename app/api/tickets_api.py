from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Ticket

tickets_api = Blueprint("tickets_api", __name__, url_prefix="/api/tickets")



@tickets_api.post("")
@login_required
def create_ticket():
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description", "")

    if not title:
        return jsonify({"error": "title required"}), 400

    t = Ticket(title=title, description=description, author_id=current_user.id)
    db.session.add(t)
    db.session.commit()

    return jsonify({"id": t.id, "status": t.status}), 201


@tickets_api.get("")
@login_required
def list_tickets():
    query = Ticket.query if current_user.role == "admin" else Ticket.query.filter_by(author_id=current_user.id)
    items = [
        {"id": t.id, "title": t.title, "status": t.status}
        for t in query.all()
    ]
    return jsonify(items), 200


@tickets_api.get("/<int:ticket_id>")
@login_required
def get_ticket(ticket_id):
    t = Ticket.query.get_or_404(ticket_id)
    if current_user.role != "admin" and t.author_id != current_user.id:
        abort(403)
    return jsonify({"id": t.id, "title": t.title, "description": t.description}), 200


@tickets_api.put("/<int:ticket_id>")
@login_required
def update_ticket(ticket_id):
    t = Ticket.query.get_or_404(ticket_id)
    if current_user.role != "admin" and t.author_id != current_user.id:
        abort(403)

    data = request.get_json() or {}
    for f in ("title", "description", "status"):
        if f in data:
            setattr(t, f, data[f])

    db.session.commit()
    return jsonify({"message": "updated"}), 200


@tickets_api.delete("/<int:ticket_id>")
@login_required
def delete_ticket(ticket_id):
    t = Ticket.query.get_or_404(ticket_id)
    if current_user.role != "admin" and t.author_id != current_user.id:
        abort(403)

    db.session.delete(t)
    db.session.commit()

    return jsonify({"message": "deleted"}), 200
