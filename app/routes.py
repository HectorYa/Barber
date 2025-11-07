from flask import Blueprint, render_template, request, redirect, url_for
from flask import current_app
from . import db
from .models import Servicio
from .models import Usuario
import os
from werkzeug.utils import secure_filename
from flask import current_app
from .models import Cliente, Usuario, Servicio, Reserva, ReservaServicio, PagoBarbero
from datetime import date, datetime
from datetime import datetime, timedelta, date
from flask import jsonify
from math import ceil
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from flask import flash
from .models import db, GastoExtra, Usuario, ReporteDiario
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps

main = Blueprint('main', __name__)  




#LOGIN

from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

# @main.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         email = request.form["email"]
#         contrasena = request.form["contrasena"]

#         usuario = Usuario.query.filter_by(email=email).first()
#         if usuario and check_password_hash(usuario.contrasena_hash, contrasena):
#             session['usuario_id'] = usuario.id
#             session['rol'] = usuario.rol
#             # Redirige según rol
#             if usuario.rol == 'barbero':
#                 return redirect(url_for('main.perfil_barbero', barbero_id=usuario.id))
#             else:
#                 return redirect(url_for('main.dashboard_admin'))
#         else:
#             flash("Credenciales incorrectas", "danger")
#     return render_template("login.html")


# @main.route("/logout")
# def logout():
#     session.clear()
#     return redirect(url_for('main.login'))


from functools import wraps
from flask import session, redirect, url_for, flash


# Ruta de LOGIN
@main.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.inicio'))
    
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        
        print(f"📧 Correo recibido: '{correo}'")
        print(f"🔑 Contraseña recibida: '{contrasena}'")
        
        # Probar obtener TODOS los usuarios
        todos = Usuario.query.all()
        print(f"📊 Total usuarios en BD: {len(todos)}")
        for u in todos:
            print(f"   - {u.id}: {u.correo} | {u.contrasena_hash} | {u.rol}")
        
        # Intentar buscar el usuario
        usuario = Usuario.query.filter_by(correo=correo).first()
        
        print(f"👤 Usuario encontrado: {usuario}")
        if usuario:
            print(f"🔐 Contraseña en BD: '{usuario.contrasena_hash}'")
            print(f"👔 Rol: '{usuario.rol}'")
        
        if usuario and usuario.contrasena_hash == contrasena:
            if usuario.rol in ['barbero', 'admin']:
                session['user_id'] = usuario.id
                session['user_nombre'] = usuario.nombres
                session['user_rol'] = usuario.rol
                
                flash(f'Bienvenido {usuario.nombres}!', 'success')
                return redirect(url_for('main.inicio'))
            else:
                flash('Acceso denegado. Solo barberos pueden ingresar', 'danger')
        else:
            flash('Correo o contraseña incorrectos', 'danger')
    
    return render_template('login/login.html')

# Decorador básico - cualquier usuario autenticado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador solo para barberos
def barbero_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión', 'warning')
            return redirect(url_for('main.login'))
        
        if session.get('user_rol') != 'barbero':
            flash('Acceso denegado. Solo barberos pueden acceder', 'danger')
            return redirect(url_for('main.inicio'))
        
        return f(*args, **kwargs)
    return decorated_function

# Decorador para barberos y admins
def barbero_o_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión', 'warning')
            return redirect(url_for('main.login'))
        
        if session.get('user_rol') not in ['barbero', 'admin']:
            flash('Acceso denegado', 'danger')
            return redirect(url_for('main.inicio'))
        
        return f(*args, **kwargs)
    return decorated_function

# Ruta de LOGOUT
@main.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('main.login'))





# Página de inicio
@main.route('/')
@login_required
def inicio():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    # Si ya está logueado, mostrar el dashboard
    return render_template('/dashboard/dashboard.html')

@main.route('/servicios')
@barbero_required
def listar_servicios():
    servicios = Servicio.query.all()
    return render_template('/servicios/servicios.html', servicios=servicios)

@main.route("/servicios/agregar", methods=["GET", "POST"])
def agregar_servicio():
    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        precio_base = float(request.form["precio_base"])
        duracion_minutos = int(request.form["duracion_minutos"])
        activo = request.form.get("activo") == "on"

        nuevo_servicio = Servicio(
            nombre=nombre,
            descripcion=descripcion,
            precio_base=precio_base,
            duracion_minutos=duracion_minutos,
            activo=activo
        )

        db.session.add(nuevo_servicio)
        db.session.commit()

        return redirect(url_for("main.listar_servicios"))

    return render_template("/servicios/agregar_servicio.html")

