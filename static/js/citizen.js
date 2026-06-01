const API_BASE = '/api';
let currentUser = null;

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
        case 'mis-tramites':
            cargarMisTramites();
            break;
        case 'mi-perfil':
            cargarMiPerfil();
            break;
    }
}

// Load current user info
async function loadCurrentUser() {
    try {
        const response = await fetch('/api/current-user');
        if (response.ok) {
            currentUser = await response.json();
            updateUserUI(currentUser);
        }
    } catch (error) {
        console.error('Error al cargar usuario:', error);
    }
}

// Update user UI
function updateUserUI(user) {
    document.getElementById('user-name').textContent = user.nombre;
    document.getElementById('profile-name').textContent = user.nombre;
    document.getElementById('profile-email').textContent = user.email;
    document.getElementById('profile-email-large').textContent = user.email;
    document.getElementById('profile-name-large').textContent = user.nombre;
    
    if (user.foto_perfil) {
        document.getElementById('user-avatar').src = user.foto_perfil;
        document.getElementById('profile-avatar-large').src = user.foto_perfil;
    }
}

// Load my tramites
async function cargarMisTramites() {
    try {
        const response = await fetch(`${API_BASE}/mis-tramites`);
        const tramites = await response.json();
        
        const tbody = document.getElementById('my-tramites-tbody');
        tbody.innerHTML = '';
        
        // Update stats
        document.getElementById('my-total-tramites').textContent = tramites.length;
        document.getElementById('my-pendientes').textContent = tramites.filter(t => t.estado === 'pendiente').length;
        document.getElementById('my-completados').textContent = tramites.filter(t => t.estado === 'completado').length;
        
        tramites.forEach(tramite => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${tramite.id}</td>
                <td>${tramite.tipo_tramite}</td>
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
        console.error('Error al cargar mis trámites:', error);
    }
}

// Save profile
document.getElementById('perfil-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        dni: document.getElementById('dni').value,
        nombres: document.getElementById('nombres').value,
        apellidos: document.getElementById('apellidos').value,
        telefono: document.getElementById('telefono').value,
        direccion: document.getElementById('direccion').value
    };
    
    try {
        const response = await fetch(`${API_BASE}/mi-perfil`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            showSuccessToast('Información guardada exitosamente');
            document.getElementById('perfil-form').reset();
        } else {
            showErrorToast('Error al guardar información');
        }
    } catch (error) {
        console.error('Error al guardar perfil:', error);
        showErrorToast('Error al guardar información');
    }
});

// Create tramite
document.getElementById('tramite-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
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
        tipo_tramite: document.getElementById('tipo-tramite').value,
        descripcion: document.getElementById('descripcion').value,
        documentos: documentos
    };
    
    try {
        const response = await fetch(`${API_BASE}/mis-tramites`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(tramiteData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
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

// View tramite detail
async function verDetalleTramite(tramiteId) {
    try {
        const response = await fetch(`${API_BASE}/mis-tramites/${tramiteId}`);
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
                    <h6>Alertas</h6>
                    ${tramite.alertas && tramite.alertas.length > 0 ? 
                        tramite.alertas.map(a => `
                            <div class="alert alert-info">
                                <small>${new Date(a.fecha_envio).toLocaleString()}</small><br>
                                ${a.mensaje}
                            </div>
                        `).join('') : 
                        '<p class="text-muted">No hay alertas.</p>'
                    }
                </div>
            </div>
            <hr>
            <h6>Descripción</h6>
            <p>${tramite.descripcion || 'Sin descripción'}</p>
            <hr>
            <h6>Documentos</h6>
            ${documentosHtml}
        `;
        
        const modal = new bootstrap.Modal(document.getElementById('tramiteModal'));
        modal.show();
    } catch (error) {
        console.error('Error al cargar detalle del trámite:', error);
        showErrorToast('Error al cargar detalle del trámite');
    }
}

// Load my profile
async function cargarMiPerfil() {
    try {
        const response = await fetch('/api/mi-perfil');
        const perfil = await response.json();
        
        if (perfil.ciudadano) {
            document.getElementById('profile-dni').textContent = perfil.ciudadano.dni || '-';
            document.getElementById('profile-telefono').textContent = perfil.ciudadano.telefono || '-';
            document.getElementById('profile-direccion').textContent = perfil.ciudadano.direccion || '-';
            document.getElementById('profile-fecha').textContent = new Date(perfil.usuario.fecha_registro).toLocaleDateString();
            document.getElementById('profile-tramites').textContent = perfil.total_tramites || 0;
            
            // Fill form
            document.getElementById('dni').value = perfil.ciudadano.dni || '';
            document.getElementById('nombres').value = perfil.ciudadano.nombres || '';
            document.getElementById('apellidos').value = perfil.ciudadano.apellidos || '';
            document.getElementById('telefono').value = perfil.ciudadano.telefono || '';
            document.getElementById('direccion').value = perfil.ciudadano.direccion || '';
        }
    } catch (error) {
        console.error('Error al cargar perfil:', error);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCurrentUser();
    cargarMisTramites();
});
