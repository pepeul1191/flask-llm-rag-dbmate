# ai/evaluation/migration_metrics.py
"""
EX y FLEX adaptadas a migraciones SQL.

- EX  (Execution Accuracy): la migración generada y la gold ejecutan lo mismo
                             (mismo conjunto de tablas, columnas, tipos, PKs, FKs).
- FLEX (False-Less Execution): un LLM juzga si la migración es semánticamente
                             equivalente a la gold, aunque el texto difiera.
"""
import re
import logging
from typing import Dict
from ai.services.puml_parser import parse_puml_schema
from ai.services.sql_parser import parse_sql_schema

logger = logging.getLogger(__name__)


def _normalize_sql(sql: str) -> str:
    sql = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    sql = re.sub(r'\s+', ' ', sql)
    return sql.strip().lower()


def compute_ex(generated_sql: str, gold_sql: str, db_type: str) -> int:
    """
    EX=1 si generated y gold producen el mismo esquema (mismo conjunto de
    tablas/columnas/tipos/PKs/FKs). Es la versión SQL del EX de Spider.
    """
    try:
        gen_schema = parse_sql_schema(generated_sql, db_type)
        gold_schema = parse_sql_schema(gold_sql, db_type)
    except Exception as e:
        logger.error("EX parse error: %s", e)
        return 0

    gen_sig = _schema_signature(gen_schema)
    gold_sig = _schema_signature(gold_schema)
    return 1 if gen_sig == gold_sig else 0


def _schema_signature(schema) -> set:
    """Firma estructural: (tabla, col, tipo, es_pk) + (tabla, fk_col, ref)."""
    sig = set()
    for tname, t in schema.tables.items():
        for cname, c in t.columns.items():
            sig.add((tname, cname, c.type, c.is_pk))
        for fk in t.foreign_keys:
            sig.add((tname, "FK", fk.column, fk.ref_table, fk.ref_column))
    return sig


FLEX_PROMPT = """Eres un experto en bases de datos.

Compara estas dos migraciones SQL y decide si son SEMÁNTICAMENTE EQUIVALENTES
(mismo esquema resultante: mismas tablas, columnas, tipos, PKs y FKs),
aunque el texto no sea idéntico.

MIGRACIÓN A (referencia):
{gold}

MIGRACIÓN B (candidata):
{generated}

Responde SOLO con una palabra: EQUIVALENTES o DIFERENTES."""


def compute_flex(generated_sql: str, gold_sql: str, chain) -> int:
    """
    FLEX=1 si el LLM juzga que ambas migraciones son semánticamente equivalentes.
    `chain` es la cadena LangChain (CHAIN_PROMPT | llm | StrOutputParser).
    """
    try:
        prompt = FLEX_PROMPT.format(gold=gold_sql, generated=generated_sql)
        # CHAIN_PROMPT espera {"context": ..., "question": ...}
        verdict = chain.invoke({
            "context": "(sin contexto RAG, evaluación de equivalencia semántica)",
            "question": prompt,
        })
    except Exception as e:
        logger.error("FLEX invoke error: %s", e)
        return 0

    text = (verdict or "").strip().upper()
    return 1 if text.startswith("EQUIVALENTES") else 0


def compute_execution_metrics(
    samples: list[Dict],
    db_type: str,
    chain=None,
) -> Dict:
    """
    samples: [{"id": "...", "generated": "...", "gold": "..."}]
    """
    ex_scores, flex_scores = [], []
    per_sample = []
    for s in samples:
        ex = compute_ex(s["generated"], s["gold"], db_type)
        flex = compute_flex(s["generated"], s["gold"], chain) if chain else None
        ex_scores.append(ex)
        if flex is not None:
            flex_scores.append(flex)
        per_sample.append({
            "id": s.get("id"),
            "EX": ex,
            "FLEX": flex,
        })

    n = len(samples) or 1
    return {
        "n_samples": len(samples),
        "EX": round(sum(ex_scores) / n, 4),
        "FLEX": round(sum(flex_scores) / n, 4) if flex_scores else None,
        "per_sample": per_sample,
    }