# scripts/rebuild_summary_final.py
"""
Reconstruye runs/summary.csv desde tmp/metrics_*.json (recomputados con TA compuesta).
Para cada una de las 180 combinaciones canónicas, busca el metrics más reciente.
Si no existe, la fila queda con TA=0 y status='missing'.
"""
import csv, json, glob, os

CSV_IN  = "runs/summary.csv"
CSV_OUT = "runs/summary.csv"
TMP     = "tmp"


def llm_to_filename_key(llm: str) -> str:
    """deepseek-r1:1.5b-qwen-distill-q8_0 → deepseek-r1_1.5b-qwen-distill-q8_0"""
    return llm.replace(":", "_")


def find_metrics(llm, schema, db, mode):
    """Busca el metrics_*.json más reciente para esta combinación."""
    llm_key = llm_to_filename_key(llm)
    pattern = f"{TMP}/metrics_*{schema}_{db}_{mode}.json"
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    for f in files:
        if llm_key in os.path.basename(f):
            with open(f) as fh:
                return json.load(fh), f
    return None, None


def main():
    # 1. Leer CSV actual como "índice canónico" (qué combinaciones tiene)
    rows = list(csv.DictReader(open(CSV_IN)))
    print(f"Filas en CSV actual: {len(rows)}")

    new_rows = []
    stats = {"updated": 0, "unchanged": 0, "missing_metrics": 0}

    for row in rows:
        llm, schema, db, mode = row["llm"], row["schema"], row["db"], row["mode"]
        m, src = find_metrics(llm, schema, db, mode)

        if m is None:
            # Sin métricas → run fallido
            row["table_acc"]      = 0.0
            row["table_name_acc"] = 0.0
            row["full_schema"]    = 0.0
            row["fk_acc"]         = 0.0
            row["status"]         = "missing_metrics"
            stats["missing_metrics"] += 1
            print(f"  [MISSING] {llm} / {schema} / {db} / {mode} → TA=0")
        else:
            old_ta = row["table_acc"]
            row["table_acc"]      = m.get("table_accuracy", 0.0)
            row["table_name_acc"] = m.get("table_name_accuracy", 0.0)
            row["full_schema"]    = m.get("full_schema_accuracy", 0.0)
            row["fk_acc"]         = m.get("foreign_key_accuracy") or 0.0
            row["status"]         = "ok"
            if str(old_ta) != str(row["table_acc"]):
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1

        row["_source"] = os.path.basename(src) if src else "MISSING"
        new_rows.append(row)

    # 2. Escribir CSV nuevo
    with open(CSV_OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=new_rows[0].keys())
        w.writeheader()
        w.writerows(new_rows)

    # 3. Reporte
    print(f"\n✅ {CSV_OUT}: {len(new_rows)} filas")
    print(f"   Actualizadas:    {stats['updated']}")
    print(f"   Sin cambios:     {stats['unchanged']}")
    print(f"   Missing metrics: {stats['missing_metrics']}")

    ta_vals = [float(r["table_acc"]) for r in new_rows]
    print(f"\n   TA promedio:  {sum(ta_vals)/len(ta_vals):.4f}")
    print(f"   TA = 1.0:     {sum(1 for t in ta_vals if t == 1.0)}/{len(ta_vals)}")

    # 4. Verificación northwind RV
    print(f"\n   Verificación northwind RV:")
    for r in new_rows:
        if r["schema"] == "northwind" and r["mode"] == "rag_validation":
            print(f"     {r['llm']:32s} {r['db']:8s} TA={r['table_acc']} status={r['status']}")


if __name__ == "__main__":
    main()