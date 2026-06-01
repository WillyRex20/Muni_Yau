const API_BASE = '/api';

// Funciones para mostrar alertas de Bootstrap
function showSuccessToast(message) {
    document.getElementById('successToastBody').textContent = message;
    const toast = new bootstrap.Toast(document.getElementById('successToast'));
    toast.show();
}

function showErrorToast(message) {
    document.getElementById('errorToastBody').textContent = message;
    const toast = new bootstrap.Toast(document.getElementById('errorToast'));
    toast.show();
}

// Show/Hide sections
function showSection(sectionName) {
    document.querySelectorAll('[id$="-section"]').forEach(section => {
        section.classList.add('hidden');
    });
    
    document.getElementById(`${sectionName}-section`).classList.remove('hidden');
    
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    event.target.closest('.nav-link').classList.add('active');
    
    switch(sectionName) {
        case 'dashboard':
            cargarEstadisticas();
            cargarTramitesRecientes();
            break;
        case 'todos-tramites':
            cargarTodosTramites();
            break;
        case 'prioritarios':
            cargarTramitesPrioritarios();
            break;
        case 'ciudadanos':
            cargarCiudadanos();
            break;
        case 'notificaciones':
            cargarNotificaciones();
            break;
    }
}

// Load statistics
async function cargarEstadisticas() {
    try {
        const response = await fetch(`${API_BASE}/tramites/estadisticas`);
        const data = await response.json();
        
        document.getElementById('total-tramites').textContent = data.total_tramites;
        document.getElementById('tramites-pendientes').textContent = data.tramites_por_estado.pendiente || 0;
        
        // Cargar trámites de hoy
        const hoy = new Date().toISOString().split('T')[0];
        const tramitesResponse = await fetch(`${API_BASE}/tramites`);
        const tramites = await tramitesResponse.json();
        const tramitesHoy = tramites.filter(t => t.fecha_solicitud.startsWith(hoy)).length;
        document.getElementById('tramites-hoy').textContent = tramitesHoy;
        
        // Cargar total ciudadanos
        const ciudadanosResponse = await fetch(`${API_BASE}/ciudadanos`);
        const ciudadanos = await ciudadanosResponse.json();
        document.getElementById('total-ciudadanos').textContent = ciudadanos.length;
        
        // Actualizar contador de notificaciones
        const alertasResponse = await fetch(`${API_BASE}/alertas`);
        const alertas = await alertasResponse.json();
        document.getElementById('notification-count').textContent = alertas.length;
    } catch (error) {
        console.error('Error al cargar estadísticas:', error);
    }
}

