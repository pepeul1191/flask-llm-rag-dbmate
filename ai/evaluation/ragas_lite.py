# ai/evaluation/ragas_lite.py
"""
Versión ligera de Faithfulness (RAGAS) sin instalar ragas.

Faithfulness = |statements supported by context| / |statements in answer|

Aproximación: descompone la migración generada en "unidades estructurales"
(tabla, columna, tipo, PK, FK) y verifica cuántas aparecen en el PUML.
Esto es una adaptación directa del Faithfulness de RAGAS al dominio de
esquemas, coherente con el paper de Flores et al.
"""
import logging
from ai.services.puml_parser import parse_puml_schema
from ai.services.sql_parser import parse_sql_schema

logger = logging.getLogger(__name__)


def compute_faithfulness(generated_sql: str, puml_file: str, db_type: str) -> dict:
    """
    Cuenta cuántos elementos estructurales de la migración están respaldados
    por el PUML (evidence). El resto se consideran "no soportados" = hallucination.
    """
    try:
        expected = parse_puml_schema(puml_file)
        generated = parse_sql_schema(generated_sql, db_type)
    except Exception as e:
        logger.error("Faithfulness parse error: %s", e)
        return {"faithfulness": None, "supported": 0, "total": 0}

    # Universo de "statements" = cada (tabla, col, tipo, is_pk) generado.
    statements = []
    for tname, t in generated.tables.items():
        for cname, c in t.columns.items():
            statements.append((tname, cname, c.type, c.is_pk))
        for fk in t.foreign_keys:
            statements.append((tname, "FK", fk.column, fk.ref_table))

    # Universo de evidencia = lo mismo pero extraído del PUML.
    evidence = set()
    for tname, t in expected.tables.items():
        for cname, c in t.columns.items():
            evidence.add((tname, cname, c.type, c.is_pk))
        for fk in t.foreign_keys:
            evidence.add((tname, "FK", fk.column, fk.ref_table))

    supported = sum(1 for s in statements if s in evidence)
    total = len(statements)
    return {
        "faithfulness": round(supported / total, 4) if total else 0.0,
        "supported": supported,
        "total": total,
    }