import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

rag_time_ms_qs = [38683.33, 74981.66, 121653.15, 190722.57, 849932.49]
memory_avg_during_rag_mb_qs = [18594.64, 19124.53, 20110.86, 20374.34, 21173.49]
cpu_avg_during_rag_qs = [8.85, 13.77, 20.84, 33.75, 44.21]
gpu_mem_avg_rag_qs = [2538.95, 3393.14, 3523.46, 3646.04, 3735.06]

def quintil():
  # Cargar datos
  df = pd.read_csv('measurements_v3.csv')

  # Variables
  variables = ['rag_time_ms', 'memory_avg_during_rag_mb', 'cpu_avg_during_rag', 'gpu_mem_avg_rag']
  nombres_mostrar = ['Tiempo RAG (ms)', 'Memoria promedio RAG (MB)', 
                    'CPU promedio RAG (%)', 'Memoria GPU promedio RAG (MB)']

  # Crear figura
  fig, axes = plt.subplots(2, 2, figsize=(14, 10))
  axes = axes.flatten()

  # Estilo
  plt.style.use('seaborn-v0_8-darkgrid')

  for i, (var, nombre) in enumerate(zip(variables, nombres_mostrar)):
      ax = axes[i]
      
      datos = df[var].dropna()
      quintiles = np.percentile(datos, [0, 20, 40, 60, 80, 100])
      
      # Histograma
      ax.hist(datos, bins=30, alpha=0.7, edgecolor='black', 
              linewidth=0.5, color='skyblue')
      
      # Líneas de quintiles
      colors = ['red', 'orange', 'green', 'blue', 'purple']
      quintil_labels = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']
      
      legend_lines = []
      legend_labels = []
      
      for j in range(1, 6):
          line = ax.axvline(x=quintiles[j], color=colors[j-1], linestyle='--', 
                          linewidth=1.5, alpha=0.8)
          legend_lines.append(line)
          legend_labels.append(f'{quintil_labels[j-1]}: {quintiles[j]:.2f}')
      
      # Configuración
      ax.set_xlabel(nombre, fontsize=11)
      ax.set_ylabel('Frecuencia', fontsize=11)
      ax.set_title(f'Distribución de {nombre} con Quintiles', fontsize=12, fontweight='bold')
      
      # Estadísticas
      stats_text = f'''
      Mín: {datos.min():.2f}
      Máx: {datos.max():.2f}
      Media: {datos.mean():.2f}
      Mediana: {datos.median():.2f}
      '''
      ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
          fontsize=9, verticalalignment='top',
          bbox=dict(boxstyle='round', facecolor='white', alpha=0.9,
                  edgecolor='black', linewidth=0.5, pad=0.1))
      
      # Leyenda
      legend = ax.legend(legend_lines, legend_labels, loc='upper right', fontsize=9,
                        framealpha=1, frameon=True, edgecolor='black',
                        facecolor='white', fancybox=True, shadow=False,
                        borderpad=0.8, labelspacing=0.5)
      legend.get_frame().set_linewidth(0.5)

      # prints
      print(nombres_mostrar[i])
      print(var)
      print(stats_text)
      print(legend_labels)
      print('\n ++++++++++++++++++++++++++++++++++++++++++++++++++++++++ \n')

  plt.tight_layout()
  plt.show()

def csv_quintil():
    # Cargar el archivo CSV
    df = pd.read_csv('measurements_v3.csv')
    
    # Quintiles proporcionados
    quintiles = {
        'rag_time_ms': [38683.33, 74981.66, 121653.15, 190722.57, 849932.49],
        'memory_avg_during_rag_mb': [18594.64, 19124.53, 20110.86, 20374.34, 21173.49],
        'cpu_avg_during_rag': [8.85, 13.77, 20.84, 33.75, 44.21],
        'gpu_mem_avg_rag': [2538.95, 3393.14, 3523.46, 3646.04, 3735.06]
    }
    
    # Agregar columnas de quintiles
    for col, q_limits in quintiles.items():
        if col in df.columns:
            # Crear array de condiciones para cada quintil
            condiciones = [
                df[col] <= q_limits[0],  # Quintil 1
                (df[col] > q_limits[0]) & (df[col] <= q_limits[1]),  # Quintil 2
                (df[col] > q_limits[1]) & (df[col] <= q_limits[2]),  # Quintil 3
                (df[col] > q_limits[2]) & (df[col] <= q_limits[3]),  # Quintil 4
                df[col] > q_limits[3]  # Quintil 5
            ]
            
            # Valores para cada condición
            valores = [1, 2, 3, 4, 5]
            
            # Aplicar condiciones usando np.select
            df[f'{col}_quintil'] = np.select(condiciones, valores, default=np.nan)
    
    # Guardar el archivo modificado
    df.to_csv('measurements_v3_quintiles.csv', index=False)
    print("Archivo 'measurements_v3_quintiles.csv' creado exitosamente.")
    
    return df

