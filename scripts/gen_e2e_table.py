#!/usr/bin/env python
"""
Genera tables/en/e2e-results.tex desde runs/summary.csv.
Promedia por (schema, mode) sobre los 4 LLMs × 3 DB backends = 12 configs.
"""
import csv
from collections import defaultdict

CSV = "runs/summary.csv"
OUT = "runs/e2e-results-v2.tex"

SCHEMA_ORDER = ["basico", "biblio", "innova", "northwind", "postulaciones"]
MODE_ORDER   = ["llm_only", "rag", "rag_validation"]
MODE_LABEL   = {"llm_only": "L", "rag": "R", "rag_validation": "RV"}


def fnum(v):
    if v in (None, "", "None"): return None
    try: return float(v)
    except: return None


def mean_of(group, col):
    vals = [fnum(r.get(col)) for r in group if fnum(r.get(col)) is not None]
    return sum(vals) / len(vals) if vals else 0.0


def main():
    rows = list(csv.DictReader(open(CSV)))
    assert len(rows) == 180, f"Esperaba 180 filas, hay {len(rows)}"

    # Sanity: los 4 LLMs, 5 schemas, 3 DBs, 3 modes
    llms    = sorted({r["llm"] for r in rows})
    schemas = sorted({r["schema"] for r in rows})
    dbs     = sorted({r["db"] for r in rows})
    modes   = sorted({r["mode"] for r in rows})
    print(f"LLMs:     {llms}")
    print(f"Schemas:  {schemas}")
    print(f"DBs:      {dbs}")
    print(f"Modes:    {modes}")

    # Agrupar por (schema, mode)
    groups = defaultdict(list)
    for r in rows:
        groups[(r["schema"], r["mode"])].append(r)

    # Sanity: cada grupo debe tener 12 configs (4 LLMs × 3 DBs)
    for k, g in groups.items():
        assert len(g) == 12, f"{k}: {len(g)} configs (esperaba 12)"

    # Construir tabla
    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(r"\scriptsize")
    lines.append(r"\setlength{\tabcolsep}{2.5pt}")
    lines.append(r"\caption{End-to-end structural and language results, averaged")
    lines.append(r"over four LLMs (\texttt{llama3.2:3b}, \texttt{qwen2.5:3b},")
    lines.append(r"\texttt{gemma2:2b}, \texttt{deepseek-r1:1.5b}) and three database")
    lines.append(r"backends. Modes: \textbf{L} = \texttt{llm\_only}, \textbf{R} = \texttt{rag},")
    lines.append(r"\textbf{RV} = \texttt{rag\_validation}. \textbf{TA}: composite Table")
    lines.append(r"Accuracy (Eq.~\ref{eq:ta}); \textbf{FK}: foreign-key accuracy;")
    lines.append(r"\textbf{Full}: Full-Schema accuracy; \textbf{Faith}: structural")
    lines.append(r"Faithfulness; \textbf{It}: correction-loop iterations (RV only).}")
    lines.append(r"\label{tab:e2e_results}")
    lines.append(r"\begin{tabular}{l l c c c c c c}")
    lines.append(r"\toprule")
    lines.append(r"\textbf{Schema} & \textbf{M} & \textbf{TA} & \textbf{F1} &")
    lines.append(r"\textbf{FK} & \textbf{Full} & \textbf{Faith} & \textbf{It} \\")
    lines.append(r"\midrule")

    for i, schema in enumerate(SCHEMA_ORDER):
        lines.append(f"\\multirow{{3}}{{*}}{{{schema}}}")
        for mode in MODE_ORDER:
            g = groups.get((schema, mode), [])
            ta    = mean_of(g, "table_acc")
            f1    = mean_of(g, "f1")
            fk    = mean_of(g, "fk_acc")
            full  = mean_of(g, "full_schema")
            faith = mean_of(g, "faith")
            iters = mean_of(g, "iters")
            label = MODE_LABEL[mode]
            lines.append(
                f"  & {label:<2s} & {ta:.3f} & {f1:.3f} & "
                f"{fk:.3f} & {full:.3f} & {faith:.3f} & {iters:.1f} \\\\"
            )
        if i < len(SCHEMA_ORDER) - 1:
            lines.append(r"\midrule")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n✅ {OUT} regenerado")

    # Resumen por modo (para verificar en texto)
    print("\n=== Media por modo (todos los schemas, 4 LLMs) ===")
    for mode in MODE_ORDER:
        sub = [r for r in rows if r["mode"] == mode]
        ta   = mean_of(sub, "table_acc")
        fk   = mean_of(sub, "fk_acc")
        full = mean_of(sub, "full_schema")
        n_ta_perfect = sum(
            1 for r in sub if fnum(r["table_acc"]) == 1.0
        )
        print(f"  {mode:15s}: TA={ta:.3f}  FK={fk:.3f}  Full={full:.3f}  "
              f"TA=1.0 en {n_ta_perfect}/{len(sub)}")


if __name__ == "__main__":
    main()