@main.route("/servicios/editar/<int:id>", methods=["GET", "POST"])
def editar_servicio(id):
    servicio = Servicio.query.get_or_404(id)

    if request.method == "POST":
        servicio.nombre = request.form["nombre"]
        servicio.descripcion = request.form["descripcion"]
        servicio.precio_base = float(request.form["precio_base"])
        servicio.duracion_minutos = int(request.form["duracion_minutos"])
        servicio.activo = request.form.get("activo") == "on"

        db.session.commit()
        return redirect(url_for("main.listar_servicios"))

    return render_template("servicios/editar.html", servicio=servicio)

@main.route('/servicios/eliminar/<int:id>', methods=["POST"])
def eliminar_servicio(id):
    servicio = Servicio.query.get_or_404(id)
    db.session.delete(servicio)
    db.session.commit()
    return redirect(url_for('main.listar_servicios'))


@main.route("/barberos")
@barbero_o_admin_required
def listar_barberos():
    barberos = Usuario.query.filter_by(rol='barbero').all()
    return render_template("barberos/listar.html", barberos=barberos)


@main.route('/barberos/agregar', methods=['GET', 'POST'])
def agregar_barbero():
    if request.method == 'POST':
        dni = request.form['dni']
        nombres = request.form['nombres']
        apellidos = request.form['apellidos']
        correo = request.form['correo']
        telefono = request.form['telefono']
        especialidad = request.form['especialidad']
        nickname = request.form['nickname']
        contrasena = request.form['contrasena']

        foto = request.files.get('foto')
        foto_url = None

        if foto and foto.filename != '':
            filename = secure_filename(foto.filename)

            # ✅ Usa la carpeta fuera de /app (la verdadera /static)
            carpeta_absoluta = os.path.join(current_app.root_path, '..', 'static', 'img', 'barberos')
            carpeta_absoluta = os.path.abspath(carpeta_absoluta)
            os.makedirs(carpeta_absoluta, exist_ok=True)

            ruta_completa = os.path.join(carpeta_absoluta, filename)
            foto.save(ruta_completa)

            # Esta ruta es la que se usará para mostrar en el navegador
            foto_url = f'static/img/barberos/{filename}'

        nuevo = Usuario(
            dni=dni,
            nombres=nombres,
            apellidos=apellidos,
            correo=correo,
            telefono=telefono,
            nickname=nickname,
            especialidad=especialidad,
            contrasena_hash=contrasena,
            rol='barbero',
            foto_url=foto_url
        )

        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('main.listar_barberos'))

    # Para el <select> de servicios
    servicios = Servicio.query.all()
    return render_template('barberos/nuevo.html', servicios=servicios)


from flask import request, abort
@main.route("/barberos/perfil/<int:barbero_id>")
@login_required
def perfil_barbero(barbero_id):

    if session['rol'] == 'barbero' and session['usuario_id'] != barbero_id:
        return redirect(url_for('main.perfil_barbero', barbero_id=session['usuario_id']))

    barbero = Usuario.query.get_or_404(barbero_id)



    # --- HISTÓRICO DE SERVICIOS (terminados) ---
    reservas = (
        ReservaServicio.query
        .join(Reserva)
        .filter(
            ReservaServicio.barbero_id == barbero.id,
            ReservaServicio.estado_servicio == "terminado"
        )
        .all()
    )

    
    total_ganancia_hist = sum(r.precio_final * (r.porcentaje_barbero or 0.5) for r in reservas)

    # --- HISTÓRICO DE EGRESOS ---
    egresos_hist = GastoExtra.query.filter_by(barbero_id=barbero.id).all()
    total_egresos_hist = sum(e.monto for e in egresos_hist)

    # --- TOTAL FINAL HISTÓRICO ---
    total_final_hist = total_ganancia_hist - total_egresos_hist


    # --- ÚLTIMAS 5 RESERVAS ---

    ultimas_reservas = (
        ReservaServicio.query
        .join(Reserva)
        .filter(
            ReservaServicio.barbero_id == barbero.id,
            ReservaServicio.estado_servicio == "terminado"
        )
        .order_by(Reserva.fecha_reserva.desc())
        .limit(10)
        .all()
    )

    

    return render_template(
        "barberos/perfil.html",
        barbero=barbero,
        total_ganancia_hist=total_ganancia_hist,
        total_egresos_hist=total_egresos_hist,
        total_final_hist=total_final_hist,
        ultimas_reservas=ultimas_reservas
    )



