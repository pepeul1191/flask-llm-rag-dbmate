#!/usr/bin/env bash
# run_pipeline.sh
# Uso:
#   ./run_pipeline.sh [schema.puml] [db_type] [config_base.json]
#
# Ejemplos:
#   ./run_pipeline.sh
#   ./run_pipeline.sh schemas/postulaciones.puml mysql
#   ./run_pipeline.sh schemas/postulaciones_v2.puml sqlite pipeline_config_basico_rag_validation.json
#
# Valores por defecto si no se pasan argumentos:
#   schema       = schemas/postulaciones.puml
#   db_type      = mysql
#   config_base  = pipeline_mysql.json
#
# Log generado:
#   <TIMESTAMP>_run_<db_type>_<llm_model>.log   (en el directorio desde donde se ejecuta)

set -u

# ---------- Argumentos ----------
SCHEMA="${1:-schemas/postulaciones.puml}"
DB_TYPE="${2:-sqlite}"
BASE_CFG="${3:-pipeline_mysql.json}"

# ---------- Modelo Ollama fijado por el script (NO se lee del .env) ----------
OLLAMA_MODEL_SET="qwen2.5:3b"
export OLLAMA_MODEL="$OLLAMA_MODEL_SET"

# ---------- Log con timestamp + motor de BD + modelo LLM ----------
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
# Sanitiza el nombre del modelo para que sea seguro como nombre de archivo
# (reemplaza ":" "/" espacios, etc., por "_")
LLM_TAG=$(printf '%s' "$OLLAMA_MODEL" | tr -c 'A-Za-z0-9._-' '_')
LOG="${TIMESTAMP}_run_${DB_TYPE}_${LLM_TAG}.log"

# ---------- Validación del config base ----------
if [ ! -f "$BASE_CFG" ]; then
    echo "✗ No existe el JSON base: $BASE_CFG" | tee "$LOG"
    exit 1
fi

# ---------- JSON temporal con inputs[0] y db_types[0] sustituidos ----------
TMP_CFG=$(mktemp --suffix=.json)
trap 'rm -f "$TMP_CFG"' EXIT

python - "$BASE_CFG" "$SCHEMA" "$DB_TYPE" "$TMP_CFG" <<'PYEOF'
import json, sys
base, schema, db_type, out = sys.argv[1:5]
with open(base) as fh:
    cfg = json.load(fh)
cfg["inputs"]   = [schema]
cfg["db_types"] = [db_type]
with open(out, "w") as fh:
    json.dump(cfg, fh, indent=2, ensure_ascii=False)
PYEOF

if [ $? -ne 0 ]; then
    echo "✗ Falló la edición del JSON base" | tee -a "$LOG"
    exit 1
fi

# ---------- Cabecera del log ----------
{
    echo "===== INICIO PIPELINE $(date) ====="
    echo "  schema        : $SCHEMA"
    echo "  db_type       : $DB_TYPE"
    echo "  config base   : $BASE_CFG"
    echo "  config temp   : $TMP_CFG"
    echo "  OLLAMA_MODEL  : $OLLAMA_MODEL"
    echo "  log           : $LOG"
    echo ""
    echo "----- JSON efectivo -----"
    cat "$TMP_CFG"
    echo "-------------------------"
    echo ""
} | tee "$LOG"

# ---------- Ejecución del pipeline ----------
python -m ai.main "$SCHEMA" "$DB_TYPE" pipeline "$TMP_CFG" 2>&1 | tee -a "$LOG"

# ---------- Localizar el último archivo de métricas ----------
LATEST=$(ls -t tmp/pipeline_results/flores_metrics_*.json 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
    echo "⚠ No se encontró ningún archivo flores_metrics_*.json en tmp/pipeline_results/" | tee -a "$LOG"
    exit 1
fi

# ---------- Tabla de métricas → anexar al log ----------
{
    echo ""
    echo "===== MÉTRICAS EXTRAÍDAS DE: $LATEST ====="
    python - "$LATEST" <<'PYEOF'
import json, sys
with open(sys.argv[1]) as fh:
    d = json.load(fh)

print(f"{'Mode':<16} {'F1':<8} {'FK':<8} {'MAP':<8} {'EX':<6} {'FLEX':<6} {'BLEU':<8} {'Faith':<8}")
print('-' * 80)
for r in d['runs']:
    f  = r['flores']
    st = f.get('structural') or {}
    rt = f.get('retrieval') or {}
    ex = f.get('execution') or {}
    nl = f.get('nlg') or {}
    fa = f.get('faithfulness') or {}
    print(f"{r['mode']:<16} "
          f"{st.get('f1','-'):<8} "
          f"{st.get('foreign_key_accuracy','-'):<8} "
          f"{rt.get('MAP','-'):<8} "
          f"{ex.get('EX','-'):<6} "
          f"{ex.get('FLEX','-'):<6} "
          f"{nl.get('BLEU','-'):<8} "
          f"{fa.get('faithfulness','-'):<8}")
PYEOF
} 2>&1 | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "===== FIN $(date) =====" | tee -a "$LOG"