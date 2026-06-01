from flask import request, jsonify, redirect, url_for, render_template
from flask_login import login_required, current_user, login_user, logout_user
from config import db
from models import Ciudadano, Tramite, Documento, Alerta, EstadoTramite, Prioridad, Usuario, Rol
from ml_models import DocumentClassifier, PriorityPredictor
from notification_system import NotificationSystem
import auth
import json
from datetime import datetime

notification_system = NotificationSystem()

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
        data = request.json
        nombre = data.get('nombre')
        email = data.get('email')
        password = data.get('password')
        
        # Verificar si el usuario ya existe
        if Usuario.query.filter_by(email=email).first():
            return jsonify({'error': 'El email ya está registrado'}), 400
        
        # Crear nuevo usuario (ciudadano por defecto)
        user = Usuario(
            email=email,
            nombre=nombre,
            rol=Rol.CIUDADANO.value
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Crear registro de ciudadano
        ciudadano = Ciudadano(
            usuario_id=user.id,
            email=email
        )
        db.session.add(ciudadano)
        db.session.commit()
        
        # Iniciar sesión automáticamente
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
        
        ciudadano = Ciudadano.query.filter_by(usuario_id=current_user.id).first()
        if not ciudadano:
            ciudadano = Ciudadano(
                usuario_id=current_user.id,
                email=current_user.email
            )
            db.session.add(ciudadano)
            db.session.commit()
        
        data = request.json
        
        # Crear trámite
        tramite = Tramite(
            ciudadano_id=ciudadano.id,
            tipo_tramite=data['tipo_tramite'],
            descripcion=data.get('descripcion', ''),
            estado=EstadoTramite.PENDIENTE.value
        )
        
        # Predecir prioridad usando ML
        predictor = PriorityPredictor()
        tramite_data = {
            'tipo_tramite': data['tipo_tramite'],
            'descripcion': data.get('descripcion', ''),
            'num_documentos': len(data.get('documentos', []))
        }
        prioridad, confianza = predictor.predict(tramite_data)
        tramite.prioridad = prioridad
        
        db.session.add(tramite)
        db.session.commit()
        
        # Procesar documentos si existen
        if 'documentos' in data:
            classifier = DocumentClassifier()
            for doc_data in data['documentos']:
                documento = Documento(
                    tramite_id=tramite.id,
                    tipo_documento=doc_data['tipo_documento'],
                    nombre_archivo=doc_data['nombre_archivo'],
                    contenido=doc_data.get('contenido', '')
                )
                
                # Clasificar documento usando ML
                clasificacion, puntuacion = classifier.predict(doc_data.get('contenido', ''))
                documento.clasificacion_ml = clasificacion
                documento.puntuacion_ml = puntuacion
                
                db.session.add(documento)
            
            db.session.commit()
        
        # Enviar notificación al ciudadano
        notification_system.enviar_notificacion_tramite(
            ciudadano.email,
            tramite.id,
            tramite.tipo_tramite,
            'creado'
        )
        
        # Crear alerta en el sistema
        alerta = Alerta(
            tramite_id=tramite.id,
            tipo_alerta='creacion',
            mensaje=f'Trámite {tramite.tipo_tramite} creado por ${current_user.nombre} con prioridad {prioridad}',
            canal='email'
        )
        db.session.add(alerta)
        db.session.commit()
        
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
    def crear_ciudadano():
        data = request.json
        
        # Verificar si el ciudadano ya existe
        ciudadano_existente = Ciudadano.query.filter_by(dni=data['dni']).first()
        if ciudadano_existente:
            return jsonify({'error': 'El ciudadano ya existe'}), 400
        
        ciudadano = Ciudadano(
            dni=data['dni'],
            nombres=data['nombres'],
            apellidos=data['apellidos'],
            email=data['email'],
            telefono=data.get('telefono', ''),
            direccion=data.get('direccion', '')
        )
        
        db.session.add(ciudadano)
        db.session.commit()
        
        return jsonify({'mensaje': 'Ciudadano creado exitosamente', 'ciudadano': ciudadano.to_dict()}), 201

    @app.route('/api/ciudadanos/<int:ciudadano_id>', methods=['GET'])
    def obtener_ciudadano(ciudadano_id):
        ciudadano = Ciudadano.query.get_or_404(ciudadano_id)
        return jsonify(ciudadano.to_dict())

    @app.route('/api/ciudadanos', methods=['GET'])
    def listar_ciudadanos():
        ciudadanos = Ciudadano.query.all()
        return jsonify([c.to_dict() for c in ciudadanos])

    @app.route('/api/tramites', methods=['POST'])
    def crear_tramite():
        data = request.json
        
        # Verificar que el ciudadano existe
        ciudadano = Ciudadano.query.get_or_404(data['ciudadano_id'])
        
        # Crear trámite
        tramite = Tramite(
            ciudadano_id=data['ciudadano_id'],
            tipo_tramite=data['tipo_tramite'],
            descripcion=data.get('descripcion', ''),
            estado=EstadoTramite.PENDIENTE.value
        )
        
        # Predecir prioridad usando ML
        predictor = PriorityPredictor()
        tramite_data = {
            'tipo_tramite': data['tipo_tramite'],
            'descripcion': data.get('descripcion', ''),
            'num_documentos': len(data.get('documentos', []))
        }
        prioridad, confianza = predictor.predict(tramite_data)
        tramite.prioridad = prioridad
        
        db.session.add(tramite)
        db.session.commit()
        
        # Procesar documentos si existen
        if 'documentos' in data:
            classifier = DocumentClassifier()
            for doc_data in data['documentos']:
                documento = Documento(
                    tramite_id=tramite.id,
                    tipo_documento=doc_data['tipo_documento'],
                    nombre_archivo=doc_data['nombre_archivo'],
                    contenido=doc_data.get('contenido', '')
                )
                
                # Clasificar documento usando ML
                clasificacion, puntuacion = classifier.predict(doc_data.get('contenido', ''))
                documento.clasificacion_ml = clasificacion
                documento.puntuacion_ml = puntuacion
                
                db.session.add(documento)
            
            db.session.commit()
        
        # Enviar notificación al ciudadano
        notification_system.enviar_notificacion_tramite(
            ciudadano.email,
            tramite.id,
            tramite.tipo_tramite,
            'creado'
        )
        
        # Crear alerta en el sistema
        alerta = Alerta(
            tramite_id=tramite.id,
            tipo_alerta='creacion',
            mensaje=f'Trámite {tramite.tipo_tramite} creado exitosamente con prioridad {prioridad}',
            canal='email'
        )
        db.session.add(alerta)
        db.session.commit()
        
        return jsonify({
            'mensaje': 'Trámite creado exitosamente',
            'tramite': tramite.to_dict(),
            'prioridad_ml': prioridad,
            'confianza_ml': confianza
        }), 201

    @app.route('/api/tramites', methods=['GET'])
    def listar_tramites():
        tramites = Tramite.query.all()
        return jsonify([tramite.to_dict() for tramite in tramites])

    @app.route('/api/tramites/<int:tramite_id>', methods=['GET'])
    def obtener_tramite(tramite_id):
        tramite = Tramite.query.get_or_404(tramite_id)
        tramite_dict = tramite.to_dict()
        tramite_dict['documentos'] = [doc.to_dict() for doc in tramite.documentos]
        tramite_dict['alertas'] = [alerta.to_dict() for alerta in tramite.alertas]
        tramite_dict['ciudadano'] = tramite.ciudadano.to_dict()
        return jsonify(tramite_dict)

    @app.route('/api/tramites/<int:tramite_id>/estado', methods=['PUT'])
    def actualizar_estado_tramite(tramite_id):
        data = request.json
        tramite = Tramite.query.get_or_404(tramite_id)
        
        estado_anterior = tramite.estado
        tramite.estado = data['estado']
        tramite.observaciones = data.get('observaciones', tramite.observaciones)
        
        if data['estado'] == EstadoTramite.COMPLETADO.value:
            tramite.fecha_completado = datetime.utcnow()
        
        db.session.commit()
        
        # Enviar notificación de actualización
        notification_system.enviar_notificacion_tramite(
            tramite.ciudadano.email,
            tramite.id,
            tramite.tipo_tramite,
            'actualizado',
            estado_anterior,
            data['estado']
        )
        
        # Crear alerta
        alerta = Alerta(
            tramite_id=tramite.id,
            tipo_alerta='actualizacion_estado',
            mensaje=f'Estado del trámite actualizado de {estado_anterior} a {data["estado"]}',
            canal='email'
        )
        db.session.add(alerta)
        db.session.commit()
        
        return jsonify({'mensaje': 'Estado actualizado', 'tramite': tramite.to_dict()})

    @app.route('/api/tramites/prioritarios', methods=['GET'])
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
    def clasificar_documento():
        data = request.json
        classifier = DocumentClassifier()
        
        clasificacion, puntuacion = classifier.predict(data['contenido'])
        
        return jsonify({
            'clasificacion': clasificacion,
            'puntuacion': puntuacion
        })

    @app.route('/api/alertas', methods=['GET'])
    def listar_alertas():
        alertas = Alerta.query.order_by(Alerta.fecha_envio.desc()).limit(50).all()
        return jsonify([alerta.to_dict() for alerta in alertas])

    @app.route('/api/tramites/<int:tramite_id>/alertas', methods=['GET'])
    def listar_alertas_tramite(tramite_id):
        alertas = Alerta.query.filter_by(tramite_id=tramite_id).order_by(Alerta.fecha_envio.desc()).all()
        return jsonify([alerta.to_dict() for alerta in alertas])

    @app.route('/api/ml/entrenar', methods=['POST'])
    def entrenar_modelos():
        data = request.json
        
        # Entrenar clasificador de documentos
        if 'documentos' in data:
            classifier = DocumentClassifier()
            classifier.train(data['documentos']['textos'], data['documentos']['labels'])
        
        # Entrenar predictor de prioridad
        if 'prioridades' in data:
            predictor = PriorityPredictor()
            import pandas as pd
            df = pd.DataFrame(data['prioridades']['features'])
            predictor.train(df, data['prioridades']['labels'])
        
        return jsonify({'mensaje': 'Modelos entrenados exitosamente'})