@main.route('/barberos/eliminar/<int:id>', methods=["POST"])
def eliminar_barbero(id):
    barbero = Usuario.query.filter_by(id=id, rol='barbero').first_or_404()
    db.session.delete(barbero)
    db.session.commit()
    return redirect(url_for('main.listar_barberos'))

@main.route('/barberos/editar/<int:id>', methods=["GET", "POST"])
def editar_barbero(id):
    barbero = Usuario.query.filter_by(id=id, rol='barbero').first_or_404()

    if request.method == "POST":
        barbero.nombres = request.form["nombres"]
        barbero.apellidos = request.form["apellidos"]
        barbero.correo = request.form["correo"]
        barbero.telefono = request.form["telefono"]
        barbero.nickname = request.form["nickname"]
        # barbero.contrasena_hash = generate_password_hash(request.form["contrasena"])  # solo si permites cambiarla

        db.session.commit()
        return redirect(url_for('main.perfil_barbero', id=barbero.id))

    return render_template("barberos/editar.html", barbero=barbero)



@main.route("/citas", methods=["GET", "POST"])
@barbero_required
def reservas():
    if request.method == "POST":
        # Procesar creación de reserva
        fecha = request.form["fecha"]
        hora = request.form["hora"]
        cliente_id = request.form["cliente"]
        barbero_id = request.form["barbero"]
        servicios_ids = request.form.getlist("servicios")

        nueva_reserva = Reserva(
            fecha_reserva=fecha,
            hora_inicio_estimada=hora,
            cliente_id=cliente_id,
            barbero_id=barbero_id,
            estado_servicio="pendiente"
        )
        db.session.add(nueva_reserva)
        db.session.commit()

        for servicio_id in servicios_ids:
            db.session.add(ReservaServicio(
                reserva_id=nueva_reserva.id,
                servicio_id=servicio_id
            ))
        db.session.commit()
        return redirect(url_for("main.reservas"))

    # Para el formulario
    clientes = Cliente.query.all()
    barberos = Usuario.query.filter_by(rol='barbero').all()
    servicios = Servicio.query.filter_by(activo=True).all()

    # Filtrado por fecha y paginación
    fecha_str = request.args.get("fecha")
    pagina = int(request.args.get("pagina", 1))
    per_page = 10

    # Fecha a filtrar
    if fecha_str:
        fecha_filtro = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    else:
        fecha_filtro = date.today()

    # Traer todas las reservas del día, ordenadas por hora (recientes arriba)
    reservas_servicio_all = (
        ReservaServicio.query
        .join(Reserva)
        .filter(
            Reserva.fecha_reserva >= fecha_filtro,
            Reserva.fecha_reserva < fecha_filtro + timedelta(days=1)
        )
        .order_by(ReservaServicio.hora_inicio_estimada.desc())
        .all()
    )

    ahora = datetime.now()
    # Calcular estado, formatos y clases
    for rs in reservas_servicio_all:
        inicio_dt = datetime.combine(rs.reserva.fecha_reserva, rs.hora_inicio_estimada)
        fin_dt = inicio_dt + timedelta(minutes=rs.servicio.duracion_minutos)

        if rs.estado_servicio == 'cancelado':
            rs.estado_label = 'Cancelado'
            rs.estado_class = 'danger'
        elif ahora < inicio_dt:
            rs.estado_label = 'En espera'
            rs.estado_class = 'secondary'
        elif inicio_dt <= ahora < fin_dt:
            rs.estado_label = 'En progreso'
            rs.estado_class = 'warning'
        else:
            rs.estado_label = 'Realizado'
            rs.estado_class = 'success'

        rs.fecha_str = rs.reserva.fecha_reserva.strftime("%Y-%m-%d")
        rs.hora_str = rs.hora_inicio_estimada.strftime("%H:%M")
        rs.precio_str = f"{rs.precio_final:.2f}"
        rs.metodo_pago_str = rs.reserva.metodo_pago.capitalize() if rs.reserva.metodo_pago else "En espera"
        rs.metodo_pago_class = 'success' if rs.reserva.metodo_pago else 'secondary'

    # Paginación manual
    total = len(reservas_servicio_all)
    total_paginas = ceil(total / per_page)
    start = (pagina - 1) * per_page
    end = start + per_page
    reservas_pag = reservas_servicio_all[start:end]

    return render_template(
        "citas/listar_citas.html",
        reservas_servicio=reservas_pag,
        clientes=clientes,
        barberos=barberos,
        servicios=servicios,
        fecha=fecha_filtro,
        pagina=pagina,
        total_paginas=total_paginas
    )



