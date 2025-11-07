from app import create_app, db
from app.models import *  # <-- IMPORTANTE

app = create_app()

with app.app_context():
    db.drop_all()       # Limpia todo antes
    db.create_all()     # Crea todas las tablas
    print("✅ Base de datos y tablas creadas.")
