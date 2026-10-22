# Comandos por schema

## Requisito previo (una vez por sesión)

```bash
cd ~/Documents/UNMSM/2025-2/Semanario\ de\ Tesis\ 3/herramienta
rm -rf tmp/chroma_db
export OLLAMA_NUM_CTX=16384
export OLLAMA_NUM_GPU=20
```

## 1. Tests de errores inyectados (`errors`)

**Objetivo:** evaluar el validador mediante errores inyectados. Es la prueba más rápida, no requiere LLM y responde directamente al Reviewer 1.

**Tiempo estimado:** segundos por schema.

### `basico.puml`

```bash
python -m ai.main schemas/basico.puml sqlite errors 2>&1 | tee run_basico_errors.log
```

### `ejemplo.puml`

```bash
python -m ai.main schemas/ejemplo.puml sqlite errors 2>&1 | tee run_ejemplo_errors.log
```

### `innova.puml`

```bash
python -m ai.main schemas/innova.puml sqlite errors 2>&1 | tee run_innova_errors.log
```

### `nortwind.puml`

```bash
python -m ai.main schemas/nortwind.puml sqlite errors 2>&1 | tee run_nortwind_errors.log
```

### `postulaciones.puml`

```bash
python -m ai.main schemas/postulaciones.puml sqlite errors 2>&1 | tee run_postulaciones_errors.log
```

### `postulaciones_v2.puml`

```bash
python -m ai.main schemas/postulaciones_v2.puml sqlite errors 2>&1 | tee run_postulaciones_v2_errors.log
```

## 2. Comparación de los tres modos (`compare`)

**Objetivo:** comparar los tres modos de ejecución del sistema.

**Tiempo estimado:** minutos por schema, debido al uso del LLM.

**Resultados esperados:** tres archivos `metrics_*.json` y un archivo `comparison_*.json` por ejecución.

### `basico.puml`

```bash
python -m ai.main schemas/basico.puml sqlite compare 2>&1 | tee run_basico_compare.log
```

### `ejemplo.puml`

```bash
python -m ai.main schemas/ejemplo.puml sqlite compare 2>&1 | tee run_ejemplo_compare.log
```

### `innova.puml`

```bash
python -m ai.main schemas/innova.puml sqlite compare 2>&1 | tee run_innova_compare.log
```

### `nortwind.puml`

```bash
python -m ai.main schemas/nortwind.puml sqlite compare 2>&1 | tee run_nortwind_compare.log
```

### `postulaciones.puml`

```bash
python -m ai.main schemas/postulaciones.puml sqlite compare 2>&1 | tee run_postulaciones_compare.log
```

### `postulaciones_v2.puml`

```bash
python -m ai.main schemas/postulaciones_v2.puml sqlite compare 2>&1 | tee run_postulaciones_v2_compare.log
```

## 3. Pipeline completo (`pipeline`)

**Objetivo:** ejecutar la comparación, los benchmarks de Flores y los tests.

**Requisito:** disponer del archivo `pipeline_config_basico_rag_validation.json` en la raíz del proyecto.

**Tiempo estimado:** 10–15 minutos por schema, considerando los tres modos.

### `basico.puml`

```bash
python -m ai.main schemas/basico.puml sqlite pipeline pipeline_config_basico_rag_validation.json 2>&1 | tee run_basico_pipeline.log
```

### `ejemplo.puml`

```bash
python -m ai.main schemas/ejemplo.puml sqlite pipeline pipeline_config_basico_rag_validation.json 2>&1 | tee run_ejemplo_pipeline.log
```

### `innova.puml`

```bash
python -m ai.main schemas/innova.puml sqlite pipeline pipeline_config_basico_rag_validation.json 2>&1 | tee run_innova_pipeline.log
```

### `nortwind.puml`

```bash
python -m ai.main schemas/nortwind.puml sqlite pipeline pipeline_config_basico_rag_validation.json 2>&1 | tee run_nortwind_pipeline.log
```

### `postulaciones.puml`

```bash
python -m ai.main schemas/postulaciones.puml sqlite pipeline pipeline_config_basico_rag_validation.json 2>&1 | tee run_postulaciones_pipeline.log
```

### `postulaciones_v2.puml`

```bash
python -m ai.main schemas/postulaciones_v2.puml sqlite pipeline pipeline_config_basico_rag_validation.json 2>&1 | tee run_postulaciones_v2_pipeline.log
```

## 4. Ejecutar un solo modo por schema

**Objetivo:** aislar y evaluar cada modo de ejecución de manera independiente.

Modos disponibles:

- `llm_only`: ejecución únicamente con LLM.
- `rag`: ejecución con recuperación aumentada por generación.
- `rag_validation`: ejecución con RAG y validación.

### `basico.puml`

```bash
python -m ai.main schemas/basico.puml sqlite llm_only 2>&1 | tee run_basico_llm_only.log
python -m ai.main schemas/basico.puml sqlite rag 2>&1 | tee run_basico_rag.log
python -m ai.main schemas/basico.puml sqlite rag_validation 2>&1 | tee run_basico_rag_validation.log
```

### `ejemplo.puml`

