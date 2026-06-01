# Instrucciones para Ejecutar el Sistema

## Pasos para Iniciar el Sistema

### 1. Abrir Terminal
- Presiona `Win + R` y escribe `cmd` o abre PowerShell
- Navega al directorio del proyecto:
```bash
cd C:\Users\Usuario.DESKTOP-83G8U4A\Documents\Muni_Yau
```

### 2. Activar Entorno Virtual (Opcional pero Recomendado)
Si creaste un entorno virtual:
```bash
venv\Scripts\activate
```

### 3. Instalar Dependencias (Solo la primera vez)
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Edita el archivo `.env` y configura:
- `SECRET_KEY`: Clave secreta para la aplicación
- `GOOGLE_CLIENT_ID`: ID de cliente de Google OAuth (opcional)
- `GOOGLE_CLIENT_SECRET`: Secreto de cliente de Google OAuth (opcional)

### 5. Ejecutar la Aplicación
```bash
python app.py
```

### 6. Acceder al Sistema
Abre tu navegador y ve a: http://localhost:5000

## Cómo Detener el Sistema

### Desde la Terminal
Presiona `Ctrl + C` en la terminal donde está ejecutándose el servidor

### Si el servidor está en segundo plano
```bash
taskkill /F /IM python.exe
```

## Estructura del Proyecto

```
Muni_Yau/
├── app.py                      # Aplicación principal
├── config.py                   # Configuración de la aplicación
├── models.py                   # Modelos de base de datos
├── routes.py                   # Rutas de la API
├── ml_models.py                # Modelos de Machine Learning
├── notification_system.py      # Sistema de notificaciones
├── auth.py                     # Sistema de autenticación
├── requirements.txt            # Dependencias de Python
├── .env                        # Variables de entorno
├── templates/                  # Plantillas HTML
│   ├── login.html
│   ├── admin_dashboard.html
│   └── citizen_dashboard.html
├── static/                     # Archivos estáticos
│   ├── js/
│   │   ├── app.js
│   │   ├── admin.js
│   │   └── citizen.js
│   └── css/
│       └── style.css
├── models/                     # Modelos ML entrenados (se crea automáticamente)
└── municipalidad.db            # Base de datos SQLite (se crea automáticamente)
```

## Credenciales de Prueba

### Administrador
- **Email**: admin@muniyau.gob.pe
- **Acceso**: Google OAuth (debe configurarse primero)
- **Rol**: Administrador

### Ciudadanos
- **Acceso**: Google OAuth con cualquier cuenta de Gmail
- **Rol**: Ciudadano (por defecto)

## Configuración de Google OAuth (Opcional)

Si quieres usar el login con Google:

1. Ve a https://console.cloud.google.com
2. Crea un nuevo proyecto
3. Habilita Google+ API
4. Ve a Credentials → Create Credentials → OAuth client ID
5. Tipo: Web application
6. Authorized redirect URIs: `http://localhost:5000/auth/callback`
7. Copia Client ID y Client Secret
8. Actualiza el archivo `.env`:
```env
GOOGLE_CLIENT_ID=tu-client-id
GOOGLE_CLIENT_SECRET=tu-client-secret
```

## Solución de Problemas

### Error: ModuleNotFoundError
```bash
pip install -r requirements.txt
```

### Error: Database locked
Elimina el archivo `municipalidad.db` y reinicia la aplicación

### Puerto 5000 en uso
Cambia el puerto en `app.py` línea 92:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Usa puerto 5001
```

## Características del Sistema

### Para Ciudadanos
- Login con Google OAuth
- Ver sus trámites
- Crear nuevos trámites
- Ver perfil
- Recibir notificaciones por email

### Para Administradores
- Ver todos los trámites
- Gestionar trámites (cambiar estados)
- Ver trámites prioritarios
- Ver ciudadanos registrados
- Dashboard con estadísticas
- Notificaciones en tiempo real

### Machine Learning
- Clasificación automática de documentos
- Asignación inteligente de prioridad
- Reducción de errores en procesamiento
