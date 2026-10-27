#!/usr/bin/env bash
# run_all.sh — 5 LLMs × 5 PUMLs × 3 motores, con CSV + logs por corrida
#
# Uso:
#   ./run_all.sh              # corre todas las combinaciones
#   ./run_all.sh --dry-run    # solo lista las combinaciones
#   ./run_all.sh --resume     # salta corridas ya hechas (marcador done_*.ok)
#   ./run_all.sh --clean      # borra marcadores y reinicia CSV
#
# Filtros opcionales por env var (útil para probar con 1 combinación):
#   FILTER_LLM="qwen2.5:3b"   ./run_all.sh
#   FILTER_SCHEMA="basico"    ./run_all.sh
#   FILTER_DB="sqlite"        ./run_all.sh
#
# Salidas en ./runs/:
#   master_<ts>.log                         — log consolidado de la corrida completa
#   summary.csv                             — una fila por (llm, schema, db, modo)
#   <idx>_<llm>_<schema>_<db>.log           — log de cada run
#   done_<llm>_<schema>_<db>.ok             — marcador de "ya hecho" (para --resume)

set -u

# ============================================================
# Configuración
# ============================================================
SCHEMAS=(
    "schemas/basico.puml"
    "schemas/biblio.puml"
    "schemas/innova.puml"
    "schemas/northwind.puml"
    "schemas/postulaciones.puml"
)
LLMS=(
    "llama3.2:3b"        # ⚠️ ajusta el tag exacto según 'ollama list'
    "deepseek-r1:1.5b-qwen-distill-q8_0"
    #"phi3"
    "gemma2:2b"
    "qwen2.5:3b"
)
DB_TYPES=("sqlite" "mysql" "postgres")
BASE_CFG="pipeline_mysql.json"

# Filtros por env var (vacío = sin filtro)
[[ -n "${FILTER_LLM:-}"    ]] && LLMS=( "${FILTER_LLM}" )
[[ -n "${FILTER_SCHEMA:-}" ]] && SCHEMAS=( "schemas/${FILTER_SCHEMA}.puml" )
[[ -n "${FILTER_DB:-}"     ]] && DB_TYPES=( "${FILTER_DB}" )

# ============================================================
# Flags
# ============================================================
DRY_RUN=0; RESUME=0; CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --resume)  RESUME=1 ;;
        --clean)   CLEAN=1 ;;
        -h|--help)
            sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *) echo "Arg desconocido: $arg"; exit 1 ;;
    esac
done

# ============================================================
# Pre-flight
# ============================================================
if [ ! -f "$BASE_CFG" ]; then
    echo "✗ No existe el config base: $BASE_CFG"
    exit 1
fi

