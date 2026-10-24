#!/usr/bin/env python3
"""
tools/make_benchmarks.py — Genera benchmarks para los .puml de schemas/

Para cada schemas/<name>.puml genera:
  benchmarks/<name>_retrieval.json — queries + chunk_ids relevantes
  benchmarks/<name>_gold.json      — migración SQL ideal (parse_puml_schema)

Uso:
    python tools/make_benchmarks.py                # todos los .puml
    python tools/make_benchmarks.py basico biblio  # solo esos
    python tools/make_benchmarks.py --force        # sobreescribe existentes
    python tools/make_benchmarks.py --check        # dry-run, no escribe
"""
import argparse
import contextlib
import io
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Silenciar el banner de retrieval.py al importar
with contextlib.redirect_stdout(io.StringIO()):
    from ai.services.ingestion import ingest_puml, split_documents
    from ai.services.puml_parser import parse_puml_schema
    from ai.services.fallback import map_puml_to_sql


ENTITY_RE = re.compile(r'entity\s+"?([A-Za-z_]\w*)"?', re.IGNORECASE)
DB_TYPE = "sqlite"


def build_retrieval(chunks, schema):
    """Genera queries con sus chunk_ids relevantes (enteros)."""
    name_to_chunk = {}
    for chunk in chunks:
        if chunk.metadata.get("chunk_type") != "entity":
            continue
        m = ENTITY_RE.search(chunk.page_content)
        if m:
            name_to_chunk[m.group(1).lower()] = chunk.metadata["chunk_id"]

    if not name_to_chunk:
        return None  # no entity chunks → probablemente line_chunk (falta apply_updates)

    queries = []

    # 1) Una query por entidad
    for name, cid in name_to_chunk.items():
        queries.append({
            "query": f"What are the columns of the {name} entity?",
            "relevant_chunks": [cid],
        })

    # 2) Una query por FK: "¿cómo se relacionan A y B?"
    for tname, table in schema.tables.items():
        src_id = name_to_chunk.get(tname.lower())
        if src_id is None:
            continue
        for fk in table.foreign_keys:
            tgt_id = name_to_chunk.get(fk.ref_table.lower())
            if tgt_id is None:
                continue
            queries.append({
                "query": f"How is {table.name} related to {fk.ref_table}?",
                "relevant_chunks": sorted({src_id, tgt_id}),
            })

    return {"queries": queries}


def build_gold(schema):
    """Genera SQL ideal a partir del SchemaModel ya parseado."""
    parts = []
    for tname, table in schema.tables.items():
        col_defs = []
        for cname, col in table.columns.items():
            if col.is_pk:
                col_defs.append(f"  {col.name} INTEGER PRIMARY KEY")
            else:
                sql_type = map_puml_to_sql(col.type, DB_TYPE)
                col_defs.append(f"  {col.name} {sql_type}")
        for fk in table.foreign_keys:
            col_defs.append(
                f"  FOREIGN KEY ({fk.column}) REFERENCES {fk.ref_table}({fk.ref_column})"
            )
        parts.append(f"CREATE TABLE {table.name} (\n" + ",\n".join(col_defs) + "\n);")

    sql = "\n\n".join(parts) + "\n"
    return {"samples": [{"id": "auto_gold_1", "gold": sql}]}


def process_puml(path: Path, force: bool, check: bool) -> None:
    name = path.stem
    r_path = _ROOT / "benchmarks" / f"{name}_retrieval.json"
    g_path = _ROOT / "benchmarks" / f"{name}_gold.json"

    if not force and r_path.exists() and g_path.exists():
        print(f"[SKIP] {name:<16} ya existen ambos (usa --force)")
        return

    content = ingest_puml(str(path))
    if content is None:
        print(f"[FAIL] {name:<16} no se pudo leer {path}")
        return

    chunks = split_documents(content, str(path))
    schema = parse_puml_schema(str(path))

    retrieval = build_retrieval(chunks, schema)
    if retrieval is None:
        print(f"[FAIL] {name:<16} sin entity chunks (corre 'apply_updates.py' primero)")
        return

    gold = build_gold(schema)

    n_t  = len(schema.tables)
    n_fk = sum(len(t.foreign_keys) for t in schema.tables.values())
    n_q  = len(retrieval["queries"])

    if check:
        print(f"[DRY]  {name:<16} {n_t:>2} tablas, {n_fk:>2} FKs, {n_q:>2} queries")
        return

    r_path.parent.mkdir(parents=True, exist_ok=True)
    r_path.write_text(json.dumps(retrieval, indent=2, ensure_ascii=False), encoding="utf-8")
    g_path.write_text(json.dumps(gold, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[DONE] {name:<16} {n_t:>2} tablas, {n_fk:>2} FKs, {n_q:>2} queries")
    print(f"       -> benchmarks/{name}_retrieval.json")
    print(f"       -> benchmarks/{name}_gold.json")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("names", nargs="*", help="basenames sin .puml (default: todos)")
    ap.add_argument("--force", action="store_true", help="sobreescribe si ya existen")
    ap.add_argument("--check", action="store_true", help="dry-run")
    args = ap.parse_args()

    schemas_dir = _ROOT / "schemas"
    if not schemas_dir.exists():
        print(f"[FAIL] no existe {schemas_dir}")
        sys.exit(1)

    if args.names:
        paths = [schemas_dir / f"{n}.puml" for n in args.names]
        for p in paths:
            if not p.exists():
                print(f"[FAIL] no existe {p}")
                sys.exit(1)
    else:
        paths = sorted(schemas_dir.glob("*.puml"))

    if not paths:
        print(f"[FAIL] no hay .puml en {schemas_dir}")
        sys.exit(1)

    for p in paths:
        process_puml(p, args.force, args.check)


if __name__ == "__main__":
    main()