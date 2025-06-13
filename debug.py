
def generar_datos_grafico(tipo_grafico='barras'):
    """
    Genera datos para diferentes tipos de gráficos basados en el DataFrame actual
    """
    try:
        # Usar el DataFrame actual con filtros aplicados - CORREGIDO
        global df_actual_filtrado, nombre_original_df
        
        # Usar el DataFrame correcto
        if not df_actual_filtrado.empty:
            df = df_actual_filtrado.copy()
        elif not nombre_original_df.empty:
            df = nombre_original_df.copy()
        else:
            return {'error': 'No hay datos disponibles para generar gráficos'}
        
        if df.empty:
            return {'error': 'No hay datos disponibles para generar gráficos'}
        
        resultado = {'tipo': tipo_grafico, 'datos': {}, 'titulo': '', 'labels': [], 'values': []}
        
        if tipo_grafico == 'barras':
            # Gráfico de barras por área
            if 'Área' in df.columns:
                conteo_areas = df['Área'].value_counts()
                if conteo_areas.empty:
                    return {'error': 'No hay datos de áreas disponibles'}
                    
                resultado['titulo'] = 'Distribución por Área'
                resultado['labels'] = conteo_areas.index.tolist()
                resultado['values'] = conteo_areas.values.tolist()
                resultado['datos'] = {
                    'datasets': [{
                        'label': 'Cantidad de Registros',
                        'data': resultado['values'],
                        'backgroundColor': [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                        ][:len(resultado['values'])]  # Limitar colores al número de datos
                    }],
                    'labels': resultado['labels']
                }
            else:
                return {'error': 'No se encontró la columna "Área" en los datos'}
        
        elif tipo_grafico == 'pie':
            # Gráfico circular por turno
            if 'turno' in df.columns:
                conteo_turnos = df['turno'].value_counts()
                if conteo_turnos.empty:
                    return {'error': 'No hay datos de turnos disponibles'}
                    
                resultado['titulo'] = 'Distribución por Turno'
                resultado['labels'] = conteo_turnos.index.tolist()
                resultado['values'] = conteo_turnos.values.tolist()
                resultado['datos'] = {
                    'datasets': [{
                        'data': resultado['values'],
                        'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'][:len(resultado['values'])]
                    }],
                    'labels': resultado['labels']
                }
            else:
                return {'error': 'No se encontró la columna "turno" en los datos'}
        
        elif tipo_grafico == 'lineas':
            # Gráfico de líneas por fecha
            if 'fecha' in df.columns:
                # Convertir fechas y contar registros por fecha
                df_temp = df.copy()
                df_temp['fecha'] = pd.to_datetime(df_temp['fecha'], errors='coerce')
                # Eliminar fechas nulas
                df_temp = df_temp.dropna(subset=['fecha'])
                
                if df_temp.empty:
                    return {'error': 'No hay fechas válidas en los datos'}
                
                conteo_fechas = df_temp['fecha'].dt.date.value_counts().sort_index()
                
                resultado['titulo'] = 'Registros por Fecha'
                resultado['labels'] = [str(fecha) for fecha in conteo_fechas.index.tolist()]
                resultado['values'] = conteo_fechas.values.tolist()
                resultado['datos'] = {
                    'datasets': [{
                        'label': 'Registros por Fecha',
                        'data': resultado['values'],
                        'borderColor': '#36A2EB',
                        'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                        'fill': True
                    }],
                    'labels': resultado['labels']
                }
            else:
                return {'error': 'No se encontró la columna "fecha" en los datos'}
        
        elif tipo_grafico == 'horas':
            # Gráfico de horas totales por persona (top 10)
            if 'nombre' in df.columns and 'duracion_horas' in df.columns:
                # Agrupar por nombre y sumar horas
                horas_por_persona = df.groupby('nombre')['duracion_horas'].sum().sort_values(ascending=False).head(10)
                
                if horas_por_persona.empty:
                    return {'error': 'No hay datos de horas disponibles'}
                
                resultado['titulo'] = 'Top 10 - Horas Totales por Persona'
                resultado['labels'] = horas_por_persona.index.tolist()
                resultado['values'] = horas_por_persona.values.tolist()
                resultado['datos'] = {
                    'datasets': [{
                        'label': 'Horas Totales',
                        'data': resultado['values'],
                        'backgroundColor': '#4BC0C0'
                    }],
                    'labels': resultado['labels']
                }
            else:
                return {'error': 'No se encontraron las columnas "nombre" o "duracion_horas" en los datos'}
        else:
            return {'error': f'Tipo de gráfico "{tipo_grafico}" no soportado'}
        
        # Debug: imprimir información del resultado
        print(f"✅ Gráfico {tipo_grafico} generado:")
        print(f"   - Título: {resultado['titulo']}")
        print(f"   - Labels: {len(resultado['labels'])} elementos")
        print(f"   - Values: {len(resultado['values'])} elementos")
        print(f"   - Datos: {len(resultado['datos'].get('datasets', []))} datasets")
        
        return resultado
        
    except Exception as e:
        print(f"❌ Error en generar_datos_grafico: {e}")
        import traceback
        traceback.print_exc()
        return {'error': f'Error al generar datos del gráfico: {str(e)}'}