@main.route('/clientes/buscar/<dni>')
@barbero_required
def buscar_cliente_por_dni(dni):
    cliente = Cliente.query.filter_by(dni=dni).first()
    if cliente:
        return jsonify({'nombre': cliente.nombre})
    else:
        return jsonify({'nombre': ''})

@main.route('/citas/nueva', methods=["POST"])
def buscar_o_crear_cliente():
    dni = request.form['dni'].strip()
    nombre = request.form['nombre'].strip()

    cliente = Cliente.query.filter_by(dni=dni).first()

    if not cliente:
        cliente = Cliente(dni=dni, nombre=nombre)
        db.session.add(cliente)
        db.session.commit()

    # Crear la reserva en blanco
    nueva = Reserva(
        cliente_id=cliente.id,
        fecha_reserva=date.today(),
        hora_reserva=datetime.now().time(),
        estado_pago='no_pagado',
        total=0.0
    )
    db.session.add(nueva)
    db.session.commit()

    return redirect(url_for('main.agregar_servicios_a_reserva', reserva_id=nueva.id))

@main.route("/citas/nueva", methods=["GET"])
def nueva_reserva():
    return render_template("citas/nueva_reserva.html")

@main.route('/citas/agregar/<int:reserva_id>', methods=['GET', 'POST'])
def agregar_servicios_a_reserva(reserva_id):
    reserva = Reserva.query.get_or_404(reserva_id)
    servicios = Servicio.query.filter_by(activo=True).all()
    barberos = Usuario.query.filter_by(rol='barbero').all()

    cliente = reserva.cliente  


    if request.method == 'POST':
        # ✅ Ya dentro del POST puedes usar request.form
        servicio_id = request.form['servicio_id']
        barbero_id = request.form['barbero_id']
        precio_final = float(request.form['precio_final'])

        persona_atendida = request.form.get('persona_atendida')
        if not persona_atendida or persona_atendida.strip() == "":
            persona_atendida = reserva.cliente.nombre  # ✅ Usas reserva.cliente
        
            # Obtener fecha y hora del formulario
        fecha_input = request.form.get('fecha')
        hora_input = request.form.get('hora')

        # Establecer fecha si se proporcionó
        if fecha_input:
            reserva.fecha_reserva = datetime.strptime(fecha_input, '%Y-%m-%d').date()

        # Establecer hora
        if hora_input:
            hora_inicio = datetime.strptime(hora_input, '%H:%M').time()
        else:
            hora_inicio = datetime.now().time() 

        porcentaje_barbero = request.form.get('porcentaje_barbero')
        if porcentaje_barbero:
            porcentaje_barbero = float(porcentaje_barbero) / 100  # convertir a decimal
        else:
            porcentaje_barbero = 0.5  # valor por defecto 50%

        comentario = request.form.get('comentario', '')

        nuevo = ReservaServicio(
            reserva_id=reserva.id,
            servicio_id=servicio_id,
            barbero_id=barbero_id,
            precio_final=precio_final,
            persona_atendida=persona_atendida,
            comentario=comentario,
            hora_inicio_estimada=hora_inicio,
            estado_servicio='en_espera',
            porcentaje_barbero=porcentaje_barbero
        )
        db.session.add(nuevo)
        db.session.commit()

        return redirect(url_for('main.agregar_servicios_a_reserva', reserva_id=reserva.id))

    reserva_servicios = ReservaServicio.query.filter_by(reserva_id=reserva.id).all()

    return render_template('citas/agregar_servicio.html',
                            reserva=reserva,
                            servicios=servicios,
                            barberos=barberos,
                            reserva_servicios=reserva_servicios)

@main.route('/citas/finalizar/<int:reserva_id>', methods=['POST'])
def finalizar_reserva(reserva_id):
    reserva = Reserva.query.get_or_404(reserva_id)
    metodo_pago = request.form.get('metodo_pago')

    # Actualizar reserva
    reserva.metodo_pago = metodo_pago if metodo_pago else None
    reserva.estado_pago = 'pagado' if metodo_pago else 'no_pagado'

    # Calcular total
    total = sum([rs.precio_final for rs in reserva.servicios_detalle])
    reserva.total = total

    db.session.commit()
    return redirect(url_for('main.reservas'))

@main.route('/reserva-servicio/eliminar/<int:id>', methods=['POST'])
def eliminar_reserva_servicio(id):
    rs = ReservaServicio.query.get_or_404(id)
    reserva_id = rs.reserva_id
    db.session.delete(rs)
    db.session.commit()
    return redirect(url_for('main.reservas'))

