#!/usr/bin/env python3
"""
diagnose_retrieval.py — Diagnóstico de retrieval para todos los schemas.

Para cada schema:
  - Reconstruye/usa el vector DB
  - Corre las queries del benchmark
  - Muestra hit/miss por query y métricas agregadas
  - Compara contra los valores objetivo del paper (Tabla 6)

Uso:
    python diagnose_retrieval.py
    python diagnose_retrieval.py basico
    python diagnose_retrieval.py basico biblio
"""
import json
import os
import sys

from ai.services.ingestion import ingest_puml, split_documents
from ai.services.retrieval import create_retriever
from ai.services.vector_store import (
    check_existing_vector_db,
    create_vector_db,
    should_recreate_vector_db,
)
from ai.evaluation.retrieval_metrics import compute_retrieval_metrics

SCHEMAS_DEFAULT = ["basico", "biblio", "innova", "northwind", "postulaciones"]

# Valores objetivo del paper (Tabla 6, sqlite + ChromaDB)
TARGET = {
    "MAP":   0.708,
    "P@5":   0.540,
    "R@5":   1.000,
    "NDCG@5": 0.708,
}


def _flag(value, target, tol=0.03):
    """Marca si un valor está cerca/por encima del objetivo del paper."""
    if value is None:
        return "  -  "
    if value >= target - tol:
        return "  ✅ "
    return "  ❌ "


def diagnose_one(schema: str, k: int = 5):
    puml = f"schemas/{schema}.puml"
    bench_path = f"benchmarks/{schema}_retrieval.json"

    if not os.path.exists(puml):
        return {"schema": schema, "error": f"{puml} no existe"}
    if not os.path.exists(bench_path):
        return {"schema": schema, "error": f"{bench_path} no existe"}

    bench = json.load(open(bench_path, encoding="utf-8"))
    queries = bench.get("queries", [])
    if not queries:
        return {"schema": schema, "error": "benchmark sin queries"}

    # Vector DB (recrear si el PUML cambió)
    vdb = check_existing_vector_db()
    if vdb is None or should_recreate_vector_db(puml, vdb):
        chunks = split_documents(ingest_puml(puml), puml)
        vdb = create_vector_db(chunks, puml)

    retriever = create_retriever(vdb, source_file=puml, k=k)

    # Detalle por query
    detail = []
    for q in queries:
        docs = retriever.invoke(q["query"])
        retrieved = [d.metadata.get("chunk_id") for d in docs]
        relevant = set(q.get("relevant_chunks", []))
        hit = bool(relevant & set(retrieved))
        detail.append({
            "query": q["query"],
            "relevant": sorted(relevant),
            "retrieved": retrieved,
            "hit": hit,
        })

    # Métricas agregadas
    metrics = compute_retrieval_metrics(queries, retriever, k=k)

    n_hits = sum(1 for d in detail if d["hit"])
    return {
        "schema": schema,
        "n_queries": len(queries),
        "n_hits": n_hits,
        "detail": detail,
        "metrics": {
            "MAP":    metrics.get("MAP"),
            "MAP+":   metrics.get("MAP+"),
            "P@5":    metrics.get("P@5"),
            "R@5":    metrics.get("R@5"),
            "NDCG@5": metrics.get("NDCG@5"),
        },
    }


def main():
    schemas = sys.argv[1:] or SCHEMAS_DEFAULT
    results = []

    for schema in schemas:
        print(f"\n{'=' * 70}")
        print(f"  SCHEMA: {schema}")
        print("=" * 70)

        try:
            r = diagnose_one(schema)
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({"schema": schema, "error": str(e)})
            continue

        if "error" in r:
            print(f"  ✗ {r['error']}")
            results.append(r)
            continue

        # Detalle por query
        for i, d in enumerate(r["detail"]):
            mark = "✓" if d["hit"] else "✗"
            print(f"  [{i}] {mark} {d['query'][:55]:55s}")
            print(f"       relevant={d['relevant']}  "
                  f"retrieved={d['retrieved']}")

        # Agregado
        m = r["metrics"]
        print(f"\n  Hits: {r['n_hits']}/{r['n_queries']}")
        print(f"  MAP    = {m['MAP']}   {_flag(m['MAP'], TARGET['MAP'])}"
              f"(paper ~{TARGET['MAP']})")
        print(f"  MAP+   = {m['MAP+']}")
        print(f"  P@5    = {m['P@5']}   {_flag(m['P@5'], TARGET['P@5'])}"
              f"(paper ~{TARGET['P@5']})")
        print(f"  R@5    = {m['R@5']}   {_flag(m['R@5'], TARGET['R@5'])}"
              f"(paper ={TARGET['R@5']})")
        print(f"  NDCG@5 = {m['NDCG@5']}   {_flag(m['NDCG@5'], TARGET['NDCG@5'])}"
              f"(paper ~{TARGET['NDCG@5']})")

        results.append(r)

    # Resumen final
    print(f"\n{'=' * 70}")
    print("  RESUMEN")
    print("=" * 70)
    print(f"  {'Schema':15s} {'Hits':7s} {'MAP':8s} {'P@5':8s} "
          f"{'R@5':8s} {'NDCG@5':8s}")
    for r in results:
        if "error" in r:
            print(f"  {r['schema']:15s} ERROR: {r['error']}")
            continue
        m = r["metrics"]
        print(f"  {r['schema']:15s} "
              f"{r['n_hits']:>2d}/{r['n_queries']:<4d} "
              f"{m['MAP']:<8.4f} {m['P@5']:<8.4f} "
              f"{m['R@5']:<8.4f} {m['NDCG@5']:<8.4f}")

    # Guardar
    os.makedirs("reports", exist_ok=True)
    out = "reports/retrieval_diagnostic.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Detalle guardado en: {out}")


if __name__ == "__main__":
    main()