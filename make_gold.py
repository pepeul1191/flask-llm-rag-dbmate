#!/usr/bin/env python3
"""
generate_gold.py — Genera benchmarks/<schema>_gold.json desde el PUML.

El gold resultante es una representación canónica del PUML:
  - tablas en orden topológico (primero las que no dependen de nadie)
  - columnas con tipo SQL normalizado según el motor
  - PK inline
  - FKs en el lado hijo, derivadas de las relaciones del PUML
  - markers -- migrate:up / -- migrate:down

Uso:
    python generate_gold.py basico sqlite
    python generate_gold.py northwind postgres
    python generate_gold.py all              # todos los schemas, sqlite
"""
import json
import os
import sys

from ai.services.puml_parser import parse_puml_schema

TYPE_MAP = {
    "sqlite": {
        "int": "INTEGER", "string": "TEXT", "float": "REAL",
        "boolean": "INTEGER", "date": "TEXT", "datetime": "TEXT",
        "time": "TEXT", "uuid": "TEXT", "blob": "BLOB",
    },
    "mysql": {
        "int": "INT", "string": "VARCHAR(255)", "float": "FLOAT",
        "boolean": "BOOLEAN", "date": "DATE", "datetime": "DATETIME",
        "time": "TIME", "uuid": "CHAR(36)", "blob": "BLOB",
    },
    "postgres": {
        "int": "INTEGER", "string": "VARCHAR(255)", "float": "REAL",
        "boolean": "BOOLEAN", "date": "DATE", "datetime": "TIMESTAMP",
        "time": "TIME", "uuid": "UUID", "blob": "BYTEA",
    },
}


def _topo_sort(schema):
    """Ordena tablas para que las referenciadas vengan antes que las que las usan."""
    visited = set()
    order = []

    def visit(name):
        if name in visited:
            return
        visited.add(name)
        t = schema.tables[name]
        for fk in t.foreign_keys:
            ref = fk.ref_table.lower()
            if ref in schema.tables and ref not in visited:
                visit(ref)
        order.append(name)

    for name in list(schema.tables.keys()):
        visit(name)
    return order


def puml_to_sql(schema, db_type="sqlite"):
    tm = TYPE_MAP.get(db_type, TYPE_MAP["sqlite"])
    up_blocks, down_blocks = [], []

    for name in _topo_sort(schema):
        t = schema.tables[name]
        cols = []
        for c in t.columns.values():
            line = f"  {c.name} {tm.get(c.type, 'TEXT')}"
            if c.is_pk:
                line += " PRIMARY KEY"
            elif not c.is_nullable:
                line += " NOT NULL"
            cols.append(line)
        for fk in t.foreign_keys:
            cols.append(
                f"  FOREIGN KEY ({fk.column}) "
                f"REFERENCES {fk.ref_table}({fk.ref_column})"
            )
        up_blocks.append(
            f"CREATE TABLE {t.name} (\n" + ",\n".join(cols) + "\n);"
        )
        down_blocks.append(f"DROP TABLE IF EXISTS {t.name};")

    up = "-- migrate:up\n\n" + "\n\n".join(up_blocks)
    down = "-- migrate:down\n\n" + "\n".join(down_blocks)
    return up + "\n\n" + down


def generate(schema_name, db_type="sqlite"):
    puml_path = f"schemas/{schema_name}.puml"
    if not os.path.exists(puml_path):
        raise FileNotFoundError(puml_path)

    schema = parse_puml_schema(puml_path)
    sql = puml_to_sql(schema, db_type)

    out = {
        "samples": [
            {"id": f"{schema_name}_{db_type}_v1", "gold": sql}
        ]
    }
    os.makedirs("benchmarks", exist_ok=True)
    out_path = f"benchmarks/{schema_name}_gold.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"✓ {out_path}  ({len(schema.tables)} tablas, "
          f"{sum(len(t.columns) for t in schema.tables.values())} columnas, "
          f"{sum(len(t.foreign_keys) for t in schema.tables.values())} FKs)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generate_gold.py <schema|all> [db_type]")
        sys.exit(1)

    arg = sys.argv[1]
    db = sys.argv[2] if len(sys.argv) > 2 else "sqlite"

    if arg == "all":
        schemas = [
            os.path.splitext(f)[0]
            for f in sorted(os.listdir("schemas"))
            if f.endswith(".puml")
        ]
    else:
        schemas = [arg]

    for s in schemas:
        try:
            generate(s, db)
        except FileNotFoundError:
            print(f"✗ schemas/{s}.puml no existe")