// Load recent tramites
async function cargarTramitesRecientes() {
    try {
        const response = await fetch(`${API_BASE}/tramites`);
        const tramites = await response.json();
        
        const tbody = document.getElementById('recent-tramites-tbody');
        tbody.innerHTML = '';
        
        // Mostrar los últimos 5 trámites
        tramites.slice(-5).reverse().forEach(tramite => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${tramite.id}</td>
                <td>${tramite.tipo_tramite}</td>
                <td>${tramite.ciudadano_id}</td>
                <td><span class="priority-badge priority-${tramite.prioridad}">${tramite.prioridad}</span></td>
                <td><span class="status-badge status-${tramite.estado}">${tramite.estado.replace('_', ' ')}</span></td>
                <td>${new Date(tramite.fecha_solicitud).toLocaleDateString()}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error al cargar trámites recientes:', error);
    }
}

// Load all tramites
async function cargarTodosTramites() {
    try {
        const response = await fetch(`${API_BASE}/tramites`);
        const tramites = await response.json();
        
        const tbody = document.getElementById('all-tramites-tbody');
        tbody.innerHTML = '';
        
        tramites.forEach(tramite => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${tramite.id}</td>
                <td>${tramite.tipo_tramite}</td>
                <td>${tramite.ciudadano_id}</td>
                <td><span class="status-badge status-${tramite.estado}">${tramite.estado.replace('_', ' ')}</span></td>
                <td><span class="priority-badge priority-${tramite.prioridad}">${tramite.prioridad}</span></td>
                <td>${new Date(tramite.fecha_solicitud).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="verDetalleTramite(${tramite.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error al cargar trámites:', error);
    }
}

// Load prioritized tramites
async function cargarTramitesPrioritarios() {
    try {
        const response = await fetch(`${API_BASE}/tramites/prioritarios`);
        const tramites = await response.json();
        
        const tbody = document.getElementById('prioritarios-tbody');
        tbody.innerHTML = '';
        
        tramites.forEach(tramite => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${tramite.id}</td>
                <td>${tramite.tipo_tramite}</td>
                <td>${tramite.ciudadano_id}</td>
                <td><span class="priority-badge priority-${tramite.prioridad}">${tramite.prioridad}</span></td>
                <td><span class="status-badge status-${tramite.estado}">${tramite.estado.replace('_', ' ')}</span></td>
                <td>${new Date(tramite.fecha_solicitud).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="verDetalleTramite(${tramite.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error al cargar trámites prioritarios:', error);
    }
}

// Load citizens
async function cargarCiudadanos() {
    try {
        const response = await fetch(`${API_BASE}/ciudadanos`);
        const ciudadanos = await response.json();
        
        const tbody = document.getElementById('ciudadanos-tbody');
        tbody.innerHTML = '';
        
        ciudadanos.forEach(ciudadano => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${ciudadano.id}</td>
                <td>${ciudadano.nombres} ${ciudadano.apellidos}</td>
                <td>${ciudadano.email}</td>
                <td>${ciudadano.dni || '-'}</td>
                <td>-</td>
                <td>${new Date(ciudadano.fecha_registro).toLocaleDateString()}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error al cargar ciudadanos:', error);
    }
}

// Load notifications
async function cargarNotificaciones() {
    try {
        const response = await fetch(`${API_BASE}/alertas`);
        const alertas = await response.json();
        
        const container = document.getElementById('notificaciones-container');
        container.innerHTML = '';
        
        if (alertas.length === 0) {
            container.innerHTML = '<p class="text-muted">No hay notificaciones recientes.</p>';
            return;
        }
        
        alertas.forEach(alerta => {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert-item';
            alertDiv.style.cssText = 'padding: 15px; border-left: 4px solid var(--primary-color); background-color: #ebf8ff; margin-bottom: 10px; border-radius: 4px;';
            alertDiv.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${alerta.tipo_alerta}</strong>
                        <p class="mb-0">${alerta.mensaje}</p>
                    </div>
                    <small class="text-muted">${new Date(alerta.fecha_envio).toLocaleString()}</small>
                </div>
            `;
            container.appendChild(alertDiv);
        });
    } catch (error) {
        console.error('Error al cargar notificaciones:', error);
    }
}

// View tramite detail
async function verDetalleTramite(tramiteId) {
    try {
        const response = await fetch(`${API_BASE}/tramites/${tramiteId}`);
        const tramite = await response.json();
        
        const modalBody = document.getElementById('tramite-modal-body');
        
        let documentosHtml = '';
        if (tramite.documentos && tramite.documentos.length > 0) {
            documentosHtml = tramite.documentos.map(doc => `
                <div class="card mb-2">
                    <div class="card-body">
                        <h6>${doc.tipo_documento}</h6>
                        <p class="mb-0 small">${doc.nombre_archivo}</p>
                        ${doc.clasificacion_ml ? `
                            <span class="ml-indicator mt-2">
                                <i class="fas fa-robot me-1"></i>ML: ${doc.clasificacion_ml} (${(doc.puntuacion_ml * 100).toFixed(1)}%)
                            </span>
                        ` : ''}
                    </div>
                </div>
            `).join('');
        } else {
            documentosHtml = '<p class="text-muted">No hay documentos adjuntos.</p>';
        }
        
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Información del Trámite</h6>
                    <table class="table table-sm">
                        <tr><td><strong>ID:</strong></td><td>${tramite.id}</td></tr>
                        <tr><td><strong>Tipo:</strong></td><td>${tramite.tipo_tramite}</td></tr>
                        <tr><td><strong>Estado:</strong></td><td><span class="status-badge status-${tramite.estado}">${tramite.estado.replace('_', ' ')}</span></td></tr>
                        <tr><td><strong>Prioridad ML:</strong></td><td><span class="priority-badge priority-${tramite.prioridad}">${tramite.prioridad}</span></td></tr>
                        <tr><td><strong>Fecha Solicitud:</strong></td><td>${new Date(tramite.fecha_solicitud).toLocaleString()}</td></tr>
                        <tr><td><strong>Última Actualización:</strong></td><td>${new Date(tramite.fecha_actualizacion).toLocaleString()}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Información del Ciudadano</h6>
                    ${tramite.ciudadano ? `
                        <table class="table table-sm">
                            <tr><td><strong>DNI:</strong></td><td>${tramite.ciudadano.dni || '-'}</td></tr>
                            <tr><td><strong>Nombre:</strong></td><td>${tramite.ciudadano.nombres || '-'} ${tramite.ciudadano.apellidos || '-'}</td></tr>
                            <tr><td><strong>Email:</strong></td><td>${tramite.ciudadano.email}</td></tr>
                            <tr><td><strong>Teléfono:</strong></td><td>${tramite.ciudadano.telefono || 'N/A'}</td></tr>
                        </table>
                    ` : '<p class="text-muted">Información no disponible</p>'}
                </div>
            </div>
            <hr>
            <h6>Descripción</h6>
            <p>${tramite.descripcion || 'Sin descripción'}</p>
            <hr>
            <h6>Documentos</h6>
            ${documentosHtml}
            <hr>
            <h6>Actualizar Estado</h6>
            <div class="mb-3">
                <select class="form-select" id="nuevo-estado">
                    <option value="pendiente" ${tramite.estado === 'pendiente' ? 'selected' : ''}>Pendiente</option>
                    <option value="en_proceso" ${tramite.estado === 'en_proceso' ? 'selected' : ''}>En Proceso</option>
                    <option value="completado" ${tramite.estado === 'completado' ? 'selected' : ''}>Completado</option>
                    <option value="rechazado" ${tramite.estado === 'rechazado' ? 'selected' : ''}>Rechazado</option>
                </select>
            </div>
            <div class="mb-3">
                <textarea class="form-control" id="observaciones" placeholder="Observaciones..." rows="2">${tramite.observaciones || ''}</textarea>
            </div>
            <button class="btn btn-primary" onclick="actualizarEstadoTramite(${tramite.id})">
                <i class="fas fa-save me-2"></i>Actualizar Estado
            </button>
        `;
        
        const modal = new bootstrap.Modal(document.getElementById('tramiteModal'));
        modal.show();
    } catch (error) {
        console.error('Error al cargar detalle del trámite:', error);
        showErrorToast('Error al cargar detalle del trámite');
    }
}

// Update tramite status
async function actualizarEstadoTramite(tramiteId) {
    const nuevoEstado = document.getElementById('nuevo-estado').value;
    const observaciones = document.getElementById('observaciones').value;
    
    try {
        const response = await fetch(`${API_BASE}/tramites/${tramiteId}/estado`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                estado: nuevoEstado,
                observaciones: observaciones
            })
        });
        
        if (response.ok) {
            showSuccessToast('Estado actualizado exitosamente');
            const modal = bootstrap.Modal.getInstance(document.getElementById('tramiteModal'));
            modal.hide();
            
            if (!document.getElementById('todos-tramites-section').classList.contains('hidden')) {
                cargarTodosTramites();
            } else if (!document.getElementById('prioritarios-section').classList.contains('hidden')) {
                cargarTramitesPrioritarios();
            } else {
                cargarTramitesRecientes();
            }
            cargarEstadisticas();
        } else {
            showErrorToast('Error al actualizar estado');
        }
    } catch (error) {
        console.error('Error al actualizar estado:', error);
        showErrorToast('Error al actualizar estado');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    cargarEstadisticas();
    cargarTramitesRecientes();
    
    // Auto-refresh notifications every 30 seconds
    setInterval(() => {
        cargarEstadisticas();
    }, 30000);
});
