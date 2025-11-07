import sys
import os
from datetime import datetime, timedelta

# -------------------------------
# 1️⃣ Configurar path relativo
# -------------------------------
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_PATH)
os.chdir(PROJECT_PATH)

# -------------------------------
# 2️⃣ Importar app y modelos desde la carpeta app
# -------------------------------
from run import create_app
from app.models import db, Reserva, ReservaServicio

# -------------------------------
# 3️⃣ Inicializar app y contexto
# -------------------------------
app = create_app()
app.app_context().push()

# -------------------------------
# 4️⃣ Función para actualizar estados
# -------------------------------
def actualizar_estados_servicios():
    ahora = datetime.now()
    servicios = ReservaServicio.query.join(Reserva).all()

    for s in servicios:
        if s.estado_servicio in ['terminado', 'cancelado']:
            continue

        # Combinar fecha + hora para obtener un datetime completo
        hora_inicio = datetime.combine(s.reserva.fecha_reserva, s.hora_inicio_estimada)
        hora_fin = hora_inicio + timedelta(minutes=s.servicio.duracion_minutos)


        if s.estado_servicio == 'en_espera' and hora_inicio <= ahora < hora_fin:
            s.estado_servicio = 'en_proceso'
        elif s.estado_servicio != 'terminado' and ahora >= hora_fin:
            s.estado_servicio = 'terminado'

    db.session.commit()
    print(f"[{ahora.strftime('%Y-%m-%d %H:%M:%S')}] Estados actualizados correctamente.")

# -------------------------------
# 5️⃣ Ejecutar si se llama directamente
# -------------------------------
if __name__ == "__main__":
    actualizar_estados_servicios()