if command -v ollama >/dev/null 2>&1; then
    AVAILABLE=$(ollama list 2>/dev/null | tail -n +2 | awk '{print $1}')
    MISSING=()
    for LLM in "${LLMS[@]}"; do
        echo "$AVAILABLE" | grep -qxF "$LLM" || MISSING+=( "$LLM" )
    done
    if [ ${#MISSING[@]} -gt 0 ]; then
        echo "⚠️  Modelos no disponibles en Ollama:"
        printf '    - %s\n' "${MISSING[@]}"
        echo "    Instálalos con: ollama pull <model>"
        echo ""
        echo "    ¿Continuar de todos modos? [y/N]"
        read -r ans
        [[ "${ans:-n}" =~ ^[yY]$ ]] || exit 1
    fi
else
    echo "⚠️  'ollama' no está en PATH. Se asume que Ollama responde por OLLAMA_HOST."
fi

# ============================================================
# Directorios y archivos de salida
# ============================================================
RUNS_DIR="runs"
mkdir -p "$RUNS_DIR"

[[ $CLEAN -eq 1 ]] && rm -f "$RUNS_DIR"/done_*.ok

MASTER_LOG="${RUNS_DIR}/master_$(date +%Y%m%d_%H%M%S).log"
CSV="${RUNS_DIR}/summary.csv"

if [ ! -f "$CSV" ] || [ $CLEAN -eq 1 ]; then
    echo "llm,schema,db,mode,f1,fk,map,ex,flex,bleu,faith" > "$CSV"
fi

TOTAL=$(( ${#LLMS[@]} * ${#SCHEMAS[@]} * ${#DB_TYPES[@]} ))
RUN_IDX=0; FAILED=0; SKIPPED=0

# Ctrl+C limpio
trap 'echo ""; echo "Interrumpido. CSV parcial: $CSV"; echo "Master log: $MASTER_LOG"; exit 130' INT

# ============================================================
# Cabecera
# ============================================================
{
    echo "============================================================"
    echo "RUN ALL PIPELINE — $(date)"
    echo "============================================================"
    echo "LLMs      : ${#LLMS[@]}  ->  ${LLMS[*]}"
    echo "Schemas   : ${#SCHEMAS[@]}  ->  $(printf '%s ' "${SCHEMAS[@]##*/}")"
    echo "DB types  : ${#DB_TYPES[@]}  ->  ${DB_TYPES[*]}"
    echo "Total runs: $TOTAL  (x3 modos = $((TOTAL*3)) filas en CSV)"
    echo "Config    : $BASE_CFG"
    echo "Modo      : dry=$DRY_RUN resume=$RESUME clean=$CLEAN"
    echo "Master log: $MASTER_LOG"
    echo "CSV       : $CSV"
    echo "============================================================"
    echo ""
} | tee "$MASTER_LOG"

[ $DRY_RUN -eq 1 ] && echo "(modo dry-run: no se ejecutará nada)"

# ============================================================
# Bucle principal
# ============================================================
for LLM in "${LLMS[@]}"; do
    LLM_TAG=$(printf '%s' "$LLM" | tr -c 'A-Za-z0-9._-' '_')

    for SCHEMA in "${SCHEMAS[@]}"; do
        SCHEMA_NAME=$(basename "$SCHEMA" .puml)

        for DB_TYPE in "${DB_TYPES[@]}"; do
            RUN_IDX=$((RUN_IDX + 1))
            MARKER="${RUNS_DIR}/done_${LLM_TAG}_${SCHEMA_NAME}_${DB_TYPE}.ok"

            if [ $RESUME -eq 1 ] && [ -f "$MARKER" ]; then
                echo "[$RUN_IDX/$TOTAL] SKIP $LLM / $SCHEMA_NAME / $DB_TYPE (ya hecho)" \
                    | tee -a "$MASTER_LOG"
                SKIPPED=$((SKIPPED + 1))
                continue
            fi

            RUN_LOG="${RUNS_DIR}/$(printf '%03d' "$RUN_IDX")_${LLM_TAG}_${SCHEMA_NAME}_${DB_TYPE}.log"

            {
                echo ""
                echo "############################################################"
                echo "[$RUN_IDX/$TOTAL] $(date)"
                echo "  LLM     : $LLM"
                echo "  Schema  : $SCHEMA"
                echo "  DB      : $DB_TYPE"
                echo "  Log     : $RUN_LOG"
                echo "############################################################"
            } | tee -a "$MASTER_LOG"

            if [ $DRY_RUN -eq 1 ]; then
                echo "  (dry-run)" | tee -a "$MASTER_LOG"
                continue
            fi

            # --- Config temporal ---
            TMP_CFG=$(mktemp --suffix=.json)
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
                echo "  ✗ Falló la edición del JSON base" | tee -a "$MASTER_LOG"
                rm -f "$TMP_CFG"
                FAILED=$((FAILED + 1))
                continue
            fi

            # --- Ejecutar ---
            export OLLAMA_MODEL="$LLM"
            T0=$(date +%s)
            python -m ai.main "$SCHEMA" "$DB_TYPE" pipeline "$TMP_CFG" > "$RUN_LOG" 2>&1
            RC=$?
            T1=$(date +%s)
            DUR=$((T1 - T0))
            rm -f "$TMP_CFG"

            if [ $RC -ne 0 ]; then
                echo "  ✗ FALLÓ (rc=$RC, ${DUR}s) — ver $RUN_LOG" | tee -a "$MASTER_LOG"
                FAILED=$((FAILED + 1))
                continue
            fi

            # --- Localizar el JSON de ESTA corrida ---
            RUN_ID=$(grep -oP 'run_id:\s*\K\S+' "$RUN_LOG" | head -1)
            NEW_FILE=""
            if [ -n "$RUN_ID" ] && [ -f "tmp/pipeline_results/flores_metrics_${RUN_ID}.json" ]; then
                NEW_FILE="tmp/pipeline_results/flores_metrics_${RUN_ID}.json"
            else
                NEW_FILE=$(ls -t tmp/pipeline_results/flores_metrics_*.json 2>/dev/null | head -1)
            fi

            if [ -z "$NEW_FILE" ]; then
                echo "  ⚠️  Sin archivo de métricas (${DUR}s)" | tee -a "$MASTER_LOG"
                FAILED=$((FAILED + 1))
                continue
            fi

            # --- Extraer filas (3 modos → 3 filas CSV) ---
            ROWS=$(python - "$NEW_FILE" "$LLM" "$SCHEMA_NAME" "$DB_TYPE" <<'PYEOF'
import json, sys
path, llm, schema, db = sys.argv[1:5]
with open(path) as fh:
    d = json.load(fh)
for r in d.get("runs", []):
    f  = r.get("flores") or {}
    st = f.get("structural") or {}
    rt = f.get("retrieval") or {}
    ex = f.get("execution") or {}
    nl = f.get("nlg") or {}
    fa = f.get("faithfulness") or {}
    vals = [
        st.get("f1"),
        st.get("foreign_key_accuracy"),
        rt.get("MAP"),
        ex.get("EX"),
        ex.get("FLEX"),
        nl.get("BLEU"),
        fa.get("faithfulness"),
    ]
    vstr = ",".join(str(v) if v is not None else "" for v in vals)
    print(f"{llm},{schema},{db},{r.get('mode','?')},{vstr}")
PYEOF
)

            if [ -z "$ROWS" ]; then
                echo "  ⚠️  JSON sin métricas (${DUR}s)" | tee -a "$MASTER_LOG"
                FAILED=$((FAILED + 1))
                continue
            fi

            echo "$ROWS" >> "$CSV"
            touch "$MARKER"

            # --- Mini-tabla al master log ---
            {
                echo "  ✓ OK (${DUR}s)"
                echo "$ROWS" | python -c '
import sys
print("  {:<16} {:<8} {:<8} {:<8} {:<6} {:<6} {:<8} {:<8}".format(
    "Mode","F1","FK","MAP","EX","FLEX","BLEU","Faith"))
for line in sys.stdin:
    parts = line.strip().split(",")
    if len(parts) < 11:
        continue
    mode = parts[3]
    vals = [v if v else "-" for v in parts[4:]]
    print("  {:<16} {:<8} {:<8} {:<8} {:<6} {:<6} {:<8} {:<8}".format(
        mode, *vals))
'
            } | tee -a "$MASTER_LOG"

        done
    done
done

# ============================================================
# Resumen final
# ============================================================
{
    echo ""
    echo "============================================================"
    echo "FIN $(date)"
    echo "============================================================"
    echo "Total runs : $TOTAL"
    echo "Ejecutados : $((TOTAL - SKIPPED - FAILED))"
    echo "Fallidos   : $FAILED"
    echo "Saltados   : $SKIPPED"
    echo "Filas CSV  : $(($(wc -l < "$CSV") - 1))  (esperadas: $((TOTAL*3)))"
    echo "CSV        : $CSV"
    echo "Master log : $MASTER_LOG"
    echo "============================================================"
} | tee -a "$MASTER_LOG"