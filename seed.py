from app import create_app, db
from app.models import Servicio

app = create_app()

with app.app_context():
    s1 = Servicio(nombre="Corte clásico", descripcion="Corte tradicional", precio_base=20.0, duracion_minutos=30, activo=True)
    s2 = Servicio(nombre="Barba", descripcion="Afeitado y forma", precio_base=15.0, duracion_minutos=20, activo=True)
    s3 = Servicio(nombre="Diseño", descripcion="Líneas y dibujos", precio_base=25.0, duracion_minutos=40, activo=True)

    db.session.add_all([s1, s2, s3])
    db.session.commit()
    print("Servicios insertados correctamente.")
