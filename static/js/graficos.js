// Funciones para mostrar y cerrar el modal de gráficos
function mostrarModalGraficos() {
    document.getElementById('graficosModal').style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevenir scroll del fondo
    // Limpiar el contenido anterior del gráfico y el input del practicante al abrir el modal
    document.getElementById('grafico-container').innerHTML = '';
    document.getElementById('descargarBtn').style.display = 'none';
    const nombrePracticanteInput = document.getElementById('nombrePracticanteInput');
    if (nombrePracticanteInput) {
        nombrePracticanteInput.value = ''; // Limpiar el campo de texto
    }
    // Asegurarse de que el control de filtro por practicante esté visible si es necesario
    togglePracticanteFilter(false); // Ocultar por defecto al abrir el modal
}

function cerrarModalGraficos() {
    document.getElementById('graficosModal').style.display = 'none';
    document.body.style.overflow = 'auto'; // Restaurar scroll
}

// Función para alternar la visibilidad del campo de filtro por practicante
function togglePracticanteFilter(show) {
    const filterSection = document.getElementById('practicante-filter-section');
    if (filterSection) {
        filterSection.style.display = show ? 'block' : 'none';
    }
}

// Función principal para generar gráficos
async function generarGrafico(tipoGrafico, nombrePracticante = null) {
    const container = document.getElementById('grafico-container');
    const descargarBtn = document.getElementById('descargarBtn');
    
    // Mostrar mensaje de carga
    container.innerHTML = '<div class="loading">📊 Generando gráfico, por favor espera...</div>';
    descargarBtn.style.display = 'none';
    
    // Preparar el cuerpo de la petición
    const requestBody = { 
        tipo_grafico: tipoGrafico 
    };

    if (tipoGrafico === 'horas_promedio' && nombrePracticante) {
        requestBody.nombre_practicante = nombrePracticante;
    }

    try {
        const response = await fetch('/generar_graficos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorText = await response.text(); // Obtener el texto del error
            throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
        }

        const data = await response.json();

        if (data.success) {
            // Mostrar el gráfico
            container.innerHTML = `
                <div class="grafico-resultado">
                    <h4 class="text-xl font-bold text-gray-800 mb-4">${data.title}</h4>
                    <img src="data:image/png;base64,${data.image}" 
                        alt="${data.title}" 
                        class="w-full h-auto rounded-lg shadow-md max-w-full"
                        id="graficoActual">
                </div>
            `;
            
            // Mostrar botón de descarga
            descargarBtn.style.display = 'inline-flex';
            
            // Guardar datos del gráfico para descarga
            window.currentChart = {
                title: data.title,
                image: data.image,
                type: tipoGrafico
            };
        } else {
            // Mostrar error
            container.innerHTML = `
                <div class="error text-red-600 p-4 bg-red-100 rounded-md">
                    ❌ Error al generar el gráfico: ${data.error || 'Error desconocido'}
                </div>
            `;
        }
    } catch (error) {
        console.error('Error:', error);
        container.innerHTML = `
            <div class="error text-red-600 p-4 bg-red-100 rounded-md">
                ❌ Error de conexión o servidor: ${error.message}
                <br><small>Verifica que el servidor Flask esté funcionando correctamente.</small>
            </div>
        `;
    }
}

// Función auxiliar para generar el gráfico de horas promedio con o sin practicante
function generarGraficoHorasPromedio() {
    // Al seleccionar "Horas Promedio", mostramos el campo de filtro por practicante.
    togglePracticanteFilter(true); 
    // Generamos el gráfico general inicialmente
    generarGrafico('horas_promedio');
}

// Función para generar el gráfico de horas promedio para un practicante específico
function generarGraficoHorasPracticanteEspecifico() {
    const nombrePracticante = document.getElementById('nombrePracticanteInput').value.trim();
    if (nombrePracticante) {
        generarGrafico('horas_promedio', nombrePracticante);
    } else {
        // En lugar de alert, podrías mostrar un mensaje en el modal o un tooltip
        // Para esta aplicación, usaremos un mensaje simple ya que la especificación prohíbe alert.
        document.getElementById('grafico-container').innerHTML = `
            <div class="error text-red-600 p-4 bg-red-100 rounded-md">
                ⚠️ Por favor, ingresa el nombre de un practicante para filtrar el gráfico.
            </div>
        `;
    }
}


// Función para descargar el gráfico actual
function descargarGrafico() {
    if (window.currentChart) {
        const link = document.createElement('a');
        link.download = `grafico_${window.currentChart.type}_${new Date().toISOString().split('T')[0]}.png`;
        link.href = `data:image/png;base64,${window.currentChart.image}`;
        link.click();
    } else {
        // En lugar de alert, mostrar un mensaje en el modal
        document.getElementById('grafico-container').innerHTML = `
            <div class="error text-red-600 p-4 bg-red-100 rounded-md">
                ⚠️ No hay ningún gráfico para descargar. Genera uno primero.
            </div>
        `;
    }
}

// Función para actualizar datos (placeholder)
function actualizarDatos() {
    // En lugar de alert, mostrar un mensaje informativo en el modal
    document.getElementById('grafico-container').innerHTML = `
        <div class="loading text-blue-600 p-4 bg-blue-100 rounded-md">
            🔄 Funcionalidad de actualización en desarrollo.<br>Por ahora, recarga la página para obtener datos actualizados.
        </div>
    `;
    // Opcionalmente, podrías disparar una recarga de la página si es lo deseado:
    // setTimeout(() => { window.location.reload(); }, 2000); 
}

// Cerrar modal al hacer clic fuera de él
window.onclick = function(event) {
    const modal = document.getElementById('graficosModal');
    if (event.target === modal) {
        cerrarModalGraficos();
    }
}

// Cerrar modal con la tecla Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('graficosModal');
        if (modal.style.display === 'block') {
            cerrarModalGraficos();
        }
    }
});