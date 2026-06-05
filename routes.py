from functools import wraps
from flask import request, jsonify, redirect, url_for, render_template, send_file
from flask_login import login_required, current_user, login_user, logout_user
from config import db
from models import Ciudadano, Tramite, Documento, Alerta, AuditLog, EstadoTramite, Prioridad, Usuario, Rol
from ml_models import DocumentClassifier, PriorityPredictor
from notification_system import NotificationSystem
import auth
from datetime import datetime
import io

notification_system = NotificationSystem()

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({'error': 'Acceso no autorizado'}), 403
        return f(*args, **kwargs)
    return decorated


def registrar_auditoria(usuario_id, accion, tabla, registro_id=None, detalle=None):
    audit = AuditLog(
        usuario_id=usuario_id,
        accion=accion,
        tabla=tabla,
        registro_id=registro_id,
        detalle=detalle
    )
    db.session.add(audit)
    db.session.commit()


def _build_dataframe_from_tramites(tramites):
    import pandas as pd
    rows = []
    for tramite in tramites:
        rows.append({
            'ID': tramite.id,
            'Ciudadano': f'{tramite.ciudadano.nombres or ""} {tramite.ciudadano.apellidos or ""}',
            'Email': tramite.ciudadano.email,
            'Tipo Trámite': tramite.tipo_tramite,
            'Estado': tramite.estado,
            'Prioridad': tramite.prioridad,
            'Fecha Solicitud': tramite.fecha_solicitud,
            'Fecha Actualización': tramite.fecha_actualizacion,
            'Fecha Completado': tramite.fecha_completado,
            'Observaciones': tramite.observaciones
        })
    return pd.DataFrame(rows)


def _build_dataframe_from_ciudadanos(ciudadanos):
    import pandas as pd
    rows = []
    for ciudadano in ciudadanos:
        rows.append({
            'ID': ciudadano.id,
            'Usuario ID': ciudadano.usuario_id,
            'DNI': ciudadano.dni,
            'Nombres': ciudadano.nombres,
            'Apellidos': ciudadano.apellidos,
            'Email': ciudadano.email,
            'Teléfono': ciudadano.telefono,
            'Dirección': ciudadano.direccion,
            'Fecha Registro': ciudadano.fecha_registro
        })
    return pd.DataFrame(rows)


def _export_dataframe_to_excel(df, filename):
    try:
        import pandas as pd
    except ImportError:
        return jsonify({'error': 'Dependencia pandas no instalada. Ejecute pip install -r requirements.txt'}), 500

    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Datos')
    except ImportError:
        return jsonify({'error': 'Dependencia openpyxl no instalada. Ejecute pip install -r requirements.txt'}), 500

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name=f'{filename}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


def _export_dataframe_to_pdf(df, filename, title):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        return jsonify({'error': 'Dependencia reportlab no instalada. Ejecute pip install -r requirements.txt'}), 500

    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=letter)
    width, height = letter
    line_height = 14
    x_offset = 40
    y = height - 50

    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawString(x_offset, y, title)
    y -= 30

    pdf.setFont('Helvetica-Bold', 10)
    headers = list(df.columns)
    header_line = '  '.join(str(h) for h in headers)
    pdf.drawString(x_offset, y, header_line[:180])
    y -= line_height
    pdf.setFont('Helvetica', 9)

    for _, row in df.iterrows():
        row_values = [str(row[col]) if row[col] is not None else '' for col in headers]
        row_line = '  '.join(row_values)
        lines = [row_line[i:i+180] for i in range(0, len(row_line), 180)]
        for line in lines:
            if y < 60:
                pdf.showPage()
                y = height - 50
                pdf.setFont('Helvetica', 9)
            pdf.drawString(x_offset, y, line)
            y -= line_height

    pdf.save()
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name=f'{filename}.pdf',
        mimetype='application/pdf'
    )


