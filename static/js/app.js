const API_BASE = '/api';

let ciudadanoActual = null;

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

function showWarningToast(message) {
    document.getElementById('warningToastBody').textContent = message;
    const toast = new bootstrap.Toast(document.getElementById('warningToast'));
    toast.show();
}

function showInfoToast(message) {
    document.getElementById('infoToastBody').textContent = message;
    const toast = new bootstrap.Toast(document.getElementById('infoToast'));
    toast.show();
}

// Show/Hide sections
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('[id$="-section"]').forEach(section => {
        section.classList.add('hidden');
    });
    
    // Show selected section
    document.getElementById(`${sectionName}-section`).classList.remove('hidden');
    
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    event.target.closest('.nav-link').classList.add('active');
    
    // Load section data
    switch(sectionName) {
        case 'dashboard':
            cargarEstadisticas();
            break;
        case 'tramites':
            cargarTramites();
            break;
        case 'prioritarios':
            cargarTramitesPrioritarios();
            break;
        case 'alertas':
            cargarAlertas();
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
        document.getElementById('tramites-proceso').textContent = data.tramites_por_estado.en_proceso || 0;
        document.getElementById('tramites-completados').textContent = data.tramites_por_estado.completado || 0;
    } catch (error) {
        console.error('Error al cargar estadísticas:', error);
    }
}

// Create citizen
document.getElementById('ciudadano-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        dni: document.getElementById('dni').value,
        email: document.getElementById('email').value,
        nombres: document.getElementById('nombres').value,
        apellidos: document.getElementById('apellidos').value,
        telefono: document.getElementById('telefono').value,
        direccion: document.getElementById('direccion').value
    };
    
    try {
        const response = await fetch(`${API_BASE}/ciudadanos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccessToast('Ciudadano registrado exitosamente');
            ciudadanoActual = result.ciudadano;
            document.getElementById('ciudadano-form').reset();
        } else {
            showErrorToast('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error al crear ciudadano:', error);
        showErrorToast('Error al registrar ciudadano');
    }
});

// Create tramite
document.getElementById('tramite-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Get citizen by DNI
    const dni = document.getElementById('tramite-dni').value;
    let ciudadanoId;
    
    try {
        // First, we need to find the citizen by DNI
        // For now, we'll use a simple approach - in production you'd have a proper endpoint
        const response = await fetch(`${API_BASE}/ciudadanos`);
        const ciudadanos = await response.json();
        const ciudadano = ciudadanos.find(c => c.dni === dni);
        
        if (!ciudadano) {
            showWarningToast('Ciudadano no encontrado. Por favor regístrese primero.');
            return;
        }
        
        ciudadanoId = ciudadano.id;
        
        // Collect documents
        const documentos = [];
        document.querySelectorAll('.documento-item').forEach(item => {
            const tipo = item.querySelector('[name="tipo_documento"]').value;
            const nombre = item.querySelector('[name="nombre_archivo"]').value;
            const contenido = item.querySelector('[name="contenido"]').value;
            
            if (tipo && nombre) {
                documentos.push({
                    tipo_documento: tipo,
                    nombre_archivo: nombre,
                    contenido: contenido
                });
            }
        });
        
        const tramiteData = {
            ciudadano_id: ciudadanoId,
            tipo_tramite: document.getElementById('tipo-tramite').value,
            descripcion: document.getElementById('descripcion').value,
            documentos: documentos
        };
        
        const tramiteResponse = await fetch(`${API_BASE}/tramites`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(tramiteData)
        });
        
        const result = await tramiteResponse.json();
        
        if (tramiteResponse.ok) {
            showSuccessToast(`Trámite creado exitosamente con prioridad ML: ${result.prioridad_ml} (confianza: ${(result.confianza_ml * 100).toFixed(1)}%)`);
            document.getElementById('tramite-form').reset();
            document.getElementById('documentos-container').innerHTML = `
                <div class="documento-item mb-2">
                    <div class="row">
                        <div class="col-md-4">
                            <input type="text" class="form-control" placeholder="Tipo de documento" name="tipo_documento">
                        </div>
                        <div class="col-md-4">
                            <input type="text" class="form-control" placeholder="Nombre del archivo" name="nombre_archivo">
                        </div>
                        <div class="col-md-4">
                            <textarea class="form-control" placeholder="Contenido del documento" rows="1" name="contenido"></textarea>
                        </div>
                    </div>
                </div>
            `;
        } else {
            showErrorToast('Error al crear trámite');
        }
    } catch (error) {
        console.error('Error al crear trámite:', error);
        showErrorToast('Error al crear trámite');
    }
});

// Add document field
function agregarDocumento() {
    const container = document.getElementById('documentos-container');
    const nuevoDocumento = document.createElement('div');
    nuevoDocumento.className = 'documento-item mb-2';
    nuevoDocumento.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <input type="text" class="form-control" placeholder="Tipo de documento" name="tipo_documento">
            </div>
            <div class="col-md-4">
                <input type="text" class="form-control" placeholder="Nombre del archivo" name="nombre_archivo">
            </div>
            <div class="col-md-4">
                <textarea class="form-control" placeholder="Contenido del documento" rows="1" name="contenido"></textarea>
            </div>
        </div>
    `;
    container.appendChild(nuevoDocumento);
}

// Load all tramites
async function cargarTramites() {
    const loading = document.getElementById('loading-tramites');
    loading.classList.add('show');
    
    try {
        const response = await fetch(`${API_BASE}/tramites`);
        const tramites = await response.json();
        
        const tbody = document.getElementById('tramites-tbody');
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
    } finally {
        loading.classList.remove('show');
    }
}

// Load prioritized tramites
async function cargarTramitesPrioritarios() {
    const loading = document.getElementById('loading-prioritarios');
    loading.classList.add('show');
    
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
    } finally {
        loading.classList.remove('show');
    }
}

// Load alerts
async function cargarAlertas() {
    const loading = document.getElementById('loading-alertas');
    loading.classList.add('show');
    
    try {
        const response = await fetch(`${API_BASE}/alertas`);
        const alertas = await response.json();
        
        const container = document.getElementById('alertas-container');
        container.innerHTML = '';
        
        if (alertas.length === 0) {
            container.innerHTML = '<p class="text-muted">No hay alertas recientes.</p>';
            return;
        }
        
        alertas.forEach(alerta => {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert-item';
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
        console.error('Error al cargar alertas:', error);
    } finally {
        loading.classList.remove('show');
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
                            <tr><td><strong>DNI:</strong></td><td>${tramite.ciudadano.dni}</td></tr>
                            <tr><td><strong>Nombre:</strong></td><td>${tramite.ciudadano.nombres} ${tramite.ciudadano.apellidos}</td></tr>
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
        alert('Error al cargar detalle del trámite');
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
            
            // Refresh current view
            if (!document.getElementById('tramites-section').classList.contains('hidden')) {
                cargarTramites();
            } else if (!document.getElementById('prioritarios-section').classList.contains('hidden')) {
                cargarTramitesPrioritarios();
            }
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
});