```bash
python -m ai.main schemas/ejemplo.puml sqlite llm_only
python -m ai.main schemas/ejemplo.puml sqlite rag
python -m ai.main schemas/ejemplo.puml sqlite rag_validation
```

### `innova.puml`

```bash
python -m ai.main schemas/innova.puml sqlite llm_only
python -m ai.main schemas/innova.puml sqlite rag
python -m ai.main schemas/innova.puml sqlite rag_validation
```

### `nortwind.puml`

```bash
python -m ai.main schemas/nortwind.puml sqlite llm_only
python -m ai.main schemas/nortwind.puml sqlite rag
python -m ai.main schemas/nortwind.puml sqlite rag_validation
```

### `postulaciones.puml`

```bash
python -m ai.main schemas/postulaciones.puml sqlite llm_only
python -m ai.main schemas/postulaciones.puml sqlite rag
python -m ai.main schemas/postulaciones.puml sqlite rag_validation
```

### `postulaciones_v2.puml`

```bash
python -m ai.main schemas/postulaciones_v2.puml sqlite llm_only
python -m ai.main schemas/postulaciones_v2.puml sqlite rag
python -m ai.main schemas/postulaciones_v2.puml sqlite rag_validation
```

**Nota:** en esta sección, solo los comandos de `basico.puml` guardan explícitamente la salida en logs. Para conservar la salida de los demás schemas, añade `2>&1 | tee nombre_del_log.log` al final de cada comando.

## 5. Cambiar de modelo por schema

Añadir `OLLAMA_MODEL=...` antes del comando para utilizar un modelo específico.

### `basico.puml` con `gemma2:2b`

```bash
OLLAMA_MODEL=gemma2:2b python -m ai.main schemas/basico.puml sqlite pipeline pipeline_config_basico_rag_validation.json 2>&1 | tee run_basico_gemma2-2b.log
```

### `ejemplo.puml` con `qwen2.5:3b`

```bash
OLLAMA_MODEL=qwen2.5:3b python -m ai.main schemas/ejemplo.puml sqlite compare 2>&1 | tee run_ejemplo_qwen2.5-3b.log
```

### `innova.puml` con `llama3.2:1b`

```bash
OLLAMA_MODEL=llama3.2:1b python -m ai.main schemas/innova.puml sqlite compare 2>&1 | tee run_innova_llama3.2-1b.log
```

## 6. Orden recomendado de ejecución

1. Ejecutar los seis tests `errors`, que permiten obtener rápidamente la tabla de falsos positivos (FP) y falsos negativos (FN) del validador.
2. Ejecutar `compare` en `basico.puml` y `postulaciones_v2.puml`, que representan dos extremos en complejidad: 6 tablas frente a 22 tablas.
3. Ejecutar `compare` en los cuatro schemas restantes si se necesita una evaluación completa.
4. Ejecutar `pipeline` si se requieren métricas adicionales como MAP/MRR, EX/FLEX y BLEU/ROUGE.
5. Ejecutar modos individuales para aislar problemas o analizar cada estrategia.
6. Probar modelos alternativos si se desea evaluar su impacto en los resultados.

## 7. Verificar los resultados

### 7.1. Comprobar los logs generados

```bash
ls -lh run_*.log
```

### 7.2. Consultar las métricas de cada schema

```bash
for f in tmp/metrics_*sqlite_*_*.json; do
  echo "=== $f ==="
  python -c "import json; d=json.load(open('$f')); print({k:d[k] for k in ['table_accuracy','column_accuracy','foreign_key_accuracy','precision','recall','f1']})"
done
```

Este script recorre los archivos JSON de métricas encontrados y muestra los siguientes indicadores:

| Métrica | Descripción |
|---|---|
| `table_accuracy` | Exactitud en la identificación de tablas. |
| `column_accuracy` | Exactitud en la identificación de columnas. |
| `foreign_key_accuracy` | Exactitud en la identificación de claves foráneas. |
| `precision` | Proporción de predicciones positivas que son correctas. |
| `recall` | Proporción de positivos reales identificados. |
| `f1` | Media armónica entre precisión y recall. |

**Nota:** el script presupone que todos los archivos contienen las seis claves. Si alguna falta, Python generará un `KeyError`. Comprueba también las fechas de los archivos para distinguir los resultados recientes de los anteriores.

## 8. Resumen de los experimentos

| Experimento | Uso de LLM | Tiempo estimado | Propósito |
|---|---|---|---|
| `errors` | No | Segundos por schema | Evaluar FP y FN del validador. |
| `compare` | Sí | Minutos por schema | Comparar los tres modos. |
| `pipeline` | Sí | 10–15 min por schema | Ejecutar comparación, benchmarks y tests. |
| Modos individuales | Depende del modo | Variable | Aislar cada estrategia. |
| Cambio de modelo | Sí | Variable | Evaluar modelos alternativos. |

**Recomendación final:** comenzar con `errors` para los seis schemas y continuar con `compare` en `basico.puml` y `postulaciones_v2.puml`. Así se obtiene evidencia rápida sobre el validador antes de invertir tiempo en el pipeline completo.