def register_routes(app):
    @app.route('/login')
    def login():
        if current_user.is_authenticated:
            if current_user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('citizen_dashboard'))
        auth_url = auth.get_google_auth_url() if app.config.get('GOOGLE_CLIENT_ID') else '#'
        return render_template('login.html', auth_url=auth_url)
    
    @app.route('/api/login', methods=['POST'])
    def api_login():
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        user = Usuario.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        if not user.activo:
            return jsonify({'error': 'Usuario inactivo'}), 403
        
        login_user(user)
        
        # Redirigir según el rol
        if user.is_admin():
            return jsonify({'redirect_url': '/admin/dashboard'})
        else:
            return jsonify({'redirect_url': '/citizen/dashboard'})
    
    @app.route('/api/register', methods=['POST'])
    def register():
        data = request.json or {}
        nombre = data.get('nombre', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        
        if not nombre or not email or not password:
            return jsonify({'error': 'Nombre, email y contraseña son obligatorios'}), 400
        
        if Usuario.query.filter_by(email=email).first():
            return jsonify({'error': 'El email ya está registrado'}), 400
        
        user = Usuario(
            email=email,
            nombre=nombre,
            rol=Rol.CIUDADANO.value
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        ciudadano = Ciudadano(
            usuario_id=user.id,
            email=email
        )
        db.session.add(ciudadano)
        db.session.commit()
        
        registrar_auditoria(user.id, 'registro_usuario', 'usuarios', user.id, f'Usuario ciudadano creado: {email}')
        
        login_user(user)
        
        return jsonify({'redirect_url': '/citizen/dashboard'})
    
    @app.route('/api/current-user', methods=['GET'])
    @login_required
    def get_current_user():
        return jsonify(current_user.to_dict())
    
    @app.route('/api/mi-perfil', methods=['GET'])
    @login_required
    def get_mi_perfil():
        if current_user.is_admin():
            return jsonify({'error': 'No disponible para administradores'}), 403
        
        ciudadano = Ciudadano.query.filter_by(usuario_id=current_user.id).first()
        total_tramites = Tramite.query.filter_by(ciudadano_id=ciudadano.id if ciudadano else None).count() if ciudadano else 0
        
        return jsonify({
            'usuario': current_user.to_dict(),
            'ciudadano': ciudadano.to_dict() if ciudadano else None,
            'total_tramites': total_tramites
        })
    
    @app.route('/api/mi-perfil', methods=['PUT'])
    @login_required
    def update_mi_perfil():
        if current_user.is_admin():
            return jsonify({'error': 'No disponible para administradores'}), 403
        
        data = request.json
        ciudadano = Ciudadano.query.filter_by(usuario_id=current_user.id).first()
        
        if not ciudadano:
            ciudadano = Ciudadano(
                usuario_id=current_user.id,
                email=current_user.email
            )
            db.session.add(ciudadano)
        
        ciudadano.dni = data.get('dni', ciudadano.dni)
        ciudadano.nombres = data.get('nombres', ciudadano.nombres)
        ciudadano.apellidos = data.get('apellidos', ciudadano.apellidos)
        ciudadano.telefono = data.get('telefono', ciudadano.telefono)
        ciudadano.direccion = data.get('direccion', ciudadano.direccion)
        
        db.session.commit()
        
        return jsonify({'mensaje': 'Perfil actualizado exitosamente', 'ciudadano': ciudadano.to_dict()})
    
    @app.route('/api/mis-tramites', methods=['GET'])
    @login_required
    def get_mis_tramites():
        if current_user.is_admin():
            return jsonify({'error': 'No disponible para administradores'}), 403
        
        ciudadano = Ciudadano.query.filter_by(usuario_id=current_user.id).first()
        if not ciudadano:
            return jsonify([])
        
        tramites = Tramite.query.filter_by(ciudadano_id=ciudadano.id).all()
        return jsonify([tramite.to_dict() for tramite in tramites])
    
    @app.route('/api/mis-tramites', methods=['POST'])
    @login_required
    def crear_mi_tramite():
        if current_user.is_admin():
            return jsonify({'error': 'No disponible para administradores'}), 403
        
        data = request.json or {}
        tipo_tramite = data.get('tipo_tramite', '').strip()
        if not tipo_tramite:
            return jsonify({'error': 'El tipo de trámite es obligatorio'}), 400
        
        ciudadano = Ciudadano.query.filter_by(usuario_id=current_user.id).first()
        if not ciudadano:
            ciudadano = Ciudadano(
                usuario_id=current_user.id,
                email=current_user.email
            )
            db.session.add(ciudadano)
            db.session.commit()
        
        tramite = Tramite(
            ciudadano_id=ciudadano.id,
            tipo_tramite=tipo_tramite,
            descripcion=data.get('descripcion', '').strip(),
            estado=EstadoTramite.PENDIENTE.value
        )
        
        predictor = PriorityPredictor()
        tramite_data = {
            'tipo_tramite': tipo_tramite,
            'descripcion': data.get('descripcion', ''),
            'num_documentos': len(data.get('documentos', []))
        }
        prioridad, confianza = predictor.predict(tramite_data)
        tramite.prioridad = prioridad
        
        db.session.add(tramite)
        db.session.commit()
        
        if 'documentos' in data:
            classifier = DocumentClassifier()
            for doc_data in data['documentos']:
                documento = Documento(
                    tramite_id=tramite.id,
                    tipo_documento=doc_data.get('tipo_documento', '').strip(),
                    nombre_archivo=doc_data.get('nombre_archivo', '').strip(),
                    contenido=doc_data.get('contenido', '')
                )
                
                clasificacion, puntuacion = classifier.predict(documento.contenido)
                documento.clasificacion_ml = clasificacion
                documento.puntuacion_ml = puntuacion
                
                db.session.add(documento)
            
            db.session.commit()
        
        notification_system.enviar_notificacion_tramite(
            ciudadano.email,
            tramite.id,
            tramite.tipo_tramite,
            'creado'
        )
        
        alerta = Alerta(
            tramite_id=tramite.id,
            tipo_alerta='creacion',
            mensaje=f'Trámite {tramite.tipo_tramite} creado por {current_user.nombre} con prioridad {prioridad}',
            canal='email'
        )
        db.session.add(alerta)
        db.session.commit()

        registrar_auditoria(current_user.id, 'crear_tramite', 'tramites', tramite.id, f'Tramite creado por ciudadano {current_user.email}')
        
        return jsonify({
            'mensaje': 'Trámite creado exitosamente',
            'tramite': tramite.to_dict(),
            'prioridad_ml': prioridad,
            'confianza_ml': confianza
        }), 201
    
    @app.route('/api/mis-tramites/<int:tramite_id>', methods=['GET'])
    @login_required
    def get_mi_tramite(tramite_id):
        if current_user.is_admin():
            return jsonify({'error': 'No disponible para administradores'}), 403
        
        ciudadano = Ciudadano.query.filter_by(usuario_id=current_user.id).first()
        if not ciudadano:
            return jsonify({'error': 'Ciudadano no encontrado'}), 404
        
        tramite = Tramite.query.filter_by(id=tramite_id, ciudadano_id=ciudadano.id).first_or_404()
        tramite_dict = tramite.to_dict()
        tramite_dict['documentos'] = [doc.to_dict() for doc in tramite.documentos]
        tramite_dict['alertas'] = [alerta.to_dict() for alerta in tramite.alertas]
        return jsonify(tramite_dict)
    
    @app.route('/api/ciudadanos', methods=['POST'])
    @login_required
    @admin_required
    def crear_ciudadano():
        data = request.json or {}
        dni = data.get('dni', '').strip()
        nombres = data.get('nombres', '').strip()
        apellidos = data.get('apellidos', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()

        if not dni or not nombres or not apellidos or not email or not password:
            return jsonify({'error': 'DNI, nombres, apellidos, email y contraseña son obligatorios'}), 400

        if Ciudadano.query.filter_by(dni=dni).first():
            return jsonify({'error': 'El DNI ya está registrado'}), 400

        user = Usuario.query.filter_by(email=email).first()
        if user and user.is_admin():
            return jsonify({'error': 'No se puede registrar un ciudadano con un email de administrador'}), 400

        if user and user.ciudadano:
            return jsonify({'error': 'El email ya está registrado para otro ciudadano'}), 400

        if not user:
            user = Usuario(
                email=email,
                nombre=f'{nombres} {apellidos}',
                rol=Rol.CIUDADANO.value,
                activo=True
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
        else:
            if not user.password_hash:
                user.set_password(password)
            user.rol = Rol.CIUDADANO.value
            user.activo = True
            db.session.add(user)
            db.session.flush()

        ciudadano = Ciudadano(
            usuario_id=user.id,
            dni=dni,
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            telefono=data.get('telefono', '').strip(),
            direccion=data.get('direccion', '').strip()
        )

        db.session.add(ciudadano)
        db.session.commit()
        registrar_auditoria(current_user.id, 'crear_ciudadano', 'ciudadanos', ciudadano.id, f'Ciudadano creado: {dni}')

        return jsonify({'mensaje': 'Ciudadano creado exitosamente', 'ciudadano': ciudadano.to_dict()}), 201

    @app.route('/api/ciudadanos/<int:ciudadano_id>', methods=['GET'])
    @login_required
    @admin_required
    def obtener_ciudadano(ciudadano_id):
        ciudadano = Ciudadano.query.get_or_404(ciudadano_id)
        return jsonify(ciudadano.to_dict())

    @app.route('/api/ciudadanos', methods=['GET'])
    @login_required
    @admin_required
    def listar_ciudadanos():
        ciudadanos = Ciudadano.query.all()
        return jsonify([c.to_dict() for c in ciudadanos])

    @app.route('/api/export/ciudadanos', methods=['GET'])
    @login_required
    @admin_required
    def exportar_ciudadanos():
        formato = request.args.get('format', 'xlsx').lower()
        ciudadanos = Ciudadano.query.all()
        df = _build_dataframe_from_ciudadanos(ciudadanos)
        filename = f'ciudadanos_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}'
        if formato == 'pdf':
            return _export_dataframe_to_pdf(df, filename, 'Reporte de Ciudadanos')
        return _export_dataframe_to_excel(df, filename)

    @app.route('/api/export/tramites', methods=['GET'])
    @login_required
    @admin_required
    def exportar_tramites():
        formato = request.args.get('format', 'xlsx').lower()
        tramites = Tramite.query.all()
        df = _build_dataframe_from_tramites(tramites)
        filename = f'tramites_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}'
        if formato == 'pdf':
            return _export_dataframe_to_pdf(df, filename, 'Reporte de Trámites')
        return _export_dataframe_to_excel(df, filename)

    @app.route('/api/tramites', methods=['POST'])
    @login_required
    @admin_required
    def crear_tramite():
        data = request.json or {}
        ciudadano_id = data.get('ciudadano_id')
        tipo_tramite = data.get('tipo_tramite', '').strip()

        if not ciudadano_id or not tipo_tramite:
            return jsonify({'error': 'Ciudadano e información de trámite son obligatorios'}), 400

        ciudadano = Ciudadano.query.get_or_404(ciudadano_id)
        
        tramite = Tramite(
            ciudadano_id=ciudadano.id,
            tipo_tramite=tipo_tramite,
            descripcion=data.get('descripcion', '').strip(),
            estado=EstadoTramite.PENDIENTE.value
        )
        
        predictor = PriorityPredictor()
        tramite_data = {
            'tipo_tramite': tipo_tramite,
            'descripcion': data.get('descripcion', ''),
            'num_documentos': len(data.get('documentos', []))
        }
        prioridad, confianza = predictor.predict(tramite_data)
        tramite.prioridad = prioridad
        
        db.session.add(tramite)
        db.session.commit()
        
        if 'documentos' in data:
            classifier = DocumentClassifier()
            for doc_data in data['documentos']:
                documento = Documento(
                    tramite_id=tramite.id,
                    tipo_documento=doc_data.get('tipo_documento', '').strip(),
                    nombre_archivo=doc_data.get('nombre_archivo', '').strip(),
                    contenido=doc_data.get('contenido', '')
                )
                
                clasificacion, puntuacion = classifier.predict(documento.contenido)
                documento.clasificacion_ml = clasificacion
                documento.puntuacion_ml = puntuacion
                
                db.session.add(documento)
            
            db.session.commit()
        
        notification_system.enviar_notificacion_tramite(
            ciudadano.email,
            tramite.id,
            tramite.tipo_tramite,
            'creado'
        )
        
        alerta = Alerta(
            tramite_id=tramite.id,
            tipo_alerta='creacion',
            mensaje=f'Trámite {tramite.tipo_tramite} creado exitosamente con prioridad {prioridad}',
            canal='email'
        )
        db.session.add(alerta)
        db.session.commit()

        registrar_auditoria(current_user.id, 'crear_tramite_admin', 'tramites', tramite.id, f'Tramite creado por admin {current_user.email}')
        
        return jsonify({
            'mensaje': 'Trámite creado exitosamente',
            'tramite': tramite.to_dict(),
            'prioridad_ml': prioridad,
            'confianza_ml': confianza
        }), 201

    @app.route('/api/tramites', methods=['GET'])
    @login_required
    @admin_required
    def listar_tramites():
        tramites = Tramite.query.all()
        return jsonify([tramite.to_dict() for tramite in tramites])

    @app.route('/api/tramites/<int:tramite_id>', methods=['GET'])
    @login_required
    @admin_required
    def obtener_tramite(tramite_id):
        tramite = Tramite.query.get_or_404(tramite_id)
        tramite_dict = tramite.to_dict()
        tramite_dict['documentos'] = [doc.to_dict() for doc in tramite.documentos]
        tramite_dict['alertas'] = [alerta.to_dict() for alerta in tramite.alertas]
        tramite_dict['ciudadano'] = tramite.ciudadano.to_dict()
        return jsonify(tramite_dict)

    @app.route('/api/tramites/<int:tramite_id>/estado', methods=['PUT'])
    @login_required
    @admin_required
    def actualizar_estado_tramite(tramite_id):
        data = request.json or {}
        nuevo_estado = data.get('estado', '').strip()
        tramite = Tramite.query.get_or_404(tramite_id)
        
        if nuevo_estado not in [estado.value for estado in EstadoTramite]:
            return jsonify({'error': 'Estado inválido'}), 400
        
        estado_anterior = tramite.estado
        tramite.estado = nuevo_estado
        tramite.observaciones = data.get('observaciones', tramite.observaciones)
        
        if nuevo_estado == EstadoTramite.COMPLETADO.value:
            tramite.fecha_completado = datetime.utcnow()
        
        db.session.commit()
        
        notification_system.enviar_notificacion_tramite(
            tramite.ciudadano.email,
            tramite.id,
            tramite.tipo_tramite,
            'actualizado',
            estado_anterior,
            nuevo_estado
        )
        
        alerta = Alerta(
            tramite_id=tramite.id,
            tipo_alerta='actualizacion_estado',
            mensaje=f'Estado del trámite actualizado de {estado_anterior} a {nuevo_estado}',
            canal='email'
        )
        db.session.add(alerta)
        db.session.commit()

        registrar_auditoria(current_user.id, 'actualizar_estado', 'tramites', tramite.id, f'Estado actualizado de {estado_anterior} a {nuevo_estado}')
        
        return jsonify({'mensaje': 'Estado actualizado', 'tramite': tramite.to_dict()})

    @app.route('/api/tramites/prioritarios', methods=['GET'])
    @login_required
    @admin_required
    def listar_tramites_prioritarios():
        tramites = Tramite.query.order_by(
            db.case(
                (Tramite.prioridad == Prioridad.URGENTE.value, 1),
                (Tramite.prioridad == Prioridad.ALTA.value, 2),
                (Tramite.prioridad == Prioridad.MEDIA.value, 3),
                (Tramite.prioridad == Prioridad.BAJA.value, 4),
            ),
            Tramite.fecha_solicitud
        ).all()
        
        return jsonify([tramite.to_dict() for tramite in tramites])

    @app.route('/api/tramites/estadisticas', methods=['GET'])
    @login_required
    @admin_required
    def obtener_estadisticas():
        total_tramites = Tramite.query.count()
        tramites_por_estado = {}
        for estado in EstadoTramite:
            count = Tramite.query.filter_by(estado=estado.value).count()
            tramites_por_estado[estado.value] = count
        
        tramites_por_prioridad = {}
        for prioridad in Prioridad:
            count = Tramite.query.filter_by(prioridad=prioridad.value).count()
            tramites_por_prioridad[prioridad.value] = count
        
        return jsonify({
            'total_tramites': total_tramites,
            'tramites_por_estado': tramites_por_estado,
            'tramites_por_prioridad': tramites_por_prioridad
        })

    @app.route('/api/documentos/clasificar', methods=['POST'])
    @login_required
    def clasificar_documento():
        data = request.json or {}
        contenido = data.get('contenido', '')
        
        if not contenido:
            return jsonify({'error': 'El contenido del documento es obligatorio'}), 400
        
        classifier = DocumentClassifier()
        clasificacion, puntuacion = classifier.predict(contenido)
        
        return jsonify({
            'clasificacion': clasificacion,
            'puntuacion': puntuacion
        })

    @app.route('/api/alertas', methods=['GET'])
    @login_required
    @admin_required
    def listar_alertas():
        alertas = Alerta.query.order_by(Alerta.fecha_envio.desc()).limit(50).all()
        return jsonify([alerta.to_dict() for alerta in alertas])

    @app.route('/api/tramites/<int:tramite_id>/alertas', methods=['GET'])
    @login_required
    @admin_required
    def listar_alertas_tramite(tramite_id):
        alertas = Alerta.query.filter_by(tramite_id=tramite_id).order_by(Alerta.fecha_envio.desc()).all()
        return jsonify([alerta.to_dict() for alerta in alertas])

    @app.route('/api/auditoria', methods=['GET'])
    @login_required
    @admin_required
    def listar_auditoria():
        registros = AuditLog.query.order_by(AuditLog.fecha.desc()).limit(100).all()
        return jsonify([registro.to_dict() for registro in registros])

    @app.route('/api/ml/entrenar', methods=['POST'])
    @login_required
    @admin_required
    def entrenar_modelos():
        data = request.json or {}
        
        if 'documentos' in data:
            classifier = DocumentClassifier()
            classifier.train(data['documentos']['textos'], data['documentos']['labels'])
        
        if 'prioridades' in data:
            predictor = PriorityPredictor()
            import pandas as pd
            df = pd.DataFrame(data['prioridades']['features'])
            predictor.train(df, data['prioridades']['labels'])
        
        registrar_auditoria(current_user.id, 'entrenar_modelos', 'modelos', None, 'Entrenamiento manual de modelos ML')
        return jsonify({'mensaje': 'Modelos entrenados exitosamente'})
