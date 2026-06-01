from config import db
from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class EstadoTramite(Enum):
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    COMPLETADO = "completado"
    RECHAZADO = "rechazado"

class Prioridad(Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"

class Rol(Enum):
    CIUDADANO = "ciudadano"
    ADMINISTRADOR = "administrador"

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255))
    google_id = db.Column(db.String(255), unique=True)
    rol = db.Column(db.String(20), default=Rol.CIUDADANO.value)
    foto_perfil = db.Column(db.String(255))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    
    # Relación con ciudadano (si es ciudadano)
    ciudadano = db.relationship('Ciudadano', backref='usuario', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.rol == Rol.ADMINISTRADOR.value
    
    def is_ciudadano(self):
        return self.rol == Rol.CIUDADANO.value
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'rol': self.rol,
            'foto_perfil': self.foto_perfil,
            'fecha_registro': self.fecha_registro.isoformat(),
            'activo': self.activo
        }

class Ciudadano(db.Model):
    __tablename__ = 'ciudadanos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    dni = db.Column(db.String(8), unique=True, nullable=True)
    nombres = db.Column(db.String(100), nullable=True)
    apellidos = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    tramites = db.relationship('Tramite', backref='ciudadano', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'dni': self.dni,
            'nombres': self.nombres,
            'apellidos': self.apellidos,
            'email': self.email,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'fecha_registro': self.fecha_registro.isoformat()
        }

class Tramite(db.Model):
    __tablename__ = 'tramites'
    
    id = db.Column(db.Integer, primary_key=True)
    ciudadano_id = db.Column(db.Integer, db.ForeignKey('ciudadanos.id'), nullable=False)
    tipo_tramite = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(20), default=EstadoTramite.PENDIENTE.value)
    prioridad = db.Column(db.String(20), default=Prioridad.MEDIA.value)
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fecha_completado = db.Column(db.DateTime)
    observaciones = db.Column(db.Text)
    
    documentos = db.relationship('Documento', backref='tramite', lazy=True)
    alertas = db.relationship('Alerta', backref='tramite', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ciudadano_id': self.ciudadano_id,
            'tipo_tramite': self.tipo_tramite,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'prioridad': self.prioridad,
            'fecha_solicitud': self.fecha_solicitud.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat(),
            'fecha_completado': self.fecha_completado.isoformat() if self.fecha_completado else None,
            'observaciones': self.observaciones
        }

class Documento(db.Model):
    __tablename__ = 'documentos'
    
    id = db.Column(db.Integer, primary_key=True)
    tramite_id = db.Column(db.Integer, db.ForeignKey('tramites.id'), nullable=False)
    tipo_documento = db.Column(db.String(100), nullable=False)
    nombre_archivo = db.Column(db.String(255), nullable=False)
    contenido = db.Column(db.Text)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    clasificacion_ml = db.Column(db.String(50))
    puntuacion_ml = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tramite_id': self.tramite_id,
            'tipo_documento': self.tipo_documento,
            'nombre_archivo': self.nombre_archivo,
            'contenido': self.contenido,
            'fecha_subida': self.fecha_subida.isoformat(),
            'clasificacion_ml': self.clasificacion_ml,
            'puntuacion_ml': self.puntuacion_ml
        }

class Alerta(db.Model):
    __tablename__ = 'alertas'
    
    id = db.Column(db.Integer, primary_key=True)
    tramite_id = db.Column(db.Integer, db.ForeignKey('tramites.id'), nullable=False)
    tipo_alerta = db.Column(db.String(50), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    estado_envio = db.Column(db.String(20), default='pendiente')
    canal = db.Column(db.String(20), default='email')
    
    def to_dict(self):
        return {
            'id': self.id,
            'tramite_id': self.tramite_id,
            'tipo_alerta': self.tipo_alerta,
            'mensaje': self.mensaje,
            'fecha_envio': self.fecha_envio.isoformat(),
            'estado_envio': self.estado_envio,
            'canal': self.canal
        }
