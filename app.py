from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from flask_login import login_required, current_user, login_user, logout_user
from config import db, create_app
from models import Tramite, Ciudadano, Documento, Alerta, Usuario
from ml_models import DocumentClassifier, PriorityPredictor
import routes
import auth

app = create_app()
CORS(app)

# Initialize login manager
auth.init_login_manager(app)

# Register routes
routes.register_routes(app)

# Initialize ML models
document_classifier = DocumentClassifier()
priority_predictor = PriorityPredictor()

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('citizen_dashboard'))
    return redirect(url_for('login'))

@app.route('/auth/callback')
def auth_callback():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('login'))
    
    user, error = auth.handle_google_callback(code)
    if error:
        return f"Error de autenticación: {error}", 400
    
    login_user(user)
    
    if user.is_admin():
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('citizen_dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        return redirect(url_for('citizen_dashboard'))
    return render_template('admin_dashboard.html')

@app.route('/citizen/dashboard')
@login_required
def citizen_dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    return render_template('citizen_dashboard.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Crear usuario administrador por defecto si no existe
        admin = Usuario.query.filter_by(email='admin@muniyau.gob.pe').first()
        if not admin:
            admin = Usuario(
                email='admin@muniyau.gob.pe',
                nombre='Administrador Municipalidad',
                rol='administrador'
            )
            admin.set_password('123456789')
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True, host='0.0.0.0', port=5000)