@main.route('/reserva-servicio/editar/<int:id>', methods=['GET', 'POST'])
def editar_reserva_servicio(id):
    rs = ReservaServicio.query.get_or_404(id)
    servicios = Servicio.query.filter_by(activo=True).all()
    barberos = Usuario.query.filter_by(rol='barbero').all()

    if request.method == 'POST':
        rs.servicio_id = request.form['servicio_id']
        rs.barbero_id = request.form['barbero_id']
        rs.precio_final = float(request.form['precio_final'])
        rs.persona_atendida = request.form.get('persona_atendida')
        rs.comentario = request.form.get('comentario')


        estado = request.form.get('estado_servicio')
        if estado:
            rs.estado_servicio = estado

        hora_input = request.form.get('hora')
        if hora_input:
            rs.hora_inicio_estimada = datetime.strptime(hora_input, '%H:%M').time()

        fecha_input = request.form.get('fecha')
        if fecha_input:
            rs.reserva.fecha_reserva = datetime.strptime(fecha_input, '%Y-%m-%d').date()

        metodo_pago = request.form.get('metodo_pago')
        rs.reserva.metodo_pago = metodo_pago if metodo_pago else None
        rs.reserva.estado_pago = "pagado" if metodo_pago else "no_pagado"


        db.session.commit()
        return redirect(url_for('main.reservas'))


    return render_template('citas/editar_reserva.html', rs=rs, servicios=servicios, barberos=barberos)


@main.route("/clientes")
def listar_clientes():
    clientes = Cliente.query.all()
    return render_template("clientes/listar_clientes.html", clientes=clientes)

@main.route("/clientes/perfil/<int:id>")
def perfil_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    reservas = Reserva.query.filter_by(cliente_id=id).all()
    for r in reservas:
        print(f"Reserva {r.id} - Fecha: {r.fecha_reserva}")
        print(f"  Servicios:", r.servicios_detalle)
        for d in r.servicios_detalle:
            print(f"    → Servicio ID: {d.servicio_id}, Persona: {d.persona_atendida}, Monto: {d.precio_final}")

    return render_template("clientes/perfil_cliente.html", cliente=cliente, reservas=reservas)

@main.route("/clientes/nuevo", methods=["GET", "POST"])
def nuevo_cliente():
    if request.method == "POST":
        nombre = request.form["nombre"]
        dni = request.form["dni"]
        telefono = request.form.get("telefono")
        correo = request.form.get("correo")

        nuevo = Cliente(nombre=nombre, dni=dni, telefono=telefono, correo=correo)
        db.session.add(nuevo)

        try:
            db.session.commit()
            return redirect(url_for("main.listar_clientes"))
        except IntegrityError:
            db.session.rollback()  # limpia la sesión si hubo error
            flash("El DNI ya está registrado.", "danger")

    return render_template("clientes/nuevo_cliente.html")


@main.route("/clientes/editar/<int:id>", methods=["GET", "POST"])
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == "POST":
        cliente.nombre = request.form["nombre"]
        cliente.dni = request.form["dni"]
        cliente.telefono = request.form["telefono"]
        cliente.correo = request.form["correo"]
        db.session.commit()
        return redirect(url_for("main.listar_clientes"))
    return render_template("clientes/editar_cliente.html", cliente=cliente)

@main.route("/clientes/eliminar/<int:id>", methods=["POST"])
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    return redirect(url_for("main.listar_clientes"))


@main.route('/pagos')
@barbero_o_admin_required
def pagos_index():
    barberos = Usuario.query.filter_by(rol='barbero').all()
    return render_template('pagos/index.html', barberos=barberos)



from datetime import date
from app.models import ReporteDiario, GastoExtra

@main.route("/widget_reporte_diario")
def widget_reporte_diario():
    hoy = date.today()

    servicios_hoy = ReservaServicio.query.join(Reserva).filter(
        Reserva.fecha_reserva == hoy
    ).all()

    ingresos = 0
    egresos = 0
    pendientes = 0
    pendientes_count = 0

    pagos = {
        "yape": 0,
        "plin": 0,
        "efectivo": 0,
        "otro": 0
    }

    servicios_realizados = 0

    for s in servicios_hoy:
        monto = s.precio_final or 0   # ← usamos precio_final, no monto

        if s.reserva.estado_pago != "no_pagado":
            ingresos += monto

            if s.reserva.metodo_pago == "yape":
                pagos["yape"] += monto
            elif s.reserva.metodo_pago == "plin":
                pagos["plin"] += monto
            elif s.reserva.metodo_pago == "efectivo":
                pagos["efectivo"] += monto
            else:
                pagos["otro"] += monto
        else:
            pendientes += monto
            pendientes_count += 1

        if s.reserva.estado_pago == "pagado" or "no_pagado":
            servicios_realizados += 1


    total_neto = ingresos - egresos

    data = {
        "total_neto": total_neto,
        "ingresos": ingresos,
        "egresos": egresos,
        "pendientes": {
            "count": pendientes_count,
            "monto": pendientes
        },
        "pagos": pagos,
        "servicios_realizados": servicios_realizados
    }

    variant = request.args.get("variant", "default")

    return render_template("widget.html", data=data, variant=variant)