def quintiles_cantidad():

    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np

    # Leer los datos
    df = pd.read_csv('measurements_v3_quintiles.csv')

    # Configurar el estilo de los gráficos
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Distribución de Quintiles - Conteos por Categoría', fontsize=18, fontweight='bold', y=1.02)

    # Definir colores para cada gráfico
    colors = ['#1f77b4', '#2ca02c', '#d62728', '#ff7f0e']
    
    # Títulos más descriptivos
    titles = {
        'rag_time_ms_quintil': 'Tiempo de RAG (ms)',
        'memory_avg_during_rag_mb_quintil': 'Memoria RAM Promedio (MB)',
        'cpu_avg_during_rag_quintil': 'Uso de CPU Promedio (%)',
        'gpu_mem_avg_rag_quintil': 'Memoria GPU Promedio (MB)'
    }

    columnas = ['rag_time_ms_quintil', 'memory_avg_during_rag_mb_quintil', 
                'cpu_avg_during_rag_quintil', 'gpu_mem_avg_rag_quintil']
    
    # Crear gráficos de barras verticales
    for idx, column in enumerate(columnas):
        ax = axes[idx // 2, idx % 2]
        
        # Obtener conteos por quintil
        conteos = df[column].value_counts().sort_index()
        
        # Crear etiquetas para todos los quintiles (1-5)
        quintiles = list(range(1, 6))
        valores = [conteos.get(q, 0) for q in quintiles]
        
        # Crear gráfico de barras
        bars = ax.bar(quintiles, valores, color=colors[idx], edgecolor='black', alpha=0.8, width=0.7)
        
        # Personalizar gráfico
        ax.set_title(f'Quintiles de {titles[column]}', fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('Quintil', fontsize=12)
        ax.set_ylabel('Número de Registros', fontsize=12)
        ax.set_xticks(quintiles)
        ax.set_xticklabels([f'Q{q}' for q in quintiles], fontsize=11)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Añadir etiquetas con los valores encima de las barras
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                   f'{int(height)}', ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        # Añadir porcentajes dentro de las barras
        total = sum(valores)
        for i, (bar, valor) in enumerate(zip(bars, valores)):
            if valor > 0:  # Solo mostrar porcentaje si hay valores
                porcentaje = (valor / total) * 100
                ax.text(bar.get_x() + bar.get_width()/2., valor/2,
                       f'{porcentaje:.1f}%', ha='center', va='center', 
                       color='white', fontweight='bold', fontsize=9)
        
        # Ajustar límites del eje Y para mejor visualización
        ax.set_ylim(0, max(valores) * 1.15 if max(valores) > 0 else 10)

    plt.tight_layout()
    plt.show()

    # Imprimir tabla resumen
    print("=" * 80)
    print("RESUMEN DE DISTRIBUCIÓN POR QUINTILES")
    print("=" * 80)
    
    # Crear tabla de datos
    resultados = {}
    for column in columnas:
        conteos = df[column].value_counts().sort_index()
        total = len(df)
        fila = []
        for q in range(1, 6):
            count = conteos.get(q, 0)
            porcentaje = (count / total) * 100
            fila.append(f"{count} ({porcentaje:.1f}%)")
        resultados[titles[column]] = fila
    
    # Crear DataFrame para mostrar como tabla
    tabla_df = pd.DataFrame(resultados, index=[f'Quintil {i}' for i in range(1, 6)])
    
    print("\nDistribución de registros por quintil:")
    print("-" * 80)
    print(tabla_df.to_string())
    
    # Estadísticas adicionales
    print("\n" + "=" * 80)
    print("ESTADÍSTICAS ADICIONALES")
    print("=" * 80)
    
    for column in columnas:
        print(f"\n📊 {titles[column]}:")
        valores = df[column]
        print(f"   Total registros: {len(valores)}")
        print(f"   Valor mínimo: {valores.min()}")
        print(f"   Valor máximo: {valores.max()}")
        print(f"   Promedio: {valores.mean():.2f}")
        print(f"   Desviación estándar: {valores.std():.2f}")
        
        # Distribución detallada
        conteos = df[column].value_counts().sort_index()
        print(f"   Distribución detallada:")
        for q in range(1, 6):
            count = conteos.get(q, 0)
            if count > 0:
                porcentaje = (count / len(df)) * 100
                print(f"     Quintil {q}: {count:3d} registros ({porcentaje:5.1f}%)")

def quintiles_cantidad_llm():
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np

    # Leer los datos
    df = pd.read_csv('measurements_v3_quintiles.csv')
    
    # Identificar los tamaños de LLM únicos
    llm_sizes = df['llm_size'].unique()
    llm_sizes = sorted(llm_sizes)  # Ordenar alfabéticamente
    print(f"Tamaños de LLM encontrados: {list(llm_sizes)}")
    
    # Definir los límites de los quintiles
    limites_quintiles = {
        'rag_time_ms_quintil': [
            "≤ 38.7s",
            "38.7s - 75.0s",
            "75.0s - 121.7s",
            "121.7s - 190.7s",
            "> 190.7s"
        ],
        'memory_avg_during_rag_mb_quintil': [
            "≤ 18.6 GB",
            "18.6 - 19.1 GB",
            "19.1 - 20.1 GB",
            "20.1 - 20.4 GB",
            "> 20.4 GB"
        ],
        'cpu_avg_during_rag_quintil': [
            "≤ 8.85%",
            "8.85% - 13.77%",
            "13.77% - 20.84%",
            "20.84% - 33.75%",
            "> 33.75%"
        ],
        'gpu_mem_avg_rag_quintil': [
            "≤ 2.54 GB",
            "2.54 - 3.39 GB",
            "3.39 - 3.52 GB",
            "3.52 - 3.65 GB",
            "> 3.65 GB"
        ]
    }
    
    # Configurar el estilo de los gráficos
    sns.set_style("whitegrid")
    
    # Crear figura con espacio para leyenda en la parte inferior
    fig = plt.figure(figsize=(22, 18))  # Más alto para acomodar leyenda
    
    # Usar GridSpec con espacio para leyenda
    # height_ratios: 2 filas de gráficos, 0.2 para la leyenda
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.15], 
                          wspace=0.4, hspace=0.4)
    
    # Crear ejes para los gráficos
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 0])
    ax4 = fig.add_subplot(gs[1, 1])
    
    # Crear eje para la leyenda (fila 2, todas las columnas)
    ax_leyenda = fig.add_subplot(gs[2, :])
    ax_leyenda.axis('off')  # Ocultar el eje de la leyenda
    
    axes = [[ax1, ax2], [ax3, ax4]]
    
    fig.suptitle('Distribución de Quintiles por Tamaño de LLM', 
                 fontsize=26, fontweight='bold', y=0.98)

    # Definir colores para cada tamaño de LLM
    colors = {
        'small': '#3498db',     # Azul para pequeño
        'standar': '#2ecc71'    # Verde para estándar
    }
    
    # Si hay más de 2 categorías, usar paleta de colores
    if len(llm_sizes) > 2:
        color_palette = sns.color_palette("husl", len(llm_sizes))
        colors = {size: color_palette[i] for i, size in enumerate(llm_sizes)}

    # Títulos descriptivos
    titles = {
        'rag_time_ms_quintil': 'Tiempo de RAG (segundos)',
        'memory_avg_during_rag_mb_quintil': 'Memoria RAM Promedio (GB)',
        'cpu_avg_during_rag_quintil': 'Uso de CPU Promedio (%)',
        'gpu_mem_avg_rag_quintil': 'Memoria GPU Promedio (GB)'
    }

    columnas = ['rag_time_ms_quintil', 'memory_avg_during_rag_mb_quintil', 
                'cpu_avg_during_rag_quintil', 'gpu_mem_avg_rag_quintil']
    
    # Lista para almacenar handles y labels para la leyenda común
    handles_leyenda = []
    labels_leyenda = []
    
    # Para cada variable, crear gráfico de barras apiladas
    for idx, column in enumerate(columnas):
        row = idx // 2
        col = idx % 2
        ax = axes[row][col]
        
        # Quintiles del 1 al 5
        quintiles = list(range(1, 6))
        
        # Preparar datos para gráfico apilado
        datos_apilados = {}
        for size in llm_sizes:
            datos_size = []
            for q in quintiles:
                count = len(df[(df['llm_size'] == size) & (df[column] == q)])
                datos_size.append(count)
            datos_apilados[size] = datos_size
        
        # Crear gráfico de barras apiladas
        bottom = np.zeros(len(quintiles))
        bars_por_tamano = []
        
        for i, size in enumerate(llm_sizes):
            valores = datos_apilados[size]
            bar = ax.bar(quintiles, valores, bottom=bottom, 
                        color=colors.get(size, f'C{i}'), 
                        edgecolor='black', alpha=0.8, width=0.7)
            
            # Guardar el primer handle de cada tamaño para la leyenda común
            if idx == 0:  # Solo necesitamos un handle por tamaño
                handles_leyenda.append(bar)
                labels_leyenda.append(f'{size.capitalize()}')
            
            # Añadir etiquetas dentro de cada segmento
            for j, (valor, bot) in enumerate(zip(valores, bottom)):
                if valor > 0:
                    y_pos = bot + valor/2
                    ax.text(quintiles[j], y_pos, str(valor), 
                           ha='center', va='center', 
                           color='white', fontweight='bold', fontsize=10)
            bottom += np.array(valores)
        
        # Personalizar gráfico
        ax.set_title(f'Quintiles de {titles[column]}', fontsize=18, fontweight='bold', pad=15)
        ax.set_ylabel('Número de Registros', fontsize=14)
        
        # Usar etiquetas con rangos
        etiquetas = []
        for q in quintiles:
            etiqueta = f"Q{q}\n{limites_quintiles[column][q-1]}"
            etiquetas.append(etiqueta)
        
        ax.set_xticks(quintiles)
        ax.set_xticklabels(etiquetas, fontsize=12, rotation=0, ha='center')
        
        ax.grid(True, alpha=0.3, axis='y')
        
        # Ajustar límites del eje Y
        total_por_quintil = [sum(datos_apilados[size][i] for size in llm_sizes) for i in range(len(quintiles))]
        ax.set_ylim(0, max(total_por_quintil) * 1.15)
        
        # Añadir totales encima de las barras
        for j, total in enumerate(total_por_quintil):
            if total > 0:
                ax.text(quintiles[j], total + 0.8, str(total), 
                       ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        # Hacer las gráficas más anchas
        ax.set_xlim(0.3, 5.7)
    
    # Crear leyenda común en la parte inferior
    ax_leyenda.legend(handles=handles_leyenda, labels=labels_leyenda,
                      title='Tamaño de LLM', title_fontsize=14,
                      fontsize=13, loc='center', ncol=len(llm_sizes),
                      frameon=True, fancybox=True, shadow=True)

    plt.show()

    # (El resto del código de tablas permanece igual...)
    # Mostrar tabla detallada de conteos
    print("\n" + "=" * 100)
    print("TABLA DETALLADA DE CONTEOS POR QUINTIL Y TAMAÑO DE LLM")
    print("=" * 100)
    
    for column, nombre in zip(columnas, [titles[col] for col in columnas]):
        print(f"\n📊 {nombre}:")
        print("-" * 100)
        print(f"{'Quintil (Rango)':<25}", end="")
        for size in llm_sizes:
            print(f"{size.capitalize():<12}", end="")
        print("Total")
        print("-" * 100)
        
        for q in range(1, 6):
            rango = limites_quintiles[column][q-1]
            print(f"Q{q}: {rango:<20}", end="")
            total_q = 0
            for size in llm_sizes:
                count = len(df[(df['llm_size'] == size) & (df[column] == q)])
                print(f"{count:>12}", end="")
                total_q += count
            print(f"{total_q:>12}")
        
        # Totales por tamaño
        print("-" * 100)
        print(f"{'Total':<25}", end="")
        for size in llm_sizes:
            total_size = len(df[(df['llm_size'] == size)])
            print(f"{total_size:>12}", end="")
        print(f"{len(df):>12}")
        
        # Porcentajes
        print(f"{'% del total':<25}", end="")
        for size in llm_sizes:
            total_size = len(df[(df['llm_size'] == size)])
            porcentaje = (total_size / len(df)) * 100
            print(f"{porcentaje:>11.1f}%", end="")
        print(f"{100:>12}%")

def reporte_acierto_tablas():
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    
    # Leer los datos
    df = pd.read_csv('measurements_v3_quintiles.csv')
    
    print("=" * 80)
    print("REPORTE SIMPLE: PORCENTAJE DE ACIERTO EN TABLAS")
    print("=" * 80)
    
    # 1. Calcular diferencia absoluta y porcentaje de acierto
    df['diff_absoluta'] = abs(df['num_tables'] - df['expected_tables'])
    df['porcentaje_acierto'] = (1 - (df['diff_absoluta'] / df['expected_tables'])) * 100
    
    # Asegurar que el porcentaje no sea negativo
    df['porcentaje_acierto'] = df['porcentaje_acierto'].clip(lower=0)
    
    # 2. Agrupar por archivo_puml
    grupos_archivo = df.groupby('archivo_puml')
    
    # 3. Mostrar resultados por archivo
    print("\n📊 RESULTADOS POR ARCHIVO PUML:")
    print("-" * 70)
    
    resultados = []
    for archivo, grupo in grupos_archivo:
        total_registros = len(grupo)
        acierto_promedio = grupo['porcentaje_acierto'].mean()
        acierto_std = grupo['porcentaje_acierto'].std()
        exactos = (grupo['diff_absoluta'] == 0).sum()
        porcentaje_exactos = (exactos / total_registros) * 100
        
        resultados.append({
            'Archivo PUML': archivo,
            'Registros': total_registros,
            'Tablas Esperadas': grupo['expected_tables'].iloc[0],
            '% Acierto Promedio': round(acierto_promedio, 1),
            '% Acierto Mínimo': round(grupo['porcentaje_acierto'].min(), 1),
            '% Acierto Máximo': round(grupo['porcentaje_acierto'].max(), 1),
            'Exactos': exactos,
            '% Exactos': round(porcentaje_exactos, 1),
            'Desviación': round(acierto_std, 1)
        })
    
    # Convertir a DataFrame y mostrar
    df_resultados = pd.DataFrame(resultados)
    print(df_resultados.to_string(index=False))
    
    # 4. Mostrar por modelo dentro de cada archivo
    print("\n📋 DETALLE POR ARCHIVO Y MODELO:")
    print("-" * 70)
    
    for archivo in sorted(df['archivo_puml'].unique()):
        df_archivo = df[df['archivo_puml'] == archivo]
        expected_tables = df_archivo['expected_tables'].iloc[0]
        
        print(f"\n📄 Archivo: {archivo} (Esperadas: {expected_tables} tablas)")
        print(f"{'Modelo':<20} {'Acierto %':<12} {'Exactos':<10} {'Diff Abs':<10}")
        print("-" * 60)
        
        for modelo in sorted(df_archivo['modelo_llm'].unique()):
            df_modelo = df_archivo[df_archivo['modelo_llm'] == modelo]
            acierto_prom = df_modelo['porcentaje_acierto'].mean()
            exactos = (df_modelo['diff_absoluta'] == 0).sum()
            diff_prom = df_modelo['diff_absoluta'].mean()
            
            print(f"{modelo:<20} {acierto_prom:>10.1f}% {exactos:>9}/{len(df_modelo)} {diff_prom:>9.2f}")
    
    # 5. Gráfico simple
    print("\n📈 GRÁFICO DE PORCENTAJE DE ACIERTO POR ARCHIVO:")
    
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Gráfico 1: Barras de acierto promedio
    ax1 = axes[0]
    
    # Ordenar por acierto
    df_resultados_sorted = df_resultados.sort_values('% Acierto Promedio', ascending=False)
    
    bars = ax1.bar(df_resultados_sorted['Archivo PUML'], 
                   df_resultados_sorted['% Acierto Promedio'],
                   color=['#2ecc71', '#3498db', '#e74c3c'][:len(df_resultados_sorted)],
                   edgecolor='black', alpha=0.8)
    
    ax1.set_title('Porcentaje de Acierto Promedio por Archivo', 
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('% Acierto', fontsize=12)
    ax1.set_xlabel('Archivo PUML', fontsize=12)
    ax1.set_ylim(0, 105)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Añadir valores en las barras
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, height + 1,
                f'{height:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # Gráfico 2: Boxplot por archivo
    ax2 = axes[1]
    
    # Crear lista de datos para boxplot
    data_boxplot = []
    labels_boxplot = []
    
    for archivo in df_resultados_sorted['Archivo PUML']:
        data = df[df['archivo_puml'] == archivo]['porcentaje_acierto']
        data_boxplot.append(data)
        labels_boxplot.append(archivo)
    
    box = ax2.boxplot(data_boxplot, labels=labels_boxplot, patch_artist=True)
    
    # Colores para las cajas
    colors = ['#2ecc71', '#3498db', '#e74c3c'][:len(data_boxplot)]
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax2.set_title('Distribución del % de Acierto por Archivo', 
                  fontsize=14, fontweight='bold')
    ax2.set_ylabel('% Acierto', fontsize=12)
    ax2.set_xlabel('Archivo PUML', fontsize=12)
    ax2.set_ylim(0, 105)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=100, color='green', linestyle='--', alpha=0.5, label='100% Acierto')
    ax2.legend()
    
    plt.tight_layout()
    plt.show()
    
    # 6. Resumen estadístico
    print("\n" + "=" * 80)
    print("RESUMEN ESTADÍSTICO")
    print("=" * 80)
    
    acierto_total = df['porcentaje_acierto'].mean()
    exactos_total = (df['diff_absoluta'] == 0).sum()
    total_registros = len(df)
    
    print(f"\n📈 ESTADÍSTICAS GLOBALES:")
    print(f"   • Porcentaje de acierto promedio: {acierto_total:.1f}%")
    print(f"   • Generaciones exactas: {exactos_total}/{total_registros} ({exactos_total/total_registros*100:.1f}%)")
    print(f"   • Desviación estándar: {df['porcentaje_acierto'].std():.1f}%")
    print(f"   • Rango: {df['porcentaje_acierto'].min():.1f}% - {df['porcentaje_acierto'].max():.1f}%")
    
    # 7. Ranking de archivos
    print(f"\n🏆 RANKING DE ARCHIVOS (de más fácil a más difícil):")
    print("-" * 60)
    
    for i, (_, row) in enumerate(df_resultados_sorted.iterrows(), 1):
        print(f"{i}. {row['Archivo PUML']}: {row['% Acierto Promedio']}% acierto "
              f"({row['Exactos']}/{row['Registros']} exactos)")
    
    # 8. Ejemplos de cálculo
    print("\n" + "=" * 80)
    print("EJEMPLOS DE CÁLCULO")
    print("=" * 80)
    
    print("\n📝 FÓRMULA:")
    print("   % Acierto = [1 - (|Generadas - Esperadas| / Esperadas)] × 100")
    
    print("\n📊 EJEMPLOS:")
    ejemplo_data = [
        {'archivo': 'basico.puml', 'esperadas': 6, 'generadas': 6, 'acierto': 100},
        {'archivo': 'basico.puml', 'esperadas': 6, 'generadas': 5, 'acierto': 83.3},
        {'archivo': 'biblio.puml', 'esperadas': 10, 'generadas': 8, 'acierto': 80},
        {'archivo': 'biblio.puml', 'esperadas': 10, 'generadas': 12, 'acierto': 80},
        {'archivo': 'innova.puml', 'esperadas': 19, 'generadas': 19, 'acierto': 100},
    ]
    
    for ejemplo in ejemplo_data:
        diff_abs = abs(ejemplo['generadas'] - ejemplo['esperadas'])
        calc_acierto = (1 - (diff_abs / ejemplo['esperadas'])) * 100
        print(f"   • {ejemplo['archivo']}: Esperadas={ejemplo['esperadas']}, "
              f"Generadas={ejemplo['generadas']}, |Diff|={diff_abs}, "
              f"Acierto={calc_acierto:.1f}%")
    
    return df_resultados

# Ejecutar el reporte
reporte_acierto_tablas()

def heatmap_agrupado_con_size():
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    
    # Leer datos
    df = pd.read_csv('measurements_v3_quintiles.csv')
    
    # Calcular acierto
    df['diff_abs'] = abs(df['num_tables'] - df['expected_tables'])
    df['acierto_%'] = (1 - (df['diff_abs'] / df['expected_tables'])) * 100
    df['acierto_%'] = df['acierto_%'].clip(lower=0)
    
    # Separar por tamaño y crear mapeo
    modelos_small = []
    modelos_standar = []
    modelo_size_map = {}
    
    for modelo in df['modelo_llm'].unique():
        size = df[df['modelo_llm'] == modelo]['llm_size'].iloc[0]
        modelo_size_map[modelo] = size
        
        if size == 'small':
            modelos_small.append(modelo)
        elif size == 'standar':
            modelos_standar.append(modelo)
    
    # Ordenar y combinar
    modelos_small = sorted(modelos_small)
    modelos_standar = sorted(modelos_standar)
    modelos_ordenados = modelos_small + modelos_standar
    
    # Crear pivot table ordenada
    pivot_table = df.pivot_table(
        index='archivo_puml',
        columns='modelo_llm',
        values='acierto_%',
        aggfunc='mean'
    ).round(1)
    
    # Reordenar columnas según el orden deseado
    pivot_table = pivot_table[modelos_ordenados]
    
    # Crear etiquetas personalizadas con tamaño
    column_labels = []
    for modelo in modelos_ordenados:
        size = modelo_size_map.get(modelo, 'N/A')
        column_labels.append(f"{modelo}\n({size})")
    
    # Heatmap
    plt.figure(figsize=(16, 6))
    
    ax = sns.heatmap(pivot_table, 
                     annot=True, 
                     fmt=".1f", 
                     cmap="RdYlGn",
                     vmin=0,
                     vmax=100,
                     linewidths=0.5,
                     cbar_kws={'label': '% Acierto', 'shrink': 0.8})
    
    # Añadir línea separadora
    if modelos_small:
        separador_pos = len(modelos_small)
        ax.axvline(x=separador_pos, color='black', linewidth=2, linestyle='--')
    
    # Aplicar etiquetas personalizadas
    ax.set_xticklabels(column_labels, rotation=45, ha='right', fontsize=9)
    ax.set_yticklabels(pivot_table.index, rotation=0, fontsize=11)
    
    plt.title('Porcentaje de Acierto - Agrupado por Tamaño\n' +
             f'Small ({len(modelos_small)} modelos) | Standar ({len(modelos_standar)} modelos)',
             fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Modelo LLM (tamaño entre paréntesis)', fontsize=12)
    plt.ylabel('Archivo PUML', fontsize=12)
    
    # Añadir leyenda de grupos
    plt.figtext(0.25, 0.01, 'SMALL', ha='center', fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7))
    plt.figtext(0.75, 0.01, 'STANDAR', ha='center', fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.show()
    
    # Mostrar modelos por tamaño con su tamaño
    print("🔵 MODELOS SMALL:")
    for modelo in modelos_small:
        print(f"  • {modelo} ({modelo_size_map[modelo]})")
    
    print("\n🟢 MODELOS STANDAR:")
    for modelo in modelos_standar:
        print(f"  • {modelo} ({modelo_size_map[modelo]})")
    
    return pivot_table


def agregar_porcentaje_acierto_csv():
    import pandas as pd
    import numpy as np
    
    # Leer datos originales
    df = pd.read_csv('measurements_v3_quintiles.csv')
    
    print("=" * 80)
    print("AGREGANDO PORCENTAJE DE ACIERTO AL CSV")
    print("=" * 80)
    
    # 1. Calcular diferencia absoluta y porcentaje de acierto
    df['diff_abs_tables'] = abs(df['num_tables'] - df['expected_tables'])
    df['porcentaje_acierto'] = (1 - (df['diff_abs_tables'] / df['expected_tables'])) * 100
    df['porcentaje_acierto'] = df['porcentaje_acierto'].clip(lower=0)
    
    # 2. Calcular también el porcentaje de error (opcional)
    df['porcentaje_error'] = 100 - df['porcentaje_acierto']
    
    # 3. Calcular exactitud binaria (1 si exacto, 0 si no)
    df['exacto'] = (df['num_tables'] == df['expected_tables']).astype(int)
    
    # 4. Calcular categoría de acierto
    def categorizar_acierto(porcentaje):
        if porcentaje == 100:
            return 'Perfecto (100%)'
        elif porcentaje >= 90:
            return 'Excelente (90-99%)'
        elif porcentaje >= 80:
            return 'Bueno (80-89%)'
        elif porcentaje >= 70:
            return 'Regular (70-79%)'
        elif porcentaje >= 50:
            return 'Aceptable (50-69%)'
        else:
            return 'Pobre (<50%)'
    
    df['categoria_acierto'] = df['porcentaje_acierto'].apply(categorizar_acierto)
    
    # 5. Calcular diferencia con signo (para ver si sobregenera o subgenera)
    df['diff_signed_tables'] = df['num_tables'] - df['expected_tables']
    
    # 6. Añadir columnas descriptivas adicionales
    df['generacion_status'] = df['diff_signed_tables'].apply(
        lambda x: 'Exacta' if x == 0 else ('Sobregenerada' if x > 0 else 'Subgenerada')
    )
    
    # 7. Ordenar columnas para mejor organización
    columnas_ordenadas = [
        # Columnas de identificación
        'test_id', 'llm_size', 'test_name', 'modelo_llm', 'db_type', 'archivo_puml',
        
        # Columnas de tablas (lo más importante primero)
        'expected_tables', 'num_tables', 'diff_signed_tables', 'diff_abs_tables',
        'porcentaje_acierto', 'porcentaje_error', 'exacto', 'categoria_acierto', 'generacion_status',
        
        # Columnas de tiempo
        'total_time_ms', 'rag_time_ms', 'parsing_time_ms', 'rag_time_ms_quintil',
        
        # Columnas de memoria
        'memory_before_mb', 'memory_avg_during_rag_mb', 'memory_final_mb', 'memory_avg_during_rag_mb_quintil',
        
        # Columnas de CPU
        'cpu_before', 'cpu_avg_during_rag', 'cpu_final', 'cpu_avg_during_rag_quintil',
        
        # Columnas de GPU
        'gpu_util_avg_rag', 'gpu_mem_avg_rag', 'gpu_temp_avg_rag',
        'gpu_util_max_rag', 'gpu_mem_max_rag', 'gpu_temp_max_rag', 'gpu_mem_avg_rag_quintil',
        
        # Columnas de éxito/error
        'success', 'error_message', 'timestamp', 'migrations_status'
    ]
    
    # Filtrar solo las columnas que existen en el DataFrame
    columnas_existentes = [col for col in columnas_ordenadas if col in df.columns]
    columnas_restantes = [col for col in df.columns if col not in columnas_existentes]
    
    # Reordenar DataFrame
    df_ordenado = df[columnas_existentes + columnas_restantes]
    
    # 8. Guardar nuevo CSV
    output_file = 'measurements_v3_quintiles_percent.csv'
    df_ordenado.to_csv(output_file, index=False)
    
    print(f"✓ Nuevo archivo creado: {output_file}")
    print(f"✓ Total de registros: {len(df)}")
    print(f"✓ Columnas añadidas:")
    print(f"  • diff_abs_tables: Diferencia absoluta de tablas")
    print(f"  • porcentaje_acierto: % de acierto (0-100%)")
    print(f"  • porcentaje_error: % de error (100 - acierto)")
    print(f"  • exacto: 1 si es exacto, 0 si no")
    print(f"  • categoria_acierto: Categoría descriptiva")
    print(f"  • diff_signed_tables: Diferencia con signo")
    print(f"  • generacion_status: Estado de generación")
    
    # 9. Mostrar estadísticas resumen
    print("\n📊 ESTADÍSTICAS DE ACIERTO:")
    print("-" * 50)
    
    acierto_promedio = df['porcentaje_acierto'].mean()
    exactos = df['exacto'].sum()
    porcentaje_exactos = (exactos / len(df)) * 100
    
    print(f"Porcentaje de acierto promedio: {acierto_promedio:.2f}%")
    print(f"Generaciones exactas: {exactos}/{len(df)} ({porcentaje_exactos:.2f}%)")
    print(f"Mínimo acierto: {df['porcentaje_acierto'].min():.2f}%")
    print(f"Máximo acierto: {df['porcentaje_acierto'].max():.2f}%")
    
    # Distribución por categoría
    print("\n📈 DISTRIBUCIÓN POR CATEGORÍA DE ACIERTO:")
    print("-" * 50)
    
    distribucion = df['categoria_acierto'].value_counts().sort_index()
    for categoria, cantidad in distribucion.items():
        porcentaje = (cantidad / len(df)) * 100
        print(f"{categoria:<25} {cantidad:>4} registros ({porcentaje:>6.2f}%)")
    
    # Por archivo PUML
    print("\n📄 POR ARCHIVO PUML:")
    print("-" * 50)
    
    for archivo in sorted(df['archivo_puml'].unique()):
        df_archivo = df[df['archivo_puml'] == archivo]
        acierto_prom = df_archivo['porcentaje_acierto'].mean()
        exactos_archivo = df_archivo['exacto'].sum()
        print(f"{archivo:<15} Acierto: {acierto_prom:>6.2f}%  Exactos: {exactos_archivo:>3}/{len(df_archivo)}")
    
    # Por modelo LLM
    print("\n🤖 POR MODELO LLM:")
    print("-" * 50)
    
    for modelo in sorted(df['modelo_llm'].unique()):
        df_modelo = df[df['modelo_llm'] == modelo]
        acierto_prom = df_modelo['porcentaje_acierto'].mean()
        exactos_modelo = df_modelo['exacto'].sum()
        print(f"{modelo:<20} Acierto: {acierto_prom:>6.2f}%  Exactos: {exactos_modelo:>3}/{len(df_modelo)}")
    
    # 10. Mostrar primeras filas del nuevo archivo
    print("\n👀 PRIMERAS 5 FILAS DEL NUEVO ARCHIVO:")
    print("-" * 80)
    
    columnas_muestra = ['test_id', 'modelo_llm', 'archivo_puml', 
                       'expected_tables', 'num_tables', 'porcentaje_acierto',
                       'categoria_acierto', 'generacion_status']
    
    print(df_ordenado[columnas_muestra].head().to_string())
    
    # 11. Crear también un archivo resumen (opcional)
    resumen_file = 'measurements_v3_summary_stats.csv'
    
    # Calcular estadísticas por grupo
    grupos = ['modelo_llm', 'archivo_puml', 'llm_size', 'db_type']
    
    for grupo in grupos:
        if grupo in df.columns:
            resumen = df.groupby(grupo).agg({
                'porcentaje_acierto': ['mean', 'std', 'min', 'max'],
                'exacto': 'sum',
                'test_id': 'count'
            }).round(2)
            
            # Renombrar columnas
            resumen.columns = ['acierto_promedio', 'acierto_std', 'acierto_min', 
                              'acierto_max', 'exactos', 'total_registros']
            
            # Calcular porcentaje de exactos
            resumen['%_exactos'] = (resumen['exactos'] / resumen['total_registros'] * 100).round(2)
            
            # Guardar resumen por grupo
            resumen.to_csv(f'measurements_v3_summary_by_{grupo}.csv')
            print(f"✓ Archivo resumen creado: measurements_v3_summary_by_{grupo}.csv")
    
    print(f"\n✅ Proceso completado exitosamente!")
    print(f"📁 Archivo principal: {output_file}")
    print(f"📊 Archivos de resumen: measurements_v3_summary_by_*.csv")
    
    return df_ordenado

# Ejecutar la función
df_nuevo = agregar_porcentaje_acierto_csv()

# Ejecutar
#heatmap_agrupado_con_size()
# Ejecutar
# Ejecutar la función
#quintiles_cantidad_llm()
#quintiles_cantidad()
#quintil()
#csv_quintil()