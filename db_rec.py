from app import app, db
with app.app_context():
    db.drop_all()  # Drops all tables
    db.create_all()