#EGRESOS
from datetime import datetime, date, timedelta

@main.route("/egresos", methods=["GET"])
def listar_egresos():
    fecha_str = request.args.get("fecha")
    if fecha_str:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    else:
        fecha = date.today()

    egresos = GastoExtra.query.filter(GastoExtra.fecha == fecha).order_by(GastoExtra.id.asc()).all()
    total_egresos = sum(e.monto for e in egresos)

    # Calculamos las fechas de navegación
    fecha_ayer = fecha - timedelta(days=1)
    fecha_manana = fecha + timedelta(days=1)

    return render_template(
        "egresos/listar_egresos.html",
        egresos=egresos,
        fecha=fecha,
        total_egresos=total_egresos,
        fecha_ayer=fecha_ayer,
        fecha_manana=fecha_manana
    )



@main.route("/egresos/nuevo", methods=["GET", "POST"])
def nuevo_egreso():
    if request.method == "POST":
        persona_id = request.form.get("barbero_id")  # puede ser None
        motivo = request.form.get("motivo")
        monto = float(request.form.get("monto", 0))
        observacion = request.form.get("observacion")

        # Obtener la hora del formulario (opcional)
        hora_str = request.form.get("hora")
        if hora_str:
            hora_egreso = datetime.strptime(hora_str, "%H:%M").time()
        else:
            hora_egreso = datetime.now().time()

        # Crear o traer el reporte diario del día
        reporte = ReporteDiario.query.filter_by(fecha=date.today()).first()
        if not reporte:
            reporte = ReporteDiario(fecha=date.today())
            db.session.add(reporte)
            db.session.commit()

        # Crear egreso
        nuevo = GastoExtra(
            fecha=date.today(),
            hora=hora_egreso,
            monto=monto,
            motivo=motivo,
            observacion=observacion,
            barbero_id=persona_id if persona_id else None,
            reporte_id=reporte.id
        )

        db.session.add(nuevo)
        db.session.commit()
        flash("Egreso registrado correctamente", "success")
        return redirect(url_for("main.listar_egresos"))

    # Traer barberos para el select
    barberos = Usuario.query.filter_by(rol="barbero").all()
    return render_template("egresos/nuevo_egreso.html", barberos=barberos)



#PAGOS BARBERO

@main.route("/barbero/<int:barbero_id>/pagos", methods=["GET", "POST"])
def pagos_barbero(barbero_id):
    barbero = Usuario.query.get_or_404(barbero_id)

    # Fecha a filtrar
    fecha_str = request.args.get("fecha")
    if fecha_str:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    else:
        fecha = date.today()

    # Servicios realizados por el barbero en la fecha
    reservas = (
        ReservaServicio.query
        .join(Reserva)
        .filter(
            Reserva.fecha_reserva == fecha,
            ReservaServicio.barbero_id == barbero.id,
            ReservaServicio.estado_servicio == "terminado"
        )
        .order_by(Reserva.hora_reserva.asc())
        .all()
    )

    # Descuentos / egresos asignados al barbero en la fecha
    egresos = GastoExtra.query.filter(
        GastoExtra.barbero_id == barbero.id,
        GastoExtra.fecha == fecha
    ).all()

    # Cálculos iniciales
    total_servicios = sum(d.precio_final * (d.porcentaje_barbero or 0.5) for d in reservas)
    total_descuentos = sum(e.monto for e in egresos)
    total_final = total_servicios - total_descuentos

    # Si se envía POST (guardar % manual o descuentos)
    porcentaje = 0
    descuento = 0
    if request.method == "POST":
        porcentaje = float(request.form.get("porcentaje", 0))
        descuento = float(request.form.get("descuento", 0))
        total_ganado = total_servicios * (porcentaje / 100)
        total_final = total_ganado - descuento
        # Guardar en PagoBarbero opcional
        nuevo_pago = PagoBarbero(
            barbero_id=barbero.id,
            fecha=fecha,
            total_servicios=total_servicios,
            total_ganado=total_ganado,
            total_descuentos=descuento,
            total_final=total_final
        )
        db.session.add(nuevo_pago)
        db.session.commit()
    
    return render_template(
        "pagos/pagos_barbero.html",
        barbero=barbero,
        fecha=fecha,
        reservas=reservas,  # ahora son objetos ReservaServicio
        egresos=egresos,
        total_servicios=total_servicios,
        total_descuentos=total_descuentos,
        total_final=total_final,
        porcentaje=porcentaje,
        descuento=descuento
    )

