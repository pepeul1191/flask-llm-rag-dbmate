# scripts/verify_csv_final.py
"""Verifica consistencia del CSV y calcula promedios definitivos para el paper."""
import csv
from collections import defaultdict


def fnum(v):
    if v in (None, "", "None"): return None
    try: return float(v)
    except: return None


rows = list(csv.DictReader(open("runs/summary.csv")))
print(f"Total filas: {len(rows)}")

# 1. Distribución de status
statuses = defaultdict(int)
for r in rows:
    statuses[r.get("status", "?")] += 1
print(f"Status: {dict(statuses)}")

# 2. Filtrar solo ok
ok = [r for r in rows if r.get("status") == "ok"]
print(f"Filas ok: {len(ok)}\n")

# 3. Filas sospechosas (TA=1.0 con full=0.0, o viceversa)
suspects = [
    r for r in ok
    if (fnum(r["table_acc"]) == 1.0 and fnum(r.get("full_schema", 0)) == 0.0)
    or (fnum(r["table_acc"]) < 1.0 and fnum(r.get("full_schema", 0)) == 1.0)
]
print(f"Filas TA/full inconsistentes: {len(suspects)}")
for r in suspects[:5]:
    print(f"  {r['llm']:32s} {r['schema']:12s} {r['db']:8s} {r['mode']:16s} "
          f"TA={r['table_acc']} full={r.get('full_schema')}")
print()

# 4. Promedios definitivos
def mean(col, subset=ok):
    vals = [fnum(r.get(col)) for r in subset if fnum(r.get(col)) is not None]
    return sum(vals) / len(vals) if vals else None


def count_perfect(col, subset=ok):
    return sum(1 for r in subset if fnum(r.get(col)) == 1.0)


print("=" * 60)
print("NÚMEROS DEFINITIVOS PARA EL PAPER")
print("=" * 60)

ta_col = "table_acc"
print(f"\n=== GLOBAL (n={len(ok)}) ===")
print(f"  TA mean:        {mean(ta_col):.4f}")
print(f"  TA=1.0:         {count_perfect(ta_col)}/{len(ok)}")
print(f"  FK mean:        {mean('fk_acc'):.4f}")
print(f"  Full mean:      {mean('full_schema'):.4f}")
print(f"  Full=1.0:       {count_perfect('full_schema')}/{len(ok)}")
print(f"  Faith mean:     {mean('faith'):.4f}")
print(f"  Faith=1.0:      {count_perfect('faith')}/{len(ok)}")
print(f"  MAP mean:       {mean('map'):.4f}")
print(f"  BLEU mean:      {mean('bleu'):.4f}")

print(f"\n=== POR MODO ===")
by_mode = defaultdict(list)
for r in ok: by_mode[r["mode"]].append(r)

for mode in ["llm_only", "rag", "rag_validation"]:
    sub = by_mode[mode]
    print(f"\n  {mode} (n={len(sub)}):")
    print(f"    TA mean:   {mean(ta_col, sub):.4f}")
    print(f"    TA=1.0:    {count_perfect(ta_col, sub)}/{len(sub)}")
    print(f"    FK mean:   {mean('fk_acc', sub):.4f}")
    print(f"    Full mean: {mean('full_schema', sub):.4f}")

print(f"\n=== POR SCHEMA ===")
by_schema = defaultdict(list)
for r in ok: by_schema[r["schema"]].append(r)

for schema in sorted(by_schema):
    sub = by_schema[schema]
    print(f"  {schema:15s} n={len(sub):2d}  TA={mean(ta_col, sub):.4f}  "
          f"perfect={count_perfect(ta_col, sub)}/{len(sub)}")

print(f"\n=== POR LLM ===")
by_llm = defaultdict(list)
for r in ok: by_llm[r["llm"]].append(r)

for llm in sorted(by_llm):
    sub = by_llm[llm]
    print(f"  {llm:35s} n={len(sub):2d}  TA={mean(ta_col, sub):.4f}")