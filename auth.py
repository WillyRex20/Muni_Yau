from flask import redirect, url_for, session, request
from flask_login import current_user, login_user, logout_user
from config import db
from models import Usuario, Ciudadano, Rol
import requests
import os

def init_login_manager(app):
    from config import login_manager
    from models import Usuario
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

def get_google_auth_url():
    """Genera la URL de autenticación de Google"""
    from flask import current_app
    client_id = current_app.config['GOOGLE_CLIENT_ID']
    redirect_uri = 'http://localhost:5000/auth/callback'
    scope = 'openid email profile'
    
    auth_url = (
        f'https://accounts.google.com/o/oauth2/v2/auth?'
        f'client_id={client_id}&'
        f'redirect_uri={redirect_uri}&'
        f'scope={scope}&'
        f'response_type=code'
    )
    return auth_url

def handle_google_callback(code):
    """Maneja el callback de Google OAuth"""
    from flask import current_app
    
    client_id = current_app.config['GOOGLE_CLIENT_ID']
    client_secret = current_app.config['GOOGLE_CLIENT_SECRET']
    redirect_uri = 'http://localhost:5000/auth/callback'
    
    # Intercambiar el código por un token de acceso
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    token_response = requests.post(token_url, data=token_data)
    token_response_data = token_response.json()
    
    if 'error' in token_response_data:
        return None, token_response_data.get('error_description', 'Error al obtener token')
    
    access_token = token_response_data.get('access_token')
    
    # Obtener información del usuario
    user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
    headers = {'Authorization': f'Bearer {access_token}'}
    user_info_response = requests.get(user_info_url, headers=headers)
    user_info = user_info_response.json()
    
    if 'error' in user_info:
        return None, user_info.get('error', 'Error al obtener información del usuario')
    
    # Buscar o crear usuario
    user = Usuario.query.filter_by(google_id=user_info['id']).first()
    
    if not user:
        # Verificar si existe usuario con el mismo email
        user = Usuario.query.filter_by(email=user_info['email']).first()
        
        if not user:
            # Crear nuevo usuario
            user = Usuario(
                email=user_info['email'],
                nombre=user_info['name'],
                google_id=user_info['id'],
                foto_perfil=user_info.get('picture'),
                rol=Rol.CIUDADANO.value  # Por defecto es ciudadano
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Actualizar usuario existente con google_id
            user.google_id = user_info['id']
            user.foto_perfil = user_info.get('picture')
            db.session.commit()
    
    return user, None

def create_admin_user(email, nombre):
    """Crea un usuario administrador"""
    user = Usuario.query.filter_by(email=email).first()
    if not user:
        user = Usuario(
            email=email,
            nombre=nombre,
            rol=Rol.ADMINISTRADOR.value,
            activo=True
        )
        db.session.add(user)
        db.session.commit()
    return user