#REPORTE

@main.route("/reportes", methods=["GET"])
def reporte_diario():
    # Filtrar fecha
    fecha_str = request.args.get("fecha")
    if fecha_str:
        fecha = date.fromisoformat(fecha_str)
    else:
        fecha = date.today()

    # Servicios terminados del día
    servicios = ReservaServicio.query.filter(
        ReservaServicio.estado_servicio == "terminado",
        ReservaServicio.reserva.has(fecha_reserva=fecha)
    ).all()

    servicios_pagados = [s for s in servicios if s.reserva.estado_pago == "pagado"]
    servicios_no_pagados = [s for s in servicios if s.reserva.estado_pago == "no_pagado"]

    ingresos_total = sum(s.precio_final for s in servicios_pagados)
    total_barberos = sum(s.precio_final * s.porcentaje_barbero for s in servicios if s.estado_servicio == "terminado")
    total_no_pagados = sum(s.precio_final for s in servicios_no_pagados)


    ganancia_empresa_pagados = sum(
    s.precio_final * (1 - s.porcentaje_barbero) for s in servicios_pagados
)
    costo_barberos_no_pagados = sum(
        s.precio_final * s.porcentaje_barbero for s in servicios_no_pagados
    )
    ganancia_neta = ganancia_empresa_pagados - costo_barberos_no_pagados

    # Conteo de servicios
    servicios_realizados = len(servicios)
    servicios_cancelados = ReservaServicio.query.join(ReservaServicio.reserva)\
        .filter(
            ReservaServicio.estado_servicio == "cancelado",
            ReservaServicio.reserva.has(fecha_reserva=fecha)
        ).count()
    servicios_totales = servicios_realizados + servicios_cancelados + \
        ReservaServicio.query.join(ReservaServicio.reserva)\
        .filter(
            ReservaServicio.estado_servicio.in_(["en_espera","pendiente","en_proceso"]),
            ReservaServicio.reserva.has(fecha_reserva=fecha)
        ).count()


    # Servicios sin cobrar: terminados pero con estado_pago = no_pagado
    servicios_sin_cobrar = ReservaServicio.query.join(Reserva) \
        .filter(
            Reserva.fecha_reserva == fecha,
            Reserva.estado_pago == "no_pagado",
            ReservaServicio.estado_servicio == "terminado"
        ).count()


    # Egresos del día (solo los que no son de barbero)
    egresos = GastoExtra.query.filter(
        GastoExtra.fecha == fecha,
        GastoExtra.barbero_id == None  # <-- solo egresos de empresa
    ).all()
    egresos_total = sum(e.monto for e in egresos)

    # Ajustar ganancia neta restando solo estos egresos
    ganancia_neta -= egresos_total

    # Totales por método de pago
    total_yape = sum(s.precio_final for s in servicios if s.reserva.metodo_pago == "yape")
    total_plin = sum(s.precio_final for s in servicios if s.reserva.metodo_pago == "plin")
    total_efectivo = sum(s.precio_final for s in servicios if s.reserva.metodo_pago == "efectivo")
    total_otro = sum(s.precio_final for s in servicios if s.reserva.metodo_pago == "otro")

    # Guardar o actualizar ReporteDiario
    reporte = ReporteDiario.query.filter_by(fecha=fecha).first()
    if not reporte:
        reporte = ReporteDiario(fecha=fecha)
        db.session.add(reporte)

    reporte.ingresos_total = ingresos_total
    reporte.ganancia_neta = ganancia_neta
    reporte.egresos_total = egresos_total
    reporte.servicios_realizados = servicios_realizados
    reporte.servicios_cancelados = servicios_cancelados
    reporte.servicios_totales = servicios_totales
    reporte.total_yape = total_yape
    reporte.total_plin = total_plin
    reporte.total_efectivo = total_efectivo
    reporte.total_otro = total_otro

    db.session.commit()

    return render_template(
        "reportes/reporte_diario.html",
        fecha=fecha,
        reporte=reporte,
        servicios=servicios,
        egresos=egresos,
        total_barberos=total_barberos,
        total_no_pagados=total_no_pagados,               
        servicios_sin_cobrar=len(servicios_no_pagados),
        egresos_total=egresos_total,
    )



