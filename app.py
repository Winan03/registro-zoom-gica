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
    exportar_reporte_completo, exportar_a_archivo, buscar_y_generar_reporte_con_estado,
    obtener_sugerencias_nombres, calcular_score_sugerencia
)
import procesamiento

def restaurar_si_vacio():
    if procesamiento.nombre_original_df.empty and os.path.exists("datos_temporales.pkl"):
        print("🟡 Restaurando datos desde respaldo temporal...")
        procesamiento.nombre_original_df = pd.read_pickle("datos_temporales.pkl")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

@app.route('/')
def index():
    # Obtener parámetros GET (página actual)
    pagina = int(request.args.get('pagina', 1))
    elementos_por_pagina = 25  # Puedes ajustar este valor

    # Obtener filtros disponibles
    fechas, areas = obtener_filtros_actuales()

    # Obtener el DataFrame actual con filtros aplicados (si existe)
    df = exportar_reporte_con_filtros_actuales()

    # Calcular paginación
    total_paginas = (len(df) + elementos_por_pagina - 1) // elementos_por_pagina if not df.empty else 1
    inicio = (pagina - 1) * elementos_por_pagina
    fin = inicio + elementos_por_pagina
    df_pagina = df.iloc[inicio:fin] if not df.empty else pd.DataFrame()

    # Generar tabla HTML de la página actual
    tabla_html = mostrar_tabla_agrupada_por_fecha(df_pagina)

    return render_template('index.html',
                           tabla_html=tabla_html,
                           fechas=fechas,
                           areas=areas,
                           busqueda_texto="",
                           pagina_actual=pagina,
                           total_paginas=total_paginas)

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

    # Paginación
    pagina = 1
    elementos_por_pagina = 26
    df_pagina = df_reporte.iloc[0:elementos_por_pagina]

    html_tabla = mostrar_tabla_agrupada_por_fecha(df_pagina)
    fechas, areas = obtener_filtros_actuales()

    return render_template('index.html',
                           tabla_html=html_tabla,
                           fechas=fechas,
                           areas=areas,
                           busqueda_texto="",
                           pagina_actual=pagina,
                           total_paginas=(len(df_reporte) + elementos_por_pagina - 1) // elementos_por_pagina)



@app.route('/filtrar', methods=['POST'])
def filtrar():
    restaurar_si_vacio() 
    area = request.form.get('area', 'TODOS')
    fechas = request.form.getlist('fechas')
    turno = request.form.get('turno', 'TODOS')
    
    # Usar la nueva función que guarda el estado
    df = aplicar_filtros_y_guardar_estado(area, fechas, turno)
    html_tabla = mostrar_tabla_agrupada_por_fecha(df)
    fechas_disponibles, areas = obtener_filtros_actuales()
    
    return render_template('index.html',
                            tabla_html=html_tabla,
                            fechas=fechas_disponibles,
                            areas=areas,
                            busqueda_texto="",
                            pagina_actual=1,
                            total_paginas=1)

@app.route('/buscar', methods=['POST'])
def buscar():
    restaurar_si_vacio() 
    try:
        texto = request.form.get('busqueda', '').strip()
        
        if procesamiento.nombre_original_df.empty:
            html_tabla = "<div class='alert alert-warning'>⚠️ No hay datos cargados. Por favor, cargue un archivo primero.</div>"
        else:
            if texto:
                df_resultado = buscar_y_generar_reporte_con_estado(texto, procesamiento.nombre_original_df)
                
                if df_resultado.empty:
                    html_tabla = f"""
                    <div class='alert alert-info'>
                        <h5>No se encontraron resultados para: "{texto}"</h5>
                        ...
                    </div>
                    """
                else:
                    html_tabla = procesamiento.mostrar_tabla_agrupada_por_fecha(df_resultado)

            else:
                df_resultado = limpiar_filtros_y_busqueda()
                html_tabla = procesamiento.mostrar_tabla_agrupada_por_fecha(df_resultado)
        
        fechas, areas = procesamiento.obtener_filtros_actuales()
        return render_template('index.html',
                                tabla_html=html_tabla,
                                fechas=fechas,
                                areas=areas,
                                busqueda_texto=texto,
                                pagina_actual=1,
                                total_paginas=1)

    except Exception as e:
        print(f"❌ Error en /buscar: {e}")
        import traceback
        traceback.print_exc()

        html_tabla = f"<div class='alert alert-danger'>Error interno: {str(e)}</div>"
        fechas, areas = procesamiento.obtener_filtros_actuales()
        return render_template('index.html',
                                tabla_html=html_tabla,
                                fechas=fechas,
                                areas=areas,
                                busqueda_texto="",
                                pagina_actual=1,
                                total_paginas=1)

# Endpoint Flask para las sugerencias
@app.route('/api/sugerencias', methods=['POST'])
def api_sugerencias():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query or len(query) < 2:
            return jsonify([])
        
        # Usar tu DataFrame global o cargarlo según tu estructura
        # Asume que tienes df_original disponible globalmente
        df_original = procesamiento.nombre_original_df
        sugerencias = obtener_sugerencias_nombres(query, df_original, limit=8)
        
        return jsonify(sugerencias)
        
    except Exception as e:
        print(f"Error en api_sugerencias: {e}")
        return jsonify([]), 500

# Función mejorada que integra sugerencias con tu búsqueda existente
def buscar_con_sugerencias(texto_busqueda, df_original):
    """
    Versión mejorada de tu función de búsqueda que también puede usarse para sugerencias
    """
    if not texto_busqueda or not texto_busqueda.strip():
        return df_original.copy() if not df_original.empty else pd.DataFrame()
    
    if df_original.empty:
        return pd.DataFrame()
    
    # Tu lógica de búsqueda existente
    texto_busqueda = texto_busqueda.strip()
    texto_busqueda_limpio = quitar_tildes_y_ñ(texto_busqueda.lower())
    palabras_clave = [p for p in texto_busqueda_limpio.split() if len(p) > 1]
    
    if not palabras_clave:
        return df_original.copy()
    
    df_trabajo = df_original.copy()
    
    def coincide_busqueda(nombre):
        if pd.isna(nombre):
            return False
        
        nombre_limpio = quitar_tildes_y_ñ(str(nombre).lower())
        
        coincidencias = 0
        for palabra in palabras_clave:
            if palabra in nombre_limpio:
                coincidencias += 1
        
        if coincidencias == len(palabras_clave):
            return True
        
        if len(palabras_clave) > 1 and coincidencias >= (len(palabras_clave) * 0.7):
            return True
        
        if len(palabras_clave) == 1 and coincidencias > 0:
            return True
        
        return False
    
    mask_principal = df_trabajo['nombre'].apply(coincide_busqueda)
    df_filtrado = df_trabajo[mask_principal].copy()
    
    # Si no hay resultados, búsqueda flexible (tu código existente)
    if df_filtrado.empty:
        def busqueda_flexible(nombre):
            if pd.isna(nombre):
                return False
            
            nombre_limpio = quitar_tildes_y_ñ(str(nombre).lower())
            
            for palabra in palabras_clave:
                if len(palabra) >= 3:
                    if palabra in nombre_limpio or any(palabra in parte for parte in nombre_limpio.split()):
                        return True
                    
                    for parte_nombre in nombre_limpio.split():
                        if len(parte_nombre) >= 3:
                            similitud = SequenceMatcher(None, palabra, parte_nombre).ratio()
                            if similitud >= 0.8:
                                return True
            
            return False
        
        mask_flexible = df_trabajo['nombre'].apply(busqueda_flexible)
        df_filtrado = df_trabajo[mask_flexible].copy()
    
    return df_filtrado

@app.route('/limpiar', methods=['POST'])
def limpiar():
    restaurar_si_vacio() 
    # Usar la nueva función que limpia todo
    df = limpiar_filtros_y_busqueda()
    html_tabla = mostrar_tabla_agrupada_por_fecha(df)
    fechas, areas = obtener_filtros_actuales()
    
    return render_template('index.html',
                            tabla_html=html_tabla,
                            fechas=fechas, 
                            areas=areas, 
                            busqueda_texto="",
                            pagina_actual=1,
                            total_paginas=1)

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
    restaurar_si_vacio() 
    df = procesamiento.reiniciar_todo()
    html_tabla = mostrar_tabla_agrupada_por_fecha(df)
    fechas, areas = obtener_filtros_actuales()
    return render_template('index.html',
                            tabla_html=html_tabla,
                            fechas=fechas,
                            areas=areas,
                            busqueda_texto="",
                            pagina_actual=1,
                            total_paginas=1)

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
    from procesamiento import restaurar_registro_desde_historial, obtener_historial
    try:
        indice = int(request.form.get("indice"))
        historial = obtener_historial()

        if 0 <= indice < len(historial):
            df_restaurado = restaurar_registro_desde_historial(historial[indice])

            if df_restaurado is not None and not df_restaurado.empty:
                tabla_html = procesamiento.mostrar_tabla_agrupada_por_fecha(df_restaurado)
            else:
                tabla_html = "<div class='alert alert-info'>No se encontraron datos para mostrar.</div>"

            fechas, areas = procesamiento.obtener_filtros_actuales()
            texto_busqueda = procesamiento.obtener_estado_filtros_actual().get("busqueda", "")
            return render_template("index.html", 
                                   tabla_html=tabla_html, 
                                   fechas=fechas, 
                                   areas=areas,
                                   busqueda_texto=texto_busqueda,
                                   pagina_actual=1,
                                   total_paginas=1)

        else:
            return "Índice fuera de rango", 400
    except Exception as e:
        print(f"❌ Error en /restaurar_historial: {e}")
        import traceback
        traceback.print_exc()
        return "Error interno", 500

@app.route('/obtener_info_vacios/<int:indice>')
def obtener_info_vacios(indice):
    """
    Endpoint para obtener información detallada de vacíos de un registro específico
    """
    try:
        if procesamiento.df_actual_filtrado.empty:
            return jsonify({'error': 'No hay datos disponibles'}), 400
        
        # Buscar el registro por índice
        registro = None
        for _, row in procesamiento.df_actual_filtrado.iterrows():
            if str(row.get('#', '')).strip() != '' and int(row['#']) == indice:
                registro = row
                break
        
        if registro is None:
            return jsonify({'error': 'Registro no encontrado'}), 404
        
        vacios_info = registro.get('vacios_info', {})
        
        if not vacios_info or not vacios_info.get('vacios'):
            return jsonify({'error': 'No hay información de vacíos disponible'}), 400
        
        return jsonify(vacios_info)
        
    except Exception as e:
        print(f"❌ Error en obtener_info_vacios: {e}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003)