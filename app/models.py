from datetime import datetime, time
from sqlalchemy import (
    Column, Integer, String, Text, Date, Time, Float, Boolean, Enum, ForeignKey
)
from datetime import date
from sqlalchemy.orm import relationship
from . import db


class Cliente(db.Model):
    __tablename__ = 'cliente'

    id = Column(Integer, primary_key=True)
    dni = Column(String, unique=True, nullable=True)
    nombre = Column(String, nullable=True)
    apellido = Column(String, nullable=True)
    documento_tipo = Column(String, nullable=True)
    observaciones = Column(Text, nullable=True)
    telefono = Column(String, nullable=True)   # ← nuevo campo
    correo = Column(String, nullable=True)     # ← nuevo campo
    reservas = relationship("Reserva", back_populates="cliente")

class Usuario(db.Model):
    __tablename__ = 'usuario'

    id = Column(Integer, primary_key=True)
    dni = Column(String(8), unique=True, nullable=False)
    nombres = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)
    contrasena_hash = Column(String, nullable=False)
    rol = Column(Enum('admin', 'barbero', name='rol_enum'), nullable=False)
    nickname = Column(String, nullable=False)
    telefono = Column(String)
    especialidad = Column(String)
    foto_url = Column(String)
    servicios = relationship("ReservaServicio", back_populates="barbero")

class Servicio(db.Model):
    __tablename__ = 'servicio'

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    precio_base = Column(Float, nullable=False)
    duracion_minutos = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)

    reservas_servicio = relationship("ReservaServicio", back_populates="servicio")

class Reserva(db.Model):
    __tablename__ = 'reserva'

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('cliente.id'), nullable=True)
    fecha_reserva = Column(Date, nullable=False)
    hora_reserva = Column(Time, nullable=False)
    estado_pago = Column(Enum('no_pagado', 'parcial', 'pagado', name='estado_pago_enum'), nullable=False, default='no_pagado')
    metodo_pago = Column(Enum('yape', 'plin', 'efectivo', 'otro', name='metodo_pago_enum'), nullable=True)
    total = Column(Float, nullable=False, default=0.0)
    descuento = Column(Float, nullable=True)
    comentario_general = Column(Text, nullable=True)

    cliente = relationship("Cliente", back_populates="reservas")
    servicios_detalle = relationship("ReservaServicio", back_populates="reserva")

class ReservaServicio(db.Model):
    __tablename__ = 'reserva_servicio'

    id = Column(Integer, primary_key=True)
    reserva_id = Column(Integer, ForeignKey('reserva.id'), nullable=False)
    servicio_id = Column(Integer, ForeignKey('servicio.id'), nullable=False)
    barbero_id = Column(Integer, ForeignKey('usuario.id'), nullable=False)
    precio_final = Column(Float, nullable=False)
    estado_servicio = Column(Enum('en_espera','pendiente', 'en_proceso', 'terminado', 'cancelado', name='estado_servicio_enum'), nullable=False, default='pendiente')
    hora_inicio_estimada = Column(Time, nullable=False)
    persona_atendida = Column(String, nullable=True)
    comentario = db.Column(db.Text) 
    porcentaje_barbero = Column(Float, nullable=False, default=0.5)  # 50% por defecto
    reserva = relationship("Reserva", back_populates="servicios_detalle")
    servicio = relationship("Servicio", back_populates="reservas_servicio")
    barbero = relationship("Usuario", back_populates="servicios")


class GastoExtra(db.Model):
    __tablename__ = 'gasto_extra'

    id = Column(Integer, primary_key=True)
    fecha = Column(Date, nullable=False, default=date.today)
    hora = Column(Time, nullable=False, default=lambda: datetime.now().time()) 
    monto = Column(Float, nullable=False)
    motivo = Column(String, nullable=False)
    observacion = Column(Text)

    # usuario que registra el gasto (ej: la recepcionista)
    usuario_id = Column(Integer, ForeignKey('usuario.id'))
    usuario = relationship("Usuario", backref="gastos_extra", foreign_keys=[usuario_id])

    # barbero al que se le asigna el gasto (si aplica)
    barbero_id = Column(Integer, ForeignKey('usuario.id'), nullable=True)
    barbero = relationship("Usuario", backref="egresos_asignados", foreign_keys=[barbero_id])

    reporte_id = Column(Integer, ForeignKey('reporte_diario.id'), nullable=True)




class PagoBarbero(db.Model):
    __tablename__ = 'pago_barbero'

    id = Column(Integer, primary_key=True)
    barbero_id = Column(Integer, ForeignKey('usuario.id'), nullable=False)
    fecha = Column(Date, nullable=False, default=date.today)

    total_servicios = Column(Float, default=0.0)   # suma precio_final del día
    total_ganado = Column(Float, default=0.0)      # total_servicios * porcentaje_ganancia
    total_descuentos = Column(Float, default=0.0)  # descuentos asignados desde GastoExtra
    total_final = Column(Float, default=0.0)       # ganado - descuentos + extras (si aplica)
    barbero = relationship("Usuario", backref="cierres_diarios")
    reporte_id = Column(Integer, ForeignKey('reporte_diario.id'), nullable=True)




class ReporteDiario(db.Model):
    __tablename__ = 'reporte_diario'

    id = Column(Integer, primary_key=True)
    fecha = Column(Date, nullable=False, unique=True)

    ingresos_total = Column(Float, default=0.0)
    egresos_total = Column(Float, default=0.0)
    ganancia_neta = Column(Float, default=0.0)
    porcentaje_ganancia = Column(Float, default=0.0)

    total_yape = Column(Float, default=0.0)
    total_plin = Column(Float, default=0.0)
    total_efectivo = Column(Float, default=0.0)
    total_otro = Column(Float, default=0.0)

    servicios_realizados = Column(Integer, default=0)
    servicios_cancelados = Column(Integer, default=0)
    servicios_totales = Column(Integer, default=0)

    # Relación opcional
    pagos_barberos = relationship("PagoBarbero", backref="reporte", lazy=True)
    gastos = relationship("GastoExtra", backref="reporte", lazy=True)


class MovimientoPago(db.Model):
    __tablename__ = 'movimiento_pago'

    id = Column(Integer, primary_key=True)
    pago_id = Column(Integer, ForeignKey('pago_barbero.id'), nullable=False)
    tipo = Column(Enum('servicio', 'descuento', 'bono', 'adelanto', name='tipo_movimiento_enum'), nullable=False)
    monto = Column(Float, nullable=False)
    descripcion = Column(String, nullable=True)

    pago = relationship("PagoBarbero", backref="movimientos")

