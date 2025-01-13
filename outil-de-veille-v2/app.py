from app import app, db
from app.services.init_db import InitDB

with app.app_context():
    db.create_all()
    InitDB()  # Initialiser les données si nécessaire

if __name__ == '__main__':
    app.run(port=55555, debug=False)