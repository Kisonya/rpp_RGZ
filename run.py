from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    db.create_all()

    # ---- Создаем администратора, если его нет ----
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(username="admin", role="admin")
        admin.set_password("adminpass")
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin / adminpass")
    else:
        print("Admin already exists")

if __name__ == "__main__":
    app.run(debug=True)
