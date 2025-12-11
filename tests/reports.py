import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.gridspec import GridSpec

def reports1():
  # Cargar datos
    df = pd.read_csv('measurements_v1.csv')
    
    # Calcular éxito real basado en num_tables == expected_tables
    df['success_real'] = df['num_tables'] == df['expected_tables']
    
    # 1. Gráfico de tiempo total por modelo (solo éxitos para comparación justa)
    plt.figure(figsize=(14, 8))
    
    # Separar éxitos y fracasos
    df_success = df[df['success_real']]
    df_failure = df[~df['success_real']]
    
    # Tiempo promedio por modelo (éxitos)
    time_success = df_success.groupby('modelo_llm')['total_time_ms'].mean().sort_values()
    
    # Tiempo promedio por modelo (todos, para comparación)
    time_all = df.groupby('modelo_llm')['total_time_ms'].mean().reindex(time_success.index)
    
    # Crear gráfico de barras doble
    x = np.arange(len(time_success))
    width = 0.35
    
    plt.bar(x - width/2, time_success.values / 1000, width, 
            label='Solo Éxitos', color='#2ecc71', alpha=0.8)
    plt.bar(x + width/2, time_all.values / 1000, width, 
            label='Todos los Casos', color='#e74c3c', alpha=0.6)
    
    plt.xlabel('Modelo LLM')
    plt.ylabel('Tiempo Promedio (segundos)')
    plt.title('Tiempo Total Promedio por Modelo\n(Comparación: Éxitos vs Todos los Casos)')
    plt.xticks(x, [m[:20] + '...' if len(m) > 20 else m for m in time_success.index], 
               rotation=45, ha='right')
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    
    # Añadir línea de promedio general
    avg_success = time_success.mean() / 1000
    avg_all = time_all.mean() / 1000
    plt.axhline(y=avg_success, color='green', linestyle='--', alpha=0.5, linewidth=1)
    plt.axhline(y=avg_all, color='red', linestyle='--', alpha=0.5, linewidth=1)
    
    plt.text(len(time_success)-1, avg_success + 0.5, 
             f'Avg éxitos: {avg_success:.1f}s', ha='right', color='green')
    plt.text(len(time_success)-1, avg_all + 0.5, 
             f'Avg total: {avg_all:.1f}s', ha='right', color='red')
    
    plt.tight_layout()
    plt.show()
    
    # 2. Éxito por modelo (nueva definición)
    plt.figure(figsize=(14, 8))
    
    # Calcular tasa de éxito
    success_stats = df.groupby('modelo_llm').agg({
        'success_real': ['count', 'sum']
    })
    success_stats.columns = ['total_tests', 'successful_tests']
    success_stats['success_rate'] = success_stats['successful_tests'] / success_stats['total_tests']
    success_stats = success_stats.sort_values('success_rate', ascending=False)
    
    # Crear gráfico de barras
    bars = plt.bar(range(len(success_stats)), 
                   success_stats['success_rate'],
                   color=['#2ecc71' if rate == 1.0 else 
                          '#f1c40f' if rate >= 0.5 else 
                          '#e74c3c' for rate in success_stats['success_rate']],
                   alpha=0.8)
    
    plt.xlabel('Modelo LLM')
    plt.ylabel('Tasa de Éxito')
    plt.title('Tasa de Éxito por Modelo\n(Éxito = num_tables == expected_tables)')
    plt.xticks(range(len(success_stats)), 
               [m[:20] + '...' if len(m) > 20 else m for m in success_stats.index], 
               rotation=45, ha='right')
    
    # Líneas de referencia
    plt.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    plt.axhline(y=1.0, color='green', linestyle='-', alpha=0.3, linewidth=2)
    
    # Añadir valores y conteos
    for i, (bar, rate) in enumerate(zip(bars, success_stats['success_rate'])):
        height = bar.get_height()
        total = success_stats.iloc[i]['total_tests']
        success = success_stats.iloc[i]['successful_tests']
        
        plt.text(bar.get_x() + bar.get_width()/2, height + 0.02,
                 f'{rate:.0%}\n({success}/{total})',
                 ha='center', va='bottom', fontsize=9,
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    plt.ylim(0, 1.15)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Leyenda de colores
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2ecc71', label='100% Éxito (Perfecto)'),
        Patch(facecolor='#f1c40f', label='50-99% Éxito (Aceptable)'),
        Patch(facecolor='#e74c3c', label='<50% Éxito (Deficiente)')
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    plt.show()
    
    # 3. Comparación de recursos (solo para modelos exitosos)
    plt.figure(figsize=(16, 10))
    
    # Seleccionar modelos para comparación (top 3 por tasa de éxito y otros interesantes)
    top_success = success_stats.head(3).index.tolist()
    
    # Añadir algunos modelos grandes para comparación
    models_to_compare = list(set(top_success + [
        'llama3.2:3b', 
        'qwen2.5:7', 
        'deepseek-r1:7b',
        'mistral:7b',
        'BERT + t5small'  # Modelo especial
    ]))
    
    # Filtrar datos
    subset = df_success[df_success['modelo_llm'].isin(models_to_compare)]
    
    # Crear subplots para diferentes métricas
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 3a. Memoria
    sns.boxplot(ax=axes[0, 0], data=subset, x='modelo_llm', y='memory_avg_during_rag_mb',
                palette='viridis')
    axes[0, 0].set_title('Uso de Memoria durante RAG\n(solo casos exitosos)')
    axes[0, 0].set_ylabel('Memoria (MB)')
    axes[0, 0].set_xlabel('')
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # Añadir media como punto
    means = subset.groupby('modelo_llm')['memory_avg_during_rag_mb'].mean()
    for i, model in enumerate(models_to_compare):
        if model in means.index:
            axes[0, 0].plot(i, means[model], 'ro', markersize=8, label='Media' if i == 0 else "")
    
    # 3b. CPU
    sns.boxplot(ax=axes[0, 1], data=subset, x='modelo_llm', y='cpu_avg_during_rag',
                palette='coolwarm')
    axes[0, 1].set_title('Uso de CPU durante RAG\n(solo casos exitosos)')
    axes[0, 1].set_ylabel('CPU (%)')
    axes[0, 1].set_xlabel('')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # 3c. GPU Utilización
    if 'gpu_util_avg_rag' in subset.columns:
        sns.boxplot(ax=axes[1, 0], data=subset, x='modelo_llm', y='gpu_util_avg_rag',
                    palette='plasma')
        axes[1, 0].set_title('Utilización de GPU durante RAG\n(solo casos exitosos)')
        axes[1, 0].set_ylabel('GPU Utilización (%)')
        axes[1, 0].set_xlabel('Modelo LLM')
        axes[1, 0].tick_params(axis='x', rotation=45)
    
    # 3d. Tiempo RAG vs Tiempo Total
    axes[1, 1].scatter(subset['rag_time_ms'] / 1000, subset['total_time_ms'] / 1000,
                       c=subset.index, cmap='tab20', alpha=0.7, s=100)
    
    # Añadir etiquetas para algunos puntos destacados
    for model in models_to_compare[:3]:  # Solo top 3 para claridad
        model_data = subset[subset['modelo_llm'] == model]
        if not model_data.empty:
            rag_mean = model_data['rag_time_ms'].mean() / 1000
            total_mean = model_data['total_time_ms'].mean() / 1000
            axes[1, 1].annotate(model[:10], 
                               (rag_mean, total_mean),
                               fontsize=9,
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    axes[1, 1].set_xlabel('Tiempo RAG (segundos)')
    axes[1, 1].set_ylabel('Tiempo Total (segundos)')
    axes[1, 1].set_title('Relación Tiempo RAG vs Tiempo Total\n(solo casos exitosos)')
    axes[1, 1].grid(True, alpha=0.3)
    
    # Línea de relación 1:1
    max_val = max(subset['rag_time_ms'].max()/1000, subset['total_time_ms'].max()/1000)
    axes[1, 1].plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='y = x')
    axes[1, 1].legend()
    
    plt.suptitle('Comparación de Recursos por Modelo\n(Análisis solo de casos exitosos)', 
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.show()
    
    # 4. RESUMEN ESTADÍSTICO
    print("=" * 80)
    print("RESUMEN ESTADÍSTICO - reports1()")
    print("=" * 80)
    
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"   • Total de pruebas: {len(df)}")
    print(f"   • Pruebas exitosas: {len(df_success)} ({len(df_success)/len(df):.1%})")
    print(f"   • Pruebas fallidas: {len(df_failure)} ({len(df_failure)/len(df):.1%})")
    
    print(f"\n⏱️  TIEMPOS PROMEDIO:")
    print(f"   • Todos los casos: {df['total_time_ms'].mean()/1000:.1f}s")
    print(f"   • Solo éxitos: {df_success['total_time_ms'].mean()/1000:.1f}s")
    print(f"   • Solo fallos: {df_failure['total_time_ms'].mean()/1000:.1f}s" if len(df_failure) > 0 else "   • Solo fallos: N/A")
    
    print(f"\n🏆 TOP 3 MODELOS POR TASA DE ÉXITO:")
    for i, (model, row) in enumerate(success_stats.head(3).iterrows(), 1):
        print(f"   {i}. {model:<25} {row['success_rate']:.0%} ({row['successful_tests']}/{row['total_tests']})")
    
    print(f"\n⚠️  MODELOS CON PROBLEMAS (<50% éxito):")
    problematic = success_stats[success_stats['success_rate'] < 0.5]
    if len(problematic) > 0:
        for model, row in problematic.iterrows():
            print(f"   • {model:<25} {row['success_rate']:.0%} ({row['successful_tests']}/{row['total_tests']})")
    else:
        print("   Ningún modelo tiene menos del 50% de éxito")
    
    print("\n" + "=" * 80)

def reports2():
  # Cargar datos
  df = pd.read_csv('measurements_v1.csv')

  # 1. Calcular el éxito real basado en num_tables == expected_tables
  df['success_real'] = df['num_tables'] == df['expected_tables']

  # 2. Agrupar por modelo y calcular tasa de éxito
  success_by_model = df.groupby('modelo_llm').agg({
      'success_real': ['count', 'sum', 'mean']
  }).round(3)

  # Renombrar columnas para claridad
  success_by_model.columns = ['total_tests', 'successful_tests', 'success_rate']
  success_by_model = success_by_model.sort_values('success_rate', ascending=False)

  # Mostrar tabla de resultados
  print("=" * 80)
  print("TASA DE ÉXITO POR MODELO (num_tables == expected_tables)")
  print("=" * 80)
  print(success_by_model)
  print("\n" + "=" * 80)
  print(f"Tasa de éxito global: {success_by_model['successful_tests'].sum()}/{success_by_model['total_tests'].sum()} = {success_by_model['successful_tests'].sum()/success_by_model['total_tests'].sum():.2%}")
  print("=" * 80)

  # 3. Gráfico de barras de tasa de éxito
  plt.figure(figsize=(14, 8))

  # Crear barras
  bars = plt.bar(range(len(success_by_model)), 
                success_by_model['success_rate'], 
                color=['#2ecc71' if rate >= 0.5 else '#e74c3c' for rate in success_by_model['success_rate']])

  # Personalizar eje X
  plt.xticks(range(len(success_by_model)), 
            success_by_model.index, 
            rotation=45, ha='right')

  # Etiquetas y título
  plt.ylabel('Tasa de Éxito', fontsize=12)
  plt.title('Tasa de Éxito por Modelo LLM\n(Éxito = num_tables == expected_tables)', 
            fontsize=14, fontweight='bold', pad=20)

  # Añadir línea horizontal en 50% y 100%
  plt.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1)
  plt.axhline(y=1.0, color='green', linestyle='--', alpha=0.5, linewidth=1)

  # Añadir etiquetas de valor encima de cada barra
  for i, (bar, rate) in enumerate(zip(bars, success_by_model['success_rate'])):
      height = bar.get_height()
      plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
              f'{rate:.0%}\n({success_by_model.iloc[i]["successful_tests"]}/{success_by_model.iloc[i]["total_tests"]})',
              ha='center', va='bottom', fontsize=9)

  # Configurar límites del eje Y
  plt.ylim(0, 1.1)

  plt.tight_layout()
  plt.show()

  # 4. Gráfico de pastel para distribución de éxito/fracaso
  plt.figure(figsize=(12, 10))

  # Contar éxitos y fracasos
  success_count = success_by_model['successful_tests'].sum()
  failure_count = success_by_model['total_tests'].sum() - success_count

  # Crear gráfico de pastel
  labels = ['Éxitos', 'Fracasos']
  sizes = [success_count, failure_count]
  colors = ['#2ecc71', '#e74c3c']
  explode = (0.1, 0)  # Resaltar éxitos

  plt.pie(sizes, explode=explode, labels=labels, colors=colors,
          autopct='%1.1f%%', shadow=True, startangle=90)
  plt.title('Distribución Global de Éxito/Fracaso\n' + 
            f'({success_count} éxitos de {success_count + failure_count} pruebas)', 
            fontsize=14, fontweight='bold')

  plt.axis('equal')  # Para que sea un círculo perfecto
  plt.tight_layout()
  plt.show()

  # 5. Análisis detallado por modelo y archivo PUML
  print("\n" + "=" * 80)
  print("ANÁLISIS DETALLADO POR MODELO Y ARCHIVO PUML")
  print("=" * 80)

  # Crear tabla pivot para ver éxito por modelo y archivo
  pivot_table = df.pivot_table(
      index='modelo_llm',
      columns='archivo_puml',
      values='success_real',
      aggfunc=['count', 'sum']
  )

  # Renombrar columnas para claridad
  pivot_table.columns = [f'{col[2]}_{col[0]}' for col in pivot_table.columns]

  # Calcular tasas
  for puml_file in ['basico.puml', 'innova.puml']:
      count_col = f'{puml_file}_count'
      sum_col = f'{puml_file}_sum'
      if count_col in pivot_table.columns and sum_col in pivot_table.columns:
          pivot_table[f'{puml_file}_rate'] = pivot_table[sum_col] / pivot_table[count_col]

  print(pivot_table.round(3))

  # 6. Gráfico de calor para éxito por modelo y archivo
  plt.figure(figsize=(12, 8))

  # Preparar datos para el heatmap
  heatmap_data = pd.DataFrame()
  for puml_file in ['basico.puml', 'innova.puml']:
      rate_col = f'{puml_file}_rate'
      if rate_col in pivot_table.columns:
          heatmap_data[puml_file] = pivot_table[rate_col]

  # Crear heatmap
  if not heatmap_data.empty:
      plt.imshow(heatmap_data.T, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
      plt.colorbar(label='Tasa de Éxito')
      
      # Etiquetas
      plt.yticks(range(len(heatmap_data.columns)), heatmap_data.columns)
      plt.xticks(range(len(heatmap_data.index)), 
                [str(x)[:20] + '...' if len(str(x)) > 20 else str(x) for x in heatmap_data.index],
                rotation=45, ha='right')
      
      # Añadir valores en las celdas
      for i in range(len(heatmap_data.columns)):
          for j in range(len(heatmap_data.index)):
              value = heatmap_data.iloc[j, i]
              if not pd.isna(value):
                  plt.text(j, i, f'{value:.0%}', 
                          ha='center', va='center',
                          color='white' if value < 0.5 else 'black',
                          fontweight='bold')
      
      plt.title('Tasa de Éxito por Modelo y Archivo PUML', fontsize=14, fontweight='bold')
      plt.xlabel('Modelo LLM')
      plt.tight_layout()
      plt.show()

  # 7. Ranking de modelos por tasa de éxito
  print("\n" + "=" * 80)
  print("RANKING DE MODELOS POR TASA DE ÉXITO")
  print("=" * 80)

  ranking = success_by_model[['success_rate', 'total_tests', 'successful_tests']].copy()
  ranking['rank'] = ranking['success_rate'].rank(method='dense', ascending=False).astype(int)
  ranking = ranking.sort_values('rank')

  for idx, (model, row) in enumerate(ranking.iterrows(), 1):
      status = "✅ EXCELENTE" if row['success_rate'] >= 0.9 else \
              "👍 BUENO" if row['success_rate'] >= 0.7 else \
              "⚠️  REGULAR" if row['success_rate'] >= 0.5 else \
              "❌ DEFICIENTE"
      
      print(f"{row['rank']:2d}. {model:<30} {status:<15} {row['success_rate']:.0%} ({row['successful_tests']}/{row['total_tests']})")

def reports3():
  import pandas as pd
  import matplotlib.pyplot as plt
  import seaborn as sns
  import numpy as np
  from matplotlib.gridspec import GridSpec

  # Cargar datos
  df = pd.read_csv('measurements_v1.csv')

  # Filtrar solo casos exitosos
  df_success = df[df['num_tables'] == df['expected_tables']].copy()

  print("=" * 80)
  print(f"ANÁLISIS DE CASOS EXITOSOS: {len(df_success)} de {len(df)} pruebas")
  print("=" * 80)

  # 1. ANÁLISIS ESTADÍSTICO POR MODELO
  print("\nESTADÍSTICAS POR MODELO (solo éxitos):")
  print("-" * 80)

  # Calcular estadísticas por modelo
  stats_by_model = df_success.groupby('modelo_llm').agg({
      'total_time_ms': ['count', 'mean', 'std', 'min', 'max'],
      'rag_time_ms': 'mean',
      'memory_avg_during_rag_mb': 'mean',
      'cpu_avg_during_rag': 'mean',
      'gpu_util_avg_rag': 'mean',
      'gpu_mem_avg_rag': 'mean'
  }).round(2)

  # Renombrar columnas
  stats_by_model.columns = [
      'num_tests', 'time_mean', 'time_std', 'time_min', 'time_max',
      'rag_time_mean', 'memory_mean', 'cpu_mean', 'gpu_util_mean', 'gpu_mem_mean'
  ]

  print(stats_by_model)

  # Función auxiliar para normalización
  def normalize_series(series):
      return (series - series.min()) / (series.max() - series.min())

  # FIGURA 1: GRÁFICO DE RADAR PARA 5 MODELOS MÁS RÁPIDOS
  print("\n" + "=" * 80)
  print("FIGURA 1: COMPARACIÓN RADAR DE LOS 5 MODELOS MÁS RÁPIDOS")
  print("=" * 80)

  fig1 = plt.figure(figsize=(10, 8))
  ax1 = plt.subplot(111, projection='polar')

  # Preparar datos normalizados
  model_names = stats_by_model.index.tolist()
  time_norm = normalize_series(stats_by_model['time_mean'])
  memory_norm = normalize_series(stats_by_model['memory_mean'])
  cpu_norm = normalize_series(stats_by_model['cpu_mean'])
  gpu_norm = normalize_series(stats_by_model['gpu_util_mean'])

  # Seleccionar top 5 modelos para claridad
  top_models = stats_by_model.sort_values('time_mean').head(5).index
  colors = plt.cm.Set2(np.linspace(0, 1, len(top_models)))

  metrics = ['Tiempo\n(↓ mejor)', 'Memoria\n(↓ mejor)', 'CPU\n(↓ mejor)', 'GPU\n(↓ mejor)']
  num_vars = len(metrics)

  for idx, model in enumerate(top_models):
      values = [
          1 - time_norm[model],  # Invertir porque menor tiempo es mejor
          1 - memory_norm[model],  # Invertir porque menor memoria es mejor
          1 - cpu_norm[model],  # Invertir porque menor CPU es mejor
          1 - gpu_norm[model]  # Invertir porque menor GPU es mejor
      ]
      
      # Cerrar el círculo
      values = values + values[:1]
      
      # Calcular ángulos
      angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
      angles += angles[:1]
      
      ax1.plot(angles, values, 'o-', linewidth=2, label=model, color=colors[idx])
      ax1.fill(angles, values, alpha=0.1, color=colors[idx])

  ax1.set_xticks(angles[:-1])
  ax1.set_xticklabels(metrics, fontsize=10)
  ax1.set_ylim(0, 1)
  ax1.set_title('Comparación Radar de los 5 Modelos Más Rápidos\n(valores normalizados invertidos: más alto = mejor)', 
                fontsize=12, fontweight='bold', pad=20)
  ax1.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=9)
  ax1.grid(True, alpha=0.3)

  plt.tight_layout()
  plt.show()

  # FIGURA 2: GRÁFICO DE BARRAS AGRUPADAS - TIEMPO Y MEMORIA
  print("\n" + "=" * 80)
  print("FIGURA 2: TIEMPO vs MEMORIA (NORMALIZADO)")
  print("=" * 80)

  fig2, ax2 = plt.subplots(figsize=(14, 8))

  x = np.arange(len(model_names))
  width = 0.35

  # Normalizar para comparación relativa
  time_norm_all = normalize_series(stats_by_model['time_mean'])
  memory_norm_all = normalize_series(stats_by_model['memory_mean'])

  bars1 = ax2.bar(x - width/2, time_norm_all, width, label='Tiempo (norm)', color='#3498db', alpha=0.7)
  bars2 = ax2.bar(x + width/2, memory_norm_all, width, label='Memoria (norm)', color='#2ecc71', alpha=0.7)

  ax2.set_xlabel('Modelo', fontsize=11)
  ax2.set_ylabel('Valor Normalizado (0-1)', fontsize=11)
  ax2.set_title('Tiempo vs Memoria (normalizado)\n↓ menor = mejor', fontsize=13, fontweight='bold')
  ax2.set_xticks(x)
  ax2.set_xticklabels([m[:15] + '...' if len(m) > 15 else m for m in model_names], 
                      rotation=45, ha='right', fontsize=9)
  ax2.legend(fontsize=10)
  ax2.grid(True, alpha=0.3, axis='y')

  # Añadir valores reales
  for i, (bar_time, bar_mem) in enumerate(zip(bars1, bars2)):
      time_val = stats_by_model.iloc[i]['time_mean']
      mem_val = stats_by_model.iloc[i]['memory_mean']
      ax2.text(bar_time.get_x() + bar_time.get_width()/2, bar_time.get_height() + 0.02,
              f'{time_val/1000:.0f}s', ha='center', va='bottom', fontsize=8)
      ax2.text(bar_mem.get_x() + bar_mem.get_width()/2, bar_mem.get_height() + 0.02,
              f'{mem_val:.0f}MB', ha='center', va='bottom', fontsize=8)

  plt.tight_layout()
  plt.show()

  # FIGURA 3: GRÁFICO DE DISPERSIÓN - TIEMPO vs RECURSOS
  print("\n" + "=" * 80)
  print("FIGURA 3: TIEMPO vs MEMORIA vs CPU vs GPU")
  print("=" * 80)

  fig3, ax3 = plt.subplots(figsize=(12, 8))

  scatter = ax3.scatter(stats_by_model['time_mean'] / 1000,  # Convertir a segundos
                        stats_by_model['memory_mean'],
                        s=stats_by_model['cpu_mean'] * 10,  # Tamaño por uso de CPU
                        c=stats_by_model['gpu_util_mean'],
                        cmap='viridis',
                        alpha=0.7,
                        edgecolors='black',
                        linewidth=1)

  # Añadir etiquetas de modelos
  for i, model in enumerate(model_names):
      ax3.annotate(model[:12] + '...' if len(model) > 12 else model,
                  (stats_by_model.iloc[i]['time_mean'] / 1000,
                  stats_by_model.iloc[i]['memory_mean']),
                  fontsize=8, alpha=0.7,
                  bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

  ax3.set_xlabel('Tiempo Promedio (segundos)', fontsize=11)
  ax3.set_ylabel('Memoria Promedio (MB)', fontsize=11)
  ax3.set_title('Tiempo vs Memoria vs CPU vs GPU\n(Tamaño = CPU %, Color = GPU %)', 
                fontsize=13, fontweight='bold')
  ax3.grid(True, alpha=0.3)

  # Barra de color para GPU
  cbar = plt.colorbar(scatter, ax=ax3)
  cbar.set_label('Uso de GPU (%)', fontsize=11)

  # Leyenda para tamaño de puntos (CPU)
  from matplotlib.lines import Line2D
  legend_elements = [
      Line2D([0], [0], marker='o', color='w', label='CPU 10%',
            markerfacecolor='gray', markersize=6),
      Line2D([0], [0], marker='o', color='w', label='CPU 50%',
            markerfacecolor='gray', markersize=12),
      Line2D([0], [0], marker='o', color='w', label='CPU 100%',
            markerfacecolor='gray', markersize=20)
  ]
  ax3.legend(handles=legend_elements, title='Tamaño del punto:', 
            loc='upper right', fontsize=9)

  plt.tight_layout()
  plt.show()

  # FIGURA 4: GRÁFICO DE LÍNEAS - COMPARATIVA DE MÚLTIPLES MÉTRICAS
  print("\n" + "=" * 80)
  print("FIGURA 4: COMPARATIVA DE TODAS LAS MÉTRICAS")
  print("=" * 80)

  fig4, ax4 = plt.subplots(figsize=(14, 8))

  # Normalizar todas las métricas para comparación
  metrics_to_plot = ['time_mean', 'memory_mean', 'cpu_mean', 'gpu_util_mean']
  labels = ['Tiempo', 'Memoria', 'CPU', 'GPU']
  colors_line = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
  markers = ['o', 's', '^', 'D']

  x_pos = np.arange(len(model_names))

  for metric, label, color, marker in zip(metrics_to_plot, labels, colors_line, markers):
      normalized = normalize_series(stats_by_model[metric])
      ax4.plot(x_pos, normalized, marker=marker, label=label, color=color, 
              linewidth=2, alpha=0.7, markersize=8)

  ax4.set_xlabel('Modelo LLM', fontsize=11)
  ax4.set_ylabel('Valor Normalizado (0-1)', fontsize=11)
  ax4.set_title('Comparativa de Todas las Métricas por Modelo\n(0 = mejor, 1 = peor)', 
                fontsize=13, fontweight='bold')
  ax4.set_xticks(x_pos)
  ax4.set_xticklabels([m[:12] + '...' for m in model_names], rotation=45, ha='right', fontsize=9)
  ax4.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
  ax4.grid(True, alpha=0.3)
  ax4.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1)

  plt.tight_layout()
  plt.show()

  # FIGURA 5: GRÁFICO DE BARRAS APILADAS - CONTRIBUCIÓN RELATIVA
  print("\n" + "=" * 80)
  print("FIGURA 5: CONTRIBUCIÓN RELATIVA DE RECURSOS")
  print("=" * 80)

  fig5, ax5 = plt.subplots(figsize=(14, 8))

  # Calcular contribución relativa de cada recurso
  resources = ['memory_mean', 'cpu_mean', 'gpu_util_mean']
  resource_labels = ['Memoria', 'CPU', 'GPU']
  resource_colors = ['#3498db', '#2ecc71', '#f39c12']

  # Normalizar cada recurso entre 0-1 por modelo
  resource_data = np.zeros((len(model_names), len(resources)))
  for i, resource in enumerate(resources):
      resource_data[:, i] = normalize_series(stats_by_model[resource])

  # Gráfico de barras apiladas
  bottom = np.zeros(len(model_names))
  for i, (resource, label, color) in enumerate(zip(resources, resource_labels, resource_colors)):
      ax5.bar([m[:10] + '...' for m in model_names], 
              resource_data[:, i], 
              bottom=bottom, 
              label=label, 
              color=color,
              alpha=0.7,
              edgecolor='white',
              linewidth=0.5)
      bottom += resource_data[:, i]

  ax5.set_xlabel('Modelo LLM', fontsize=11)
  ax5.set_ylabel('Uso Relativo de Recursos (0-3)', fontsize=11)
  ax5.set_title('Contribución Relativa de Recursos por Modelo\n(Valores normalizados 0-1 por recurso)', 
                fontsize=13, fontweight='bold')
  ax5.set_xticklabels([m[:10] + '...' for m in model_names], rotation=45, ha='right', fontsize=9)
  ax5.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fontsize=10)
  ax5.grid(True, alpha=0.3, axis='y')

  # Añadir línea horizontal en cada nivel
  for level in [0.5, 1.0, 1.5, 2.0, 2.5]:
      ax5.axhline(y=level, color='gray', linestyle=':', alpha=0.3, linewidth=0.5)

  plt.tight_layout()
  plt.show()

  # 3. TABLA DE RANKING MULTICRITERIO
  print("\n" + "=" * 80)
  print("RANKING MULTICRITERIO DE MODELOS EXITOSOS")
  print("=" * 80)

  # Calcular puntuación compuesta (menor es mejor en todos los casos)
  stats_by_model['score_time'] = normalize_series(stats_by_model['time_mean'])
  stats_by_model['score_memory'] = normalize_series(stats_by_model['memory_mean'])
  stats_by_model['score_cpu'] = normalize_series(stats_by_model['cpu_mean'])
  stats_by_model['score_gpu'] = normalize_series(stats_by_model['gpu_util_mean'])

  # Puntuación total (promedio de todas las métricas normalizadas)
  stats_by_model['total_score'] = (
      stats_by_model['score_time'] + 
      stats_by_model['score_memory'] + 
      stats_by_model['score_cpu'] + 
      stats_by_model['score_gpu']
  ) / 4

  # Ordenar por puntuación total (menor es mejor)
  ranking = stats_by_model.sort_values('total_score')[['total_score', 'time_mean', 'memory_mean', 'cpu_mean', 'gpu_util_mean']]

  print("\nTop 10 Modelos Más Eficientes (combinando tiempo y recursos):")
  print("-" * 80)
  for i, (model, row) in enumerate(ranking.head(10).iterrows(), 1):
      print(f"{i:2d}. {model:<30} "
            f"Score: {row['total_score']:.3f} | "
            f"Tiempo: {row['time_mean']/1000:.1f}s | "
            f"Mem: {row['memory_mean']:.0f}MB | "
            f"CPU: {row['cpu_mean']:.1f}% | "
            f"GPU: {row['gpu_util_mean']:.1f}%")

  # FIGURA 6: GRÁFICO DE RANKING DE EFICIENCIA
  print("\n" + "=" * 80)
  print("FIGURA 6: RANKING DE EFICIENCIA MULTICRITERIO")
  print("=" * 80)

  fig6, (ax6a, ax6b) = plt.subplots(1, 2, figsize=(16, 8))

  # Gráfico 6a: Puntuación total
  top_n = min(15, len(ranking))
  top_models = ranking.head(top_n)

  colors_score = plt.cm.RdYlGn_r((top_models['total_score'] - top_models['total_score'].min()) / 
                                (top_models['total_score'].max() - top_models['total_score'].min()))

  bars = ax6a.barh(range(len(top_models)), top_models['total_score'], color=colors_score)
  ax6a.set_yticks(range(len(top_models)))
  ax6a.set_yticklabels([m[:20] + '...' if len(m) > 20 else m for m in top_models.index], fontsize=9)
  ax6a.set_xlabel('Puntuación de Eficiencia (menor = mejor)', fontsize=11)
  ax6a.set_title('Ranking de Eficiencia de Modelos\n(Puntuación combinada: tiempo + recursos)', 
                fontsize=12, fontweight='bold')
  ax6a.invert_yaxis()  # Mejor modelo en la parte superior
  ax6a.grid(True, alpha=0.3, axis='x')

  # Añadir valores en las barras
  for i, (bar, score) in enumerate(zip(bars, top_models['total_score'])):
      ax6a.text(score + 0.01, bar.get_y() + bar.get_height()/2,
              f'{score:.3f}', ha='left', va='center', fontsize=9,
              bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

  # Gráfico 6b: Desglose de puntuaciones
  bottom = np.zeros(len(top_models))
  score_components = ['score_time', 'score_memory', 'score_cpu', 'score_gpu']
  component_labels = ['Tiempo', 'Memoria', 'CPU', 'GPU']
  component_colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']

  for i, (score_col, label, color) in enumerate(zip(score_components, component_labels, component_colors)):
      values = top_models[score_col] / 4  # Dividir por 4 porque cada componente contribuye 1/4
      ax6b.barh(range(len(top_models)), values, left=bottom, 
                label=label, color=color, alpha=0.7)
      bottom += values

  ax6b.set_yticks(range(len(top_models)))
  ax6b.set_yticklabels([])  # Ocultar etiquetas duplicadas
  ax6b.set_xlabel('Contribución a la Puntuación Total', fontsize=11)
  ax6b.set_title('Desglose de Puntuación por Componente', fontsize=12, fontweight='bold')
  ax6b.legend(loc='lower right', fontsize=9)
  ax6b.invert_yaxis()
  ax6b.grid(True, alpha=0.3, axis='x')

  plt.suptitle('Análisis de Eficiencia Multicriterio - Top 15 Modelos', 
              fontsize=14, fontweight='bold', y=1.02)
  plt.tight_layout()
  plt.show()

  # 4. ANÁLISIS POR TIPO DE BASE DE DATOS
  print("\n" + "=" * 80)
  print("COMPARATIVA POR TIPO DE BASE DE DATOS (solo éxitos)")
  print("=" * 80)

  db_comparison = df_success.groupby('db_type').agg({
      'total_time_ms': 'mean',
      'memory_avg_during_rag_mb': 'mean',
      'cpu_avg_during_rag': 'mean',
      'gpu_util_avg_rag': 'mean'
  }).round(2)

  print(db_comparison)

  # FIGURA 7: GRÁFICO DE COMPARACIÓN POR BASE DE DATOS
  print("\n" + "=" * 80)
  print("FIGURA 7: COMPARACIÓN POR TIPO DE BASE DE DATOS")
  print("=" * 80)

  fig7, axes = plt.subplots(2, 2, figsize=(14, 10))

  metrics_db = [
      ('total_time_ms', 'Tiempo Promedio (ms)', 'Reds'),
      ('memory_avg_during_rag_mb', 'Memoria Promedio (MB)', 'Blues'),
      ('cpu_avg_during_rag', 'CPU Promedio (%)', 'Greens'),
      ('gpu_util_avg_rag', 'GPU Promedio (%)', 'Purples')
  ]

  for idx, (metric, title, cmap) in enumerate(metrics_db):
      ax = axes[idx//2, idx%2]
      
      # Agrupar por modelo y DB
      pivot_data = df_success.pivot_table(
          index='modelo_llm',
          columns='db_type',
          values=metric,
          aggfunc='mean'
      )
      
      # Ordenar modelos por tiempo promedio
      if metric == 'total_time_ms':
          model_order = pivot_data.mean(axis=1).sort_values().index
          pivot_data = pivot_data.reindex(model_order)
      
      # Gráfico de barras agrupadas
      x = np.arange(len(pivot_data.index))
      width = 0.25
      
      for i, db_type in enumerate(pivot_data.columns):
          ax.bar(x + (i-1)*width, pivot_data[db_type], width, 
                label=db_type, 
                color=plt.cm.get_cmap(cmap)(0.3 + i*0.3),
                alpha=0.7,
                edgecolor='black',
                linewidth=0.5)
      
      ax.set_xlabel('Modelo', fontsize=9)
      ax.set_ylabel(title.split('(')[0].strip(), fontsize=9)
      ax.set_title(title, fontsize=11)
      ax.set_xticks(x)
      ax.set_xticklabels([m[:8] + '...' for m in pivot_data.index], 
                        rotation=45, ha='right', fontsize=8)
      
      if idx == 0:
          ax.legend(title='Base de Datos', fontsize=8, title_fontsize=9)
      
      ax.grid(True, alpha=0.3, axis='y')

  plt.suptitle('Comparativa de Rendimiento por Tipo de Base de Datos\n(solo casos exitosos)', 
              fontsize=14, fontweight='bold', y=1.02)
  plt.tight_layout()
  plt.show()

  # 6. RESUMEN EJECUTIVO
  print("\n" + "=" * 80)
  print("RESUMEN EJECUTIVO - CASOS EXITOSOS")
  print("=" * 80)

  # Mejor modelo en cada categoría
  best_time = stats_by_model['time_mean'].idxmin()
  best_memory = stats_by_model['memory_mean'].idxmin()
  best_cpu = stats_by_model['cpu_mean'].idxmin()
  best_gpu = stats_by_model['gpu_util_mean'].idxmin()

  print(f"\n🏆 MEJORES MODELOS POR CATEGORÍA:")
  print(f"   • Más rápido: {best_time} ({stats_by_model.loc[best_time, 'time_mean']/1000:.1f}s)")
  print(f"   • Menos memoria: {best_memory} ({stats_by_model.loc[best_memory, 'memory_mean']:.0f}MB)")
  print(f"   • Menos CPU: {best_cpu} ({stats_by_model.loc[best_cpu, 'cpu_mean']:.1f}%)")
  print(f"   • Menos GPU: {best_gpu} ({stats_by_model.loc[best_gpu, 'gpu_util_mean']:.1f}%)")

  # Hallazgos clave
  print(f"\n📊 HALLAZGOS CLAVE:")
  print(f"   • Tiempo promedio exitoso: {stats_by_model['time_mean'].mean()/1000:.1f}s")
  print(f"   • Memoria promedio: {stats_by_model['memory_mean'].mean():.0f}MB")
  print(f"   • CPU promedio: {stats_by_model['cpu_mean'].mean():.1f}%")
  print(f"   • GPU promedio: {stats_by_model['gpu_util_mean'].mean():.1f}%")

  # Recomendación basada en equilibrio
  balanced_model = ranking.index[0]
  print(f"\n💡 RECOMENDACIÓN (mejor equilibrio): {balanced_model}")
  print(f"   Score: {ranking.iloc[0]['total_score']:.3f}")
  print(f"   Tiempo: {ranking.iloc[0]['time_mean']/1000:.1f}s")
  print(f"   Memoria: {ranking.iloc[0]['memory_mean']:.0f}MB")

def reports4():
  import pandas as pd
  import matplotlib.pyplot as plt
  import seaborn as sns
  import numpy as np

  # Cargar datos
  df = pd.read_csv('measurements_v1.csv')

  # Calcular éxito real
  df['success_real'] = df['num_tables'] == df['expected_tables']

  print("=" * 80)
  print("ANÁLISIS COMPARATIVO: ÉXITOS vs NO ÉXITOS por SIZE y MODELO")
  print("=" * 80)

  # 1. ESTADÍSTICAS AGRUPADAS POR SIZE Y MODELO
  print("\nESTADÍSTICAS POR SIZE Y MODELO:")
  print("-" * 80)

  # Agrupar por size y modelo_llm
  group_stats = df.groupby(['size', 'modelo_llm']).agg({
      'success_real': ['count', 'sum', 'mean'],
      'total_time_ms': ['mean', 'std', 'min', 'max'],
      'memory_avg_during_rag_mb': 'mean',
      'cpu_avg_during_rag': 'mean',
      'gpu_util_avg_rag': 'mean'
  }).round(2)

  # Aplanar columnas multi-nivel
  group_stats.columns = ['_'.join(col).strip() for col in group_stats.columns.values]
  group_stats = group_stats.rename(columns={
      'success_real_count': 'total_tests',
      'success_real_sum': 'success_count',
      'success_real_mean': 'success_rate',
      'total_time_ms_mean': 'time_mean',
      'total_time_ms_std': 'time_std',
      'total_time_ms_min': 'time_min',
      'total_time_ms_max': 'time_max',
      'memory_avg_during_rag_mb_mean': 'memory_mean',
      'cpu_avg_during_rag_mean': 'cpu_mean',
      'gpu_util_avg_rag_mean': 'gpu_mean'
  })

  print(group_stats)

  # 2. FIGURA 1: TASA DE ÉXITO POR SIZE Y MODELO
  print("\n" + "=" * 80)
  print("FIGURA 1: TASA DE ÉXITO POR SIZE Y MODELO")
  print("=" * 80)

  fig1, (ax1a, ax1b) = plt.subplots(1, 2, figsize=(16, 8))

  # Gráfico 1a: Tasa de éxito por tamaño
  success_by_size = df.groupby('size')['success_real'].agg(['count', 'sum', 'mean']).round(3)
  success_by_size.columns = ['total_tests', 'success_count', 'success_rate']

  # Ordenar por tasa de éxito
  success_by_size = success_by_size.sort_values('success_rate', ascending=False)

  # Gráfico de barras
  bars_size = ax1a.bar(range(len(success_by_size)), success_by_size['success_rate'],
                      color=['#2ecc71' if rate >= 0.7 else 
                              '#f1c40f' if rate >= 0.5 else 
                              '#e74c3c' for rate in success_by_size['success_rate']],
                      alpha=0.8)

  ax1a.set_xlabel('Tamaño del Modelo')
  ax1a.set_ylabel('Tasa de Éxito')
  ax1a.set_title('Tasa de Éxito por Tamaño del Modelo')
  ax1a.set_xticks(range(len(success_by_size)))
  ax1a.set_xticklabels(success_by_size.index)
  ax1a.set_ylim(0, 1.1)
  ax1a.grid(True, alpha=0.3, axis='y')

  # Añadir valores
  for i, (bar, rate) in enumerate(zip(bars_size, success_by_size['success_rate'])):
      total = success_by_size.iloc[i]['total_tests']
      success = success_by_size.iloc[i]['success_count']
      ax1a.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
              f'{rate:.0%}\n({success}/{total})',
              ha='center', va='bottom', fontsize=9)

  # Gráfico 1b: Tasa de éxito por modelo dentro de cada tamaño
  # Preparar datos para heatmap
  heatmap_data = group_stats.reset_index().pivot_table(
      index='modelo_llm',
      columns='size',
      values='success_rate',
      aggfunc='mean'
  )

  # Ordenar modelos por tasa de éxito promedio
  heatmap_data['avg_success'] = heatmap_data.mean(axis=1)
  heatmap_data = heatmap_data.sort_values('avg_success', ascending=False)
  heatmap_data = heatmap_data.drop('avg_success', axis=1)

  # Crear heatmap
  im = ax1b.imshow(heatmap_data.T, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)

  # Etiquetas
  ax1b.set_yticks(range(len(heatmap_data.columns)))
  ax1b.set_yticklabels(heatmap_data.columns)
  ax1b.set_xticks(range(len(heatmap_data.index)))
  ax1b.set_xticklabels([m[:15] + '...' if len(m) > 15 else m for m in heatmap_data.index], 
                      rotation=45, ha='right', fontsize=9)

  # Añadir valores en las celdas
  for i in range(len(heatmap_data.columns)):
      for j in range(len(heatmap_data.index)):
          value = heatmap_data.iloc[j, i]
          if not pd.isna(value):
              ax1b.text(j, i, f'{value:.0%}', 
                      ha='center', va='center',
                      color='white' if value < 0.5 else 'black',
                      fontweight='bold')

  ax1b.set_title('Tasa de Éxito por Modelo y Tamaño\n(Heatmap)')
  ax1b.set_xlabel('Modelo LLM')

  # Barra de color
  cbar = plt.colorbar(im, ax=ax1b)
  cbar.set_label('Tasa de Éxito')

  plt.suptitle('Comparativa de Tasa de Éxito por Tamaño y Modelo', fontsize=14, fontweight='bold', y=1.02)
  plt.tight_layout()
  plt.show()

  # 3. FIGURA 2: TIEMPO DE EJECUCIÓN POR ÉXITO Y TAMAÑO
  print("\n" + "=" * 80)
  print("FIGURA 2: TIEMPO DE EJECUCIÓN POR ÉXITO Y TAMAÑO")
  print("=" * 80)

  fig2, axes2 = plt.subplots(1, 2, figsize=(16, 8))

  # Gráfico 2a: Boxplot de tiempo por éxito y tamaño
  sns.boxplot(ax=axes2[0], data=df, x='size', y='total_time_ms', hue='success_real',
              palette={True: '#2ecc71', False: '#e74c3c'}, showfliers=False)

  axes2[0].set_xlabel('Tamaño del Modelo')
  axes2[0].set_ylabel('Tiempo Total (ms)')
  axes2[0].set_title('Distribución de Tiempo por Éxito y Tamaño')
  axes2[0].legend(title='Éxito', labels=['Fracaso', 'Éxito'])
  axes2[0].grid(True, alpha=0.3, axis='y')

  # Convertir a segundos para mejor legibilidad
  axes2[0].set_ylabel('Tiempo Total (segundos)')
  yticks = axes2[0].get_yticks()
  axes2[0].set_yticklabels([f'{t/1000:.0f}' for t in yticks])

  # Gráfico 2b: Tiempo promedio por tamaño y éxito
  time_stats = df.groupby(['size', 'success_real'])['total_time_ms'].agg(['mean', 'std', 'count']).reset_index()

  # Crear gráfico de barras agrupadas
  sizes = time_stats['size'].unique()
  success_values = [True, False]
  x = np.arange(len(sizes))
  width = 0.35

  for i, success in enumerate(success_values):
      subset = time_stats[time_stats['success_real'] == success]
      means = [subset[subset['size'] == s]['mean'].values[0] if s in subset['size'].values else 0 
              for s in sizes]
      
      color = '#2ecc71' if success else '#e74c3c'
      label = 'Éxito' if success else 'Fracaso'
      
      axes2[1].bar(x + (i-0.5)*width, means, width, label=label, color=color, alpha=0.7)

  axes2[1].set_xlabel('Tamaño del Modelo')
  axes2[1].set_ylabel('Tiempo Promedio (ms)')
  axes2[1].set_title('Tiempo Promedio por Tamaño y Éxito')
  axes2[1].set_xticks(x)
  axes2[1].set_xticklabels(sizes)
  axes2[1].legend()
  axes2[1].grid(True, alpha=0.3, axis='y')

  # Convertir a segundos
  axes2[1].set_ylabel('Tiempo Promedio (segundos)')
  yticks = axes2[1].get_yticks()
  axes2[1].set_yticklabels([f'{t/1000:.0f}' for t in yticks])

  plt.suptitle('Análisis de Tiempo de Ejecución por Éxito y Tamaño', fontsize=14, fontweight='bold', y=1.02)
  plt.tight_layout()
  plt.show()

  # 4. FIGURA 3: USO DE RECURSOS POR ÉXITO Y TAMAÑO
  print("\n" + "=" * 80)
  print("FIGURA 3: USO DE RECURSOS POR ÉXITO Y TAMAÑO")
  print("=" * 80)

  fig3, axes3 = plt.subplots(2, 2, figsize=(16, 12))

  metrics_resources = [
      ('memory_avg_during_rag_mb', 'Memoria Promedio (MB)', 'Blues'),
      ('cpu_avg_during_rag', 'CPU Promedio (%)', 'Greens'),
      ('gpu_util_avg_rag', 'GPU Utilización Promedio (%)', 'Reds'),
      ('gpu_mem_avg_rag', 'GPU Memoria Promedio (MB)', 'Purples')
  ]

  for idx, (metric, title, cmap) in enumerate(metrics_resources):
      ax = axes3[idx//2, idx%2]
      
      if metric in df.columns:
          # Boxplot por tamaño y éxito
          sns.boxplot(ax=ax, data=df, x='size', y=metric, hue='success_real',
                    palette={True: '#2ecc71', False: '#e74c3c'}, showfliers=False)
          
          ax.set_xlabel('Tamaño del Modelo')
          ax.set_ylabel(title.split('(')[0].strip())
          ax.set_title(f'{title} por Éxito y Tamaño')
          
          if idx == 0:
              ax.legend(title='Éxito', labels=['Fracaso', 'Éxito'])
          else:
              ax.get_legend().remove()
          
          ax.grid(True, alpha=0.3, axis='y')
      else:
          ax.text(0.5, 0.5, f'Dato no disponible:\n{metric}', 
                  ha='center', va='center', transform=ax.transAxes, fontsize=12)
          ax.set_title(title)

  plt.suptitle('Comparativa de Uso de Recursos por Éxito y Tamaño', fontsize=14, fontweight='bold', y=1.02)
  plt.tight_layout()
  plt.show()

  # 5. FIGURA 4: ANÁLISIS DETALLADO POR MODELO (TOP 10)
  print("\n" + "=" * 80)
  print("FIGURA 4: ANÁLISIS DETALLADO POR MODELO (TOP 10)")
  print("=" * 80)

  # Seleccionar top 10 modelos por número de pruebas
  top_models = df['modelo_llm'].value_counts().head(10).index.tolist()
  df_top = df[df['modelo_llm'].isin(top_models)].copy()

  # Crear figura
  fig4, axes4 = plt.subplots(2, 2, figsize=(16, 12))

  # Gráfico 4a: Tasa de éxito por modelo
  success_by_model = df_top.groupby('modelo_llm')['success_real'].agg(['count', 'sum', 'mean']).round(3)
  success_by_model.columns = ['total_tests', 'success_count', 'success_rate']
  success_by_model = success_by_model.sort_values('success_rate', ascending=False)

  bars_model = axes4[0, 0].bar(range(len(success_by_model)), success_by_model['success_rate'],
                              color=['#2ecc71' if rate >= 0.7 else 
                                      '#f1c40f' if rate >= 0.5 else 
                                      '#e74c3c' for rate in success_by_model['success_rate']],
                              alpha=0.8)

  axes4[0, 0].set_xlabel('Modelo LLM')
  axes4[0, 0].set_ylabel('Tasa de Éxito')
  axes4[0, 0].set_title('Top 10 Modelos por Tasa de Éxito')
  axes4[0, 0].set_xticks(range(len(success_by_model)))
  axes4[0, 0].set_xticklabels([m[:15] + '...' for m in success_by_model.index], rotation=45, ha='right')
  axes4[0, 0].set_ylim(0, 1.1)
  axes4[0, 0].grid(True, alpha=0.3, axis='y')

  # Añadir valores
  for i, (bar, rate) in enumerate(zip(bars_model, success_by_model['success_rate'])):
      total = success_by_model.iloc[i]['total_tests']
      success = success_by_model.iloc[i]['success_count']
      axes4[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                      f'{rate:.0%}\n({success}/{total})',
                      ha='center', va='bottom', fontsize=8)

  # Gráfico 4b: Tiempo promedio por modelo (éxitos vs fracasos)
  time_by_model = df_top.groupby(['modelo_llm', 'success_real'])['total_time_ms'].mean().unstack()
  time_by_model = time_by_model.reindex(success_by_model.index)  # Mismo orden que gráfico anterior

  x = np.arange(len(time_by_model))
  width = 0.35

  if True in time_by_model.columns:
      axes4[0, 1].bar(x - width/2, time_by_model[True] / 1000, width, 
                    label='Éxitos', color='#2ecc71', alpha=0.7)
  if False in time_by_model.columns:
      axes4[0, 1].bar(x + width/2, time_by_model[False] / 1000, width, 
                    label='Fracasos', color='#e74c3c', alpha=0.7)

  axes4[0, 1].set_xlabel('Modelo LLM')
  axes4[0, 1].set_ylabel('Tiempo Promedio (segundos)')
  axes4[0, 1].set_title('Tiempo Promedio por Modelo (Éxitos vs Fracasos)')
  axes4[0, 1].set_xticks(x)
  axes4[0, 1].set_xticklabels([m[:12] + '...' for m in time_by_model.index], rotation=45, ha='right')
  axes4[0, 1].legend()
  axes4[0, 1].grid(True, alpha=0.3, axis='y')

  # Gráfico 4c: Distribución de pruebas por tamaño dentro de cada modelo
  size_dist = df_top.groupby(['modelo_llm', 'size']).size().unstack(fill_value=0)
  size_dist = size_dist.reindex(success_by_model.index)  # Mismo orden

  # Gráfico de barras apiladas
  bottom = np.zeros(len(size_dist))
  for size_col in size_dist.columns:
      axes4[1, 0].bar(range(len(size_dist)), size_dist[size_col], bottom=bottom, 
                    label=f'Size: {size_col}', alpha=0.7)
      bottom += size_dist[size_col]

  axes4[1, 0].set_xlabel('Modelo LLM')
  axes4[1, 0].set_ylabel('Número de Pruebas')
  axes4[1, 0].set_title('Distribución de Pruebas por Tamaño (Top 10 Modelos)')
  axes4[1, 0].set_xticks(range(len(size_dist)))
  axes4[1, 0].set_xticklabels([m[:12] + '...' for m in size_dist.index], rotation=45, ha='right')
  axes4[1, 0].legend(title='Tamaño', fontsize=8)
  axes4[1, 0].grid(True, alpha=0.3, axis='y')

  # Gráfico 4d: Relación tiempo-éxito por modelo
  scatter = axes4[1, 1].scatter(df_top['total_time_ms'] / 1000, 
                                df_top['success_real'].astype(int),
                                c=df_top.index, cmap='tab20', alpha=0.7, s=100)

  # Añadir líneas de promedio por modelo
  for model in top_models[:5]:  # Solo primeros 5 para claridad
      model_data = df_top[df_top['modelo_llm'] == model]
      if not model_data.empty:
          time_mean = model_data['total_time_ms'].mean() / 1000
          success_rate = model_data['success_real'].mean()
          
          # Línea vertical en tiempo promedio
          axes4[1, 1].axvline(x=time_mean, color='gray', linestyle='--', alpha=0.5, linewidth=1)
          
          # Texto con modelo
          axes4[1, 1].annotate(model[:10], 
                            (time_mean, success_rate),
                            fontsize=8, alpha=0.7,
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

  axes4[1, 1].set_xlabel('Tiempo Total (segundos)')
  axes4[1, 1].set_ylabel('Éxito (0=Fracaso, 1=Éxito)')
  axes4[1, 1].set_title('Relación Tiempo-Éxito por Modelo\n(Puntos coloreados por prueba)')
  axes4[1, 1].set_yticks([0, 1])
  axes4[1, 1].set_yticklabels(['Fracaso', 'Éxito'])
  axes4[1, 1].grid(True, alpha=0.3)

  plt.suptitle('Análisis Detallado de los 10 Modelos Más Probados', fontsize=14, fontweight='bold', y=1.02)
  plt.tight_layout()
  plt.show()

  # 6. RESUMEN ESTADÍSTICO
  print("\n" + "=" * 80)
  print("RESUMEN ESTADÍSTICO")
  print("=" * 80)

  # Estadísticas generales
  print(f"\n📊 ESTADÍSTICAS GENERALES:")
  print(f"   • Total de pruebas: {len(df)}")
  print(f"   • Pruebas exitosas: {df['success_real'].sum()} ({df['success_real'].mean():.1%})")
  print(f"   • Pruebas fallidas: {(~df['success_real']).sum()} ({1-df['success_real'].mean():.1%})")

  print(f"\n📁 DISTRIBUCIÓN POR TAMAÑO:")
  for size in df['size'].unique():
      size_data = df[df['size'] == size]
      success_rate = size_data['success_real'].mean()
      print(f"   • {size}: {len(size_data)} pruebas, {success_rate:.1%} éxito")

  print(f"\n🏆 MEJORES MODELOS POR TASA DE ÉXITO:")
  top_success_models = df.groupby('modelo_llm')['success_real'].mean().sort_values(ascending=False).head(5)
  for i, (model, rate) in enumerate(top_success_models.items(), 1):
      count = df[df['modelo_llm'] == model].shape[0]
      success_count = df[(df['modelo_llm'] == model) & df['success_real']].shape[0]
      size = df[df['modelo_llm'] == model]['size'].iloc[0] if not df[df['modelo_llm'] == model].empty else 'N/A'
      print(f"   {i}. {model:<25} {rate:.0%} ({success_count}/{count}), Size: {size}")

  print(f"\n⚠️  MODELOS CON PROBLEMAS (<50% éxito):")
  problematic = df.groupby('modelo_llm')['success_real'].mean()
  problematic = problematic[problematic < 0.5]
  if len(problematic) > 0:
      for model, rate in problematic.sort_values().items():
          count = df[df['modelo_llm'] == model].shape[0]
          success_count = df[(df['modelo_llm'] == model) & df['success_real']].shape[0]
          print(f"   • {model:<25} {rate:.0%} ({success_count}/{count})")
  else:
      print("   Ningún modelo tiene menos del 50% de éxito")

  print(f"\n⏱️  TIEMPOS PROMEDIO:")
  print(f"   • Todos: {df['total_time_ms'].mean()/1000:.1f}s")
  print(f"   • Éxitos: {df[df['success_real']]['total_time_ms'].mean()/1000:.1f}s")
  print(f"   • Fracasos: {df[~df['success_real']]['total_time_ms'].mean()/1000:.1f}s")

  print(f"\n💡 HALLAZGOS CLAVE:")
  # Calcular diferencia de tiempo entre éxitos y fracasos
  time_diff = (df[~df['success_real']]['total_time_ms'].mean() - 
              df[df['success_real']]['total_time_ms'].mean()) / 1000
  print(f"   • Los fracasos son {abs(time_diff):.1f}s más {'largos' if time_diff > 0 else 'cortos'} que los éxitos")

  # Análisis por tamaño
  for size in df['size'].unique():
      size_data = df[df['size'] == size]
      success_rate = size_data['success_real'].mean()
      time_success = size_data[size_data['success_real']]['total_time_ms'].mean()/1000
      time_failure = size_data[~size_data['success_real']]['total_time_ms'].mean()/1000 if len(size_data[~size_data['success_real']]) > 0 else 0
      
      print(f"   • Size '{size}': {success_rate:.0%} éxito, "
            f"Éxitos: {time_success:.1f}s, "
            f"Fracasos: {time_failure:.1f}s" if time_failure > 0 else f"Size '{size}': {success_rate:.0%} éxito, Éxitos: {time_success:.1f}s")

  print("\n" + "=" * 80)

#reports1()
#reports2()
#reports3()
reports4()