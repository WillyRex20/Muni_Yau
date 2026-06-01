# Sistema de Gestión Documental - Municipalidad de Yau

Sistema automatizado de gestión documental y selección de currículos mediante Machine Learning para la Municipalidad Provincial de Yau.

## Características

### 1. Gestión de Trámites con Machine Learning
- **Clasificación Automática de Documentos**: Utiliza algoritmos de ML para clasificar automáticamente los documentos adjuntos (DNI, Curriculum, Certificados, etc.)
- **Predictor de Prioridad**: Asigna prioridad a los trámites basándose en análisis de contenido y reglas de negocio (Urgente, Alta, Media, Baja)
- **Reducción de Errores**: Minimiza errores humanos en la clasificación y procesamiento de documentos

### 2. Sistema de Alertas y Notificaciones
- **Notificaciones en Tiempo Real**: Los ciudadanos reciben notificaciones automáticas sobre el estado de sus trámites
- **Alertas por Email**: Sistema de envío de correos electrónicos para actualizar a los ciudadanos
- **Historial de Alertas**: Registro completo de todas las notificaciones enviadas

### 3. Dashboard y Estadísticas
- **Estadísticas en Tiempo Real**: Visualización de métricas de trámites por estado y prioridad
- **Monitoreo de ML**: Indicadores del estado de los modelos de Machine Learning
- **Lista de Trámites Prioritarios**: Vista ordenada por prioridad asignada por ML

### 4. Protección de Datos y Transparencia
- **Cumplimiento de Normas**: Sistema diseñado respetando leyes de protección de datos
- **Transparencia**: Los ciudadanos pueden hacer seguimiento de sus trámites
- **Seguridad**: Almacenamiento seguro de información personal

## Tecnologías Utilizadas

### Backend (Python)
- **Flask**: Framework web para la API REST
- **SQLAlchemy**: ORM para gestión de base de datos
- **Scikit-learn**: Biblioteca de Machine Learning
- **Pandas/NumPy**: Procesamiento de datos
- **SMTPLIB**: Sistema de notificaciones por email

### Frontend (HTML/CSS/JavaScript)
- **HTML5**: Estructura de la interfaz
- **Bootstrap 5**: Framework CSS para diseño responsivo
- **JavaScript Vanilla**: Lógica del frontend
- **Font Awesome**: Iconos

### Machine Learning
- **Random Forest Classifier**: Para clasificación de documentos
- **TF-IDF Vectorizer**: Para procesamiento de texto
- **Label Encoder**: Para codificación de etiquetas

## Instalación

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
cd Muni_Yau
```

2. **Crear entorno virtual (opcional pero recomendado)**
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
Editar el archivo `.env` con sus configuraciones:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///municipalidad.db
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

5. **Ejecutar la aplicación**
```bash
python app.py
```

6. **Acceder a la aplicación**
Abrir el navegador en: `http://localhost:5000`

## Uso del Sistema

### 1. Registrar Ciudadano
- Navegar a la sección "Nuevo Trámite"
- Completar el formulario de registro de ciudadano
- Incluir DNI, nombres, apellidos, email y teléfono

### 2. Crear Trámite
- Después de registrar el ciudadano, crear un trámite
- Seleccionar el tipo de trámite
- Agregar descripción
- Adjuntar documentos (el sistema los clasificará automáticamente con ML)
- El sistema asignará prioridad automáticamente usando ML

### 3. Monitorear Trámites
- Ver la lista de todos los trámites
- Consultar trámites prioritarios (ordenados por ML)
- Ver detalles de cada trámite incluyendo clasificación ML de documentos

### 4. Actualizar Estados
- Cambiar el estado de los trámites (Pendiente → En Proceso → Completado)
- Agregar observaciones
- El sistema enviará notificaciones automáticas al ciudadano

### 5. Ver Alertas
- Consultar el historial de alertas y notificaciones
- Verificar el estado de envío de notificaciones

## Estructura del Proyecto

```
Muni_Yau/
├── app.py                      # Aplicación principal Flask
├── models.py                   # Modelos de base de datos
├── routes.py                   # Rutas de la API
├── ml_models.py                # Modelos de Machine Learning
├── notification_system.py      # Sistema de notificaciones
├── requirements.txt            # Dependencias de Python
├── .env                        # Variables de entorno
├── templates/
│   └── index.html             # Interfaz principal
├── static/
│   ├── js/
│   │   └── app.js             # Lógica del frontend
│   └── css/
│       └── style.css          # Estilos personalizados
├── models/                     # Modelos ML entrenados (se crea automáticamente)
├── municipalidad.db            # Base de datos SQLite (se crea automáticamente)
└── README.md                   # Este archivo
```

## API Endpoints

### Ciudadanos
- `POST /api/ciudadanos` - Crear nuevo ciudadano
- `GET /api/ciudadanos/<id>` - Obtener ciudadano por ID

### Trámites
- `POST /api/tramites` - Crear nuevo trámite
- `GET /api/tramites` - Listar todos los trámites
- `GET /api/tramites/<id>` - Obtener detalle de trámite
- `PUT /api/tramites/<id>/estado` - Actualizar estado de trámite
- `GET /api/tramites/prioritarios` - Listar trámites ordenados por prioridad ML
- `GET /api/tramites/estadisticas` - Obtener estadísticas

### Documentos
- `POST /api/documentos/clasificar` - Clasificar documento con ML

### Alertas
- `GET /api/alertas` - Listar todas las alertas
- `GET /api/tramites/<id>/alertas` - Listar alertas de un trámite

### Machine Learning
- `POST /api/ml/entrenar` - Entrenar modelos con datos personalizados

## Entrenamiento de Modelos ML

El sistema incluye modelos pre-entrenados con reglas básicas, pero puede entrenarse con datos propios:

### Entrenar Clasificador de Documentos
```bash
curl -X POST http://localhost:5000/api/ml/entrenar \
  -H "Content-Type: application/json" \
  -d '{
    "documentos": {
      "textos": ["texto del documento 1", "texto del documento 2"],
      "labels": ["DNI", "Curriculum"]
    }
  }'
```

### Entrenar Predictor de Prioridad
```bash
curl -X POST http://localhost:5000/api/ml/entrenar \
  -H "Content-Type: application/json" \
  -d '{
    "prioridades": {
      "features": [[10, 50, 1, 2], [15, 100, 0, 3]],
      "labels": ["alta", "media"]
    }
  }'
```

## Seguridad y Protección de Datos

- **Encriptación**: Las contraseñas de email se almacenan en variables de entorno
- **Validación**: Validación de datos en backend y frontend
- **Transparencia**: Los ciudadanos pueden ver el estado de sus trámites
- **Cumplimiento**: Sistema diseñado para cumplir con normativas de protección de datos

## Escalabilidad

El sistema es escalable y puede adaptarse a:
- Infraestructura existente de la municipalidad
- Flujos de trabajo establecidos
- Incremento en el volumen de trámites
- Integración con otros sistemas

## Soporte

Para preguntas o problemas, contactar al equipo de desarrollo.

## Licencia

Este proyecto fue desarrollado como trabajo final para el curso de Desarrollo de Aplicaciones con Machine Learning.