#DASHBOARD

@main.route("/dashboard", methods=["GET"])
@barbero_required
def dashboard():
    # Fecha seleccionada o hoy
    fecha_str = request.args.get("fecha")
    if fecha_str:
        fecha = date.fromisoformat(fecha_str)
    else:
        fecha = date.today()

    # --- Servicios del día pagados ---
    from sqlalchemy import and_

    servicios = ReservaServicio.query.join(ReservaServicio.reserva)\
        .filter(
            ReservaServicio.estado_servicio == "terminado",
            ReservaServicio.reserva.has(
                and_(
                    Reserva.fecha_reserva == fecha,
                    Reserva.estado_pago != 'no_pagado'
                )
            )
        ).all()


    # Totales por método de pago
    total_efectivo = sum(s.precio_final for s in servicios if s.reserva.metodo_pago == "efectivo")
    total_yape = sum(s.precio_final for s in servicios if s.reserva.metodo_pago == "yape")
    total_plin = sum(s.precio_final for s in servicios if s.reserva.metodo_pago == "plin")
    total_otro = sum(s.precio_final for s in servicios if s.reserva.metodo_pago == "otro")

    # --- Egresos del día ---
    egresos = GastoExtra.query.filter(GastoExtra.fecha == fecha).all()
    egresos_total = sum(e.monto for e in egresos)

    # Caja neta = efectivo - egresos
    caja_neta = total_efectivo - egresos_total

    # --- Movimientos del día ---
    movimientos = []

    # Ingresos: servicios
    for s in servicios:
        movimientos.append({
            "hora": s.reserva.hora_reserva,
            "tipo": "Servicio",
            "detalle": f"{s.reserva.cliente.nombre if s.reserva.cliente else 'Cliente'} - {s.servicio.nombre}",
            "monto": s.precio_final,
            "metodo": s.reserva.metodo_pago
        })

    # Egresos
    for e in egresos:
        movimientos.append({
            "hora": e.hora,
            "tipo": "Egreso",
            "detalle": e.motivo,
            "monto": -e.monto,
            "metodo": "Egreso"
        })

    # Ordenar por hora
    movimientos.sort(key=lambda x: x["hora"])
    
    from sqlalchemy import or_
    hoy = date.today()

    servicios_sin_cobrar = (
        ReservaServicio.query
        .join(Reserva)
        .filter(
            Reserva.fecha_reserva == hoy,
            ReservaServicio.estado_servicio == 'terminado',
            or_(
                Reserva.estado_pago != 'pagado'  # cualquier cosa que NO sea "pagado"
            )
        )
        .count()
    )


    fecha = date.today()

    # 2️⃣ Mejor barbero del día (más cortes realizados)
    from sqlalchemy import func

    mejor_barbero = db.session.query(
        ReservaServicio.barbero_id,
        func.count(ReservaServicio.id).label('total_cortes')
    ).join(ReservaServicio.reserva)\
    .filter(ReservaServicio.reserva.has(fecha_reserva=fecha),
            ReservaServicio.estado_servicio=='terminado')\
    .group_by(ReservaServicio.barbero_id)\
    .order_by(func.count(ReservaServicio.id).desc())\
    .first()

    # Traer el objeto Barbero si existe
    if mejor_barbero:
        barbero_obj = Usuario.query.get(mejor_barbero.barbero_id)
        total_cortes = mejor_barbero.total_cortes
    else:
        barbero_obj = None
        total_cortes = 0

    # 3️⃣ Servicio más popular históricamente
    servicio_popular = db.session.query(
        ReservaServicio.servicio_id,
        func.count(ReservaServicio.id).label('total_veces')
    ).filter(ReservaServicio.estado_servicio=='terminado')\
    .group_by(ReservaServicio.servicio_id)\
    .order_by(func.count(ReservaServicio.id).desc())\
    .first()

    if servicio_popular:
        servicio_obj = Servicio.query.get(servicio_popular.servicio_id)
        veces_realizado = servicio_popular.total_veces
    else:
        servicio_obj = None
        veces_realizado = 0


    return render_template(
        "dashboard/dashboard.html",
        fecha=fecha,
        total_efectivo=total_efectivo,
        total_yape=total_yape,
        total_plin=total_plin,
        total_otro=total_otro,
        caja_neta=caja_neta,
        movimientos=movimientos,
        egresos_total=egresos_total,
        servicios_sin_cobrar=servicios_sin_cobrar,
        mejor_barbero=barbero_obj,
        total_cortes=total_cortes,
        servicio_popular=servicio_obj,
        veces_realizado=veces_realizado,
    )




