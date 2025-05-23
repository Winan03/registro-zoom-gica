from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import os
import tempfile
import pandas as pd 
from datetime import datetime
from werkzeug.utils import secure_filename
from procesamiento import (
    procesar_excel, mostrar_tabla_agrupada_por_fecha,
    aplicar_filtros_y_guardar_estado, limpiar_filtros_y_busqueda, 
    obtener_filtros_actuales, exportar_reporte_con_filtros_actuales,
    exportar_reporte_completo, exportar_a_archivo, buscar_y_generar_reporte_con_estado
)
import procesamiento

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

@app.route('/')
def index():
    fechas, areas = obtener_filtros_actuales()
    return render_template('index.html', tabla_html="No hay datos para mostrar.", fechas=fechas, areas=areas, busqueda_texto="")

@app.route('/cargar', methods=['POST'])
def cargar():
    archivos = request.files.getlist('archivos')
    file_paths = []
    
    for archivo in archivos:
        filename = secure_filename(archivo.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        archivo.save(path)
        file_paths.append(path)
    
    df_reporte = procesar_excel(file_paths)
    html_tabla = mostrar_tabla_agrupada_por_fecha(df_reporte)
    fechas, areas = obtener_filtros_actuales()
    
    return render_template('index.html', tabla_html=html_tabla, fechas=fechas, areas=areas, busqueda_texto="")

@app.route('/filtrar', methods=['POST'])
def filtrar():
    area = request.form.get('area', 'TODOS')
    fechas = request.form.getlist('fechas')
    turno = request.form.get('turno', 'TODOS')
    
    # Usar la nueva función que guarda el estado
    df = aplicar_filtros_y_guardar_estado(area, fechas, turno)
    html_tabla = mostrar_tabla_agrupada_por_fecha(df)
    fechas_disponibles, areas = obtener_filtros_actuales()
    
    return render_template('index.html', tabla_html=html_tabla, fechas=fechas_disponibles, areas=areas, busqueda_texto="")

@app.route('/buscar', methods=['POST'])
def buscar():
    """Ruta mejorada para búsqueda con manejo correcto del DataFrame global"""
    try:
        # Obtener el texto de búsqueda desde el formulario
        texto = request.form.get('busqueda', '').strip()
        
        print(f"🌐 Búsqueda recibida: '{texto}'")
        print(f"📊 Estado DataFrame original: {len(procesamiento.nombre_original_df) if not procesamiento.nombre_original_df.empty else 'VACÍO'}")
        
        # Verificar si el DataFrame global tiene datos cargados
        if procesamiento.nombre_original_df.empty:
            print("❌ DataFrame original vacío")
            html_tabla = "<div class='alert alert-warning'>⚠️ No hay datos cargados. Por favor, cargue un archivo primero.</div>"
        else:
            if texto:
                print(f"🔍 Realizando búsqueda con: '{texto}'")
                # Usar la nueva función que también guarda el estado
                df_resultado = buscar_y_generar_reporte_con_estado(texto, procesamiento.nombre_original_df)
                
                if df_resultado.empty:
                    print("❌ Sin resultados")
                    html_tabla = f"""
                    <div class='alert alert-info'>
                        <h5>No se encontraron resultados para: "{texto}"</h5>
                        <p>Sugerencias:</p>
                        <ul>
                            <li>Verifique la ortografía</li>
                            <li>Intente con solo el nombre o apellido</li>
                            <li>Use menos palabras en la búsqueda</li>
                        </ul>
                    </div>
                    """
                else:
                    print(f"✅ Resultados encontrados: {len(df_resultado)}")
                    html_tabla = procesamiento.mostrar_tabla_agrupada_por_fecha(df_resultado)
            else:
                print("📋 Mostrando todos los datos porque el texto está vacío")
                df_resultado = limpiar_filtros_y_busqueda()
                html_tabla = procesamiento.mostrar_tabla_agrupada_por_fecha(df_resultado)
        
        # Obtener fechas y áreas actualizadas para recargar el formulario
        fechas, areas = procesamiento.obtener_filtros_actuales()

        return render_template('index.html', 
                               tabla_html=html_tabla, 
                               fechas=fechas, 
                               areas=areas, 
                               busqueda_texto=texto)
    
    except Exception as e:
        print(f"❌ Error en /buscar: {e}")
        import traceback
        traceback.print_exc()
        
        html_tabla = f"<div class='alert alert-danger'>Error procesando búsqueda: {str(e)}</div>"
        fechas, areas = procesamiento.obtener_filtros_actuales()

        return render_template('index.html', 
                               tabla_html=html_tabla, 
                               fechas=fechas, 
                               areas=areas, 
                               busqueda_texto=texto if 'texto' in locals() else '')

@app.route('/limpiar', methods=['POST'])
def limpiar():
    # Usar la nueva función que limpia todo
    df = limpiar_filtros_y_busqueda()
    html_tabla = mostrar_tabla_agrupada_por_fecha(df)
    fechas, areas = obtener_filtros_actuales()
    
    return render_template('index.html', tabla_html=html_tabla, fechas=fechas, areas=areas, busqueda_texto="")

@app.route('/exportar', methods=['POST'])
def exportar():
    try:
        # Obtener el tipo de exportación solicitado
        tipo = request.form.get('tipo', 'filtros')  # 'filtros' o 'completo'
        
        print(f"Tipo de exportación solicitado: {tipo}")
        
        # Generar el reporte según el tipo
        if tipo == "filtros":
            df_exportar = exportar_reporte_con_filtros_actuales()
            tipo_nombre = "filtrado"
        else:
            df_exportar = exportar_reporte_completo()
            tipo_nombre = "completo"
        
        if df_exportar.empty:
            return jsonify({'error': f'No hay datos para exportar el reporte {tipo_nombre}'}), 400
        
        # Crear archivo temporal
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'reporte_{tipo_nombre}_{timestamp}.xlsx'
        ruta_temporal = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Exportar archivo
        if exportar_a_archivo(df_exportar, ruta_temporal):
            print(f"✅ Archivo exportado exitosamente: {filename}")
            return send_file(
                ruta_temporal, 
                as_attachment=True, 
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify({'error': 'Error al generar el archivo'}), 500
            
    except Exception as e:
        print(f"❌ Error en exportar(): {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/obtener_estado_filtros')
def obtener_estado_filtros():
    """Endpoint para obtener el estado actual de los filtros (útil para debugging)"""
    try:
        estado = procesamiento.obtener_estado_filtros_actual()
        return jsonify(estado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reestablecer', methods=['POST'])
def reestablecer():
    df = procesamiento.reiniciar_todo()
    html_tabla = mostrar_tabla_agrupada_por_fecha(df)
    fechas, areas = obtener_filtros_actuales()
    return render_template('index.html', tabla_html=html_tabla, fechas=fechas, areas=areas, busqueda_texto="")

@app.route('/historial')
def historial():
    from procesamiento import obtener_historial
    historial = obtener_historial()
    return jsonify(historial)

@app.route('/ver_historial')
def ver_historial():
    from procesamiento import obtener_historial
    historial = obtener_historial()
    return render_template('historial.html', historial=historial)

@app.route('/restaurar_historial', methods=['POST'])
def restaurar_historial():
    try:
        indice = int(request.form.get("indice"))
        historial = procesamiento.obtener_historial()
        if 0 <= indice < len(historial):
            df_restaurado = procesamiento.restaurar_registro_desde_historial(historial[indice])

            print(f"✅ Restaurado. Registros en memoria: {len(df_restaurado)}")

            html_tabla = procesamiento.mostrar_tabla_agrupada_por_fecha(df_restaurado)
            fechas, areas = procesamiento.obtener_filtros_actuales()
            estado = procesamiento.obtener_estado_filtros_actual()
            texto_busqueda = estado.get("busqueda", "")

            return render_template('index.html',
                                   tabla_html=html_tabla,
                                   fechas=fechas,
                                   areas=areas,
                                   busqueda_texto=texto_busqueda)
        else:
            return "Índice fuera de rango", 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return "Error interno", 500


if __name__ == '__main__':
    app.run(debug=True)