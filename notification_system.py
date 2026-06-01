import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationSystem:
    def __init__(self):
        self.smtp_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_PORT', 587))
        self.smtp_user = os.getenv('EMAIL_USER', '')
        self.smtp_password = os.getenv('EMAIL_PASSWORD', '')
    
    def enviar_correo(self, to_email, subject, body):
        """Envía un correo electrónico"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f'Correo enviado exitosamente a {to_email}')
            return True
        except Exception as e:
            logger.error(f'Error al enviar correo: {str(e)}')
            return False
    
    def enviar_notificacion_tramite(self, email, tramite_id, tipo_tramite, accion, estado_anterior=None, estado_nuevo=None):
        """Envía notificación sobre el estado de un trámite"""
        subject = f'Actualización de Trámite #{tramite_id} - Municipalidad de Yau'
        
        if accion == 'creado':
            body = f'''
Estimado ciudadano,

Le informamos que su trámite ha sido creado exitosamente:

- Tipo de trámite: {tipo_tramite}
- Número de trámite: #{tramite_id}
- Estado: Pendiente

Puede hacer seguimiento de su trámite a través de nuestro portal web.

Atentamente,
Municipalidad Provincial de Yau
'''
        elif accion == 'actualizado':
            body = f'''
Estimado ciudadano,

Le informamos que hay una actualización en su trámite:

- Tipo de trámite: {tipo_tramite}
- Número de trámite: #{tramite_id}
- Estado anterior: {estado_anterior}
- Nuevo estado: {estado_nuevo}

Puede hacer seguimiento de su trámite a través de nuestro portal web.

Atentamente,
Municipalidad Provincial de Yau
'''
        
        return self.enviar_correo(email, subject, body)
    
    def enviar_alerta_critica(self, email, mensaje):
        """Envía una alerta crítica"""
        subject = 'ALERTA CRÍTICA - Municipalidad de Yau'
        body = f'''
Estimado ciudadano,

{mensaje}

Por favor, contacte a la municipalidad para más información.

Atentamente,
Municipalidad Provincial de Yau
'''
        return self.enviar_correo(email, subject, body)
