#!/usr/bin/env bash
# merge_ai.sh - Fusiona todos los .py de la carpeta ai/ en ai_full.py
#
# Excluye:
#   - draft.py          (en cualquier subcarpeta)
#   - __init__.py       (marcadores de paquete)
#   - ai_full.py        (evita autoreferencia)
#   - __pycache__/      (bytecode)
#
# Deduplica imports repetidos en el archivo final.
# Uso: ./merge_ai.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_DIR="$SCRIPT_DIR/ai"
OUTPUT="$SCRIPT_DIR/ai_full.py"
TMPFILE="$(mktemp)"
trap 'rm -f "$TMPFILE"' EXIT

if [ ! -d "$AI_DIR" ]; then
    echo "Error: no existe la carpeta '$AI_DIR'" >&2
    exit 1
fi

if [ -f "$OUTPUT" ]; then
    echo "Borrando $OUTPUT ..."
    rm -f "$OUTPUT"
fi

# ---------- 1) Recolectar archivos ----------
# IMPORTANTE: -print0 en find  +  sort -z  +  mapfile -d ''  -> separación por NUL
mapfile -d '' FILES < <(
    find "$AI_DIR" -type f -name "*.py" \
        ! -name "draft.py" \
        ! -name "__init__.py" \
        ! -name "ai_full.py" \
        -not -path "*/__pycache__/*" \
        -print0 \
        | LC_ALL=C sort -z
)

if [ ${#FILES[@]} -eq 0 ]; then
    echo "Error: no se encontraron archivos .py para fusionar en '$AI_DIR'" >&2
    exit 1
fi

# ---------- 2) Cabecera ----------
{
    echo "# ================================================================"
    echo "# Archivo generado automáticamente por merge_ai.sh"
    echo "# Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "# NO EDITAR MANUALMENTE - se regenera en cada ejecución"
    echo "# ================================================================"
    echo
} > "$TMPFILE"

# ---------- 3) Concatenar cada archivo con su cabecera ----------
count=0
for file in "${FILES[@]}"; do
    rel="${file#"$AI_DIR"/}"
    {
        echo "# ================================================================"
        echo "# Archivo: $rel"
        echo "# ================================================================"
        cat "$file"
        echo
        echo
    } >> "$TMPFILE"
    count=$((count + 1))
done

# ---------- 4) Deduplicar imports repetidos ----------
awk '
    {
        line = $0
        trimmed = line
        sub(/^[ \t]+/, "", trimmed)

        if (trimmed ~ /^(import|from)[ \t]/) {
            key = trimmed
            gsub(/[ \t]+/, " ", key)
            if (key in seen) {
                print "# [dedup] " line
                next
            }
            seen[key] = 1
        }
        print line
    }
' "$TMPFILE" > "$OUTPUT"

echo "Merge completado: $OUTPUT"
echo "Archivos incluidos: $count"
echo "Tamaño final: $(wc -l < "$OUTPUT") líneas"