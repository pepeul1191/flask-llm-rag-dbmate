# ================================================================
# Archivo generado automáticamente por merge_ai.sh
# Fecha: 2026-10-31 12:46:46
# NO EDITAR MANUALMENTE - se regenera en cada ejecución
# ================================================================

# ================================================================
# Archivo: env.py
# ================================================================
# ai/env.py
"""
Carga .env y expone helpers de configuración.
Debe importarse ANTES de ai.services.* para que OLLAMA_MODEL
esté disponible cuando retrieval.py calcula MODEL_NAME.
"""
import os
from dotenv import load_dotenv

# Cargar .env de la raíz del proyecto (3 niveles arriba de este archivo)
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
load_dotenv(os.path.join(_ROOT, ".env"))


def get_model_name() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3.2")


def flores_enabled(metric: str) -> bool:
    """Activa/desactiva métricas Flores individuales desde .env."""
    key = f"AI_FLORES_{metric.upper()}"
    return os.getenv(key, "1") == "1"


def flores_export_enabled() -> bool:
    return os.getenv("AI_FLORES_EXPORT", "1") == "1"

# ================================================================
# Archivo: evaluation/migration_metrics.py
# ================================================================
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
    if chain is None:
        return 0
    prompt = FLEX_PROMPT.format(gold=gold_sql, generated=generated_sql)

    verdict = None
    try:
        verdict = chain.invoke({"input": prompt})
    except Exception as e1:
        try:
            verdict = chain.invoke({
                "context": "(sin contexto RAG)",
                "question": prompt,
            })
        except Exception as e2:
            logger.error("FLEX invoke error: %s | %s", e1, e2)
            return 0

    text = (verdict or "").strip().upper()

    # Matcher robusto
    positives = ("EQUIVALENTES", "EQUIVALENT", "SÍ", "SI", "YES", "TRUE", "1")
    negatives = ("DIFERENTES", "DIFERENT", "NO", "FALSE", "0")

    # Primero buscar negativos (más específicos)
    for neg in negatives:
        if text.startswith(neg):
            return 0

    # Luego buscar positivos
    for pos in positives:
        if text.startswith(pos):
            return 1

    # Si no matchea nada, buscar en el texto completo
    if "EQUIVALENT" in text and "DIFERENT" not in text:
        return 1

    logger.warning("FLEX verdict no reconocido: %r", text[:100])
    return 0


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

# ================================================================
# Archivo: evaluation/nlg_metrics.py
# ================================================================
"""
BERTScore F1, BLEU, ROUGE (F1), comparando migración generada vs gold.
"""
# [dedup] import logging

logger = logging.getLogger(__name__)


def compute_nlg_metrics(generations: list[str], references: list[str]) -> dict:
    """
    Requiere:
      pip install bert-score sacrebleu rouge-score
    """
    out = {}
    try:
        from bert_score import score as bscore
        # Forzar CPU y modelo pequeño
        P, R, F1 = bscore(
            generations, references,
            lang="en",
            verbose=False,
            device="cpu",                          # ← CPU en lugar de GPU
            model_type="distilbert-base-uncased",  # ← modelo 6x más pequeño
        )
        out["BERTScore_F1"] = round(float(F1.mean()), 4)
    except Exception as e:
        logger.warning("BERTScore no disponible: %s", e)
        out["BERTScore_F1"] = None

    try:
        from sacrebleu.metrics import BLEU
        bleu = BLEU()
        out["BLEU"] = round(bleu.corpus_score(generations, [references]).score / 100, 4)
    except Exception as e:
        logger.warning("BLEU no disponible: %s", e)
        out["BLEU"] = None

    try:
        from rouge_score import rouge_scorer
        scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
        r1, r2, rl = [], [], []
        for g, r in zip(generations, references):
            s = scorer.score(r, g)
            r1.append(s["rouge1"].fmeasure)
            r2.append(s["rouge2"].fmeasure)
            rl.append(s["rougeL"].fmeasure)
        n = len(generations) or 1
        out["ROUGE-1_F1"] = round(sum(r1) / n, 4)
        out["ROUGE-2_F1"] = round(sum(r2) / n, 4)
        out["ROUGE-L_F1"] = round(sum(rl) / n, 4)
    except Exception as e:
        logger.warning("ROUGE no disponible: %s", e)
        out["ROUGE-1_F1"] = out["ROUGE-2_F1"] = out["ROUGE-L_F1"] = None

    return out

# ================================================================
# Archivo: evaluation/ragas_lite.py
# ================================================================
# ai/evaluation/ragas_lite.py
"""
Versión ligera de Faithfulness (RAGAS) sin instalar ragas.

Faithfulness = |statements supported by context| / |statements in answer|

Aproximación: descompone la migración generada en "unidades estructurales"
(tabla, columna, tipo, PK, FK) y verifica cuántas aparecen en el PUML.
Esto es una adaptación directa del Faithfulness de RAGAS al dominio de
esquemas, coherente con el paper de Flores et al.
"""
# [dedup] import logging
# [dedup] from ai.services.puml_parser import parse_puml_schema
# [dedup] from ai.services.sql_parser import parse_sql_schema

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

# ================================================================
# Archivo: evaluation/retrieval_metrics.py
# ================================================================
# ai/evaluation/retrieval_metrics.py
"""
Precision@K, Recall@K, MAP, MAP+, MRR, NDCG@K, Top-1.

Réplica la Tabla 6 del paper: MAP, MAP+, P@5, R@5, NDCG@5.

Robustez:
  - Deduplica retrieved_ids (evita R@5 > 1 cuando el retriever devuelve
    el mismo chunk_id varias veces por acumulación en el vector store).
  - Clampea recall/AP/NDCG a 1.0 por seguridad numérica.
  - Ignora IDs None (chunks sin metadata.chunk_id).
"""
# [dedup] import logging
import math
from typing import List, Dict

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Helpers internos
# --------------------------------------------------------------------------- #
def _dedup_truncate(retrieved: List, k: int) -> List:
    """Elimina duplicados preservando el orden y trunca a k."""
    seen = set()
    out = []
    for r in retrieved:
        if r is None:
            continue
        if r in seen:
            continue
        seen.add(r)
        out.append(r)
        if len(out) >= k:
            break
    return out


def _precision_at_k(retrieved: List[str], relevant: set, k: int) -> float:
    if k <= 0:
        return 0.0
    topk = retrieved[:k]
    hits = sum(1 for r in topk if r in relevant)
    return min(hits / k, 1.0)


def _recall_at_k(retrieved: List[str], relevant: set, k: int) -> float:
    if not relevant:
        return 0.0
    topk = retrieved[:k]
    hits = sum(1 for r in topk if r in relevant)
    return min(hits / len(relevant), 1.0)


def _average_precision(retrieved: List[str], relevant: set) -> float:
    if not relevant:
        return 0.0
    hits, precisions = 0, []
    for i, r in enumerate(retrieved, 1):
        if r in relevant:
            hits += 1
            precisions.append(hits / i)
    if not precisions:
        return 0.0
    return min(sum(precisions) / len(relevant), 1.0)


def _reciprocal_rank(retrieved: List[str], relevant: set) -> float:
    for i, r in enumerate(retrieved, 1):
        if r in relevant:
            return 1.0 / i
    return 0.0


def _ndcg_at_k(retrieved: List[str], relevant: set, k: int) -> float:
    """NDCG@K con relevancia binaria (1 si el chunk_id está en relevant)."""
    topk = retrieved[:k]
    dcg = 0.0
    for i, r in enumerate(topk, 1):
        if r in relevant:
            dcg += 1.0 / math.log2(i + 1)
    n_rel = min(len(relevant), k)
    if n_rel == 0:
        return 0.0
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, n_rel + 1))
    if idcg <= 0:
        return 0.0
    return min(dcg / idcg, 1.0)


# --------------------------------------------------------------------------- #
# Métrica principal
# --------------------------------------------------------------------------- #
def compute_retrieval_metrics(
    queries: List[Dict],
    retriever,
    k: int = 5,
) -> Dict:
    """
    queries: [{"query": "...", "relevant_chunks": [0, 1]}]
    retriever: objeto invocable con .invoke(query) -> list[Document]

    Devuelve:
      - Métricas a K principal: Precision@K, Recall@K, MAP, MAP+, MRR, NDCG@K, Top1
      - Métricas fijas a K=5 (Tabla 6 del paper): P@5, R@5, NDCG@5
      - per_query: detalle por query (útil para diagnóstico)
    """
    p_at_k, r_at_k, aps, rrs, top1, ndcgs = [], [], [], [], [], []
    p5, r5, n5 = [], [], []
    per_query = []

    for q in queries:
        # 1. Obtener docs del retriever
        docs = retriever.invoke(q["query"])

        # 2. Extraer chunk_ids
        raw_ids = [d.metadata.get("chunk_id") for d in docs]

        # 3. Deduplicar (importante: evita R@5 > 1)
        retrieved_ids = _dedup_truncate(raw_ids, k)

        # 4. Conjunto de relevantes
        relevant = set(q.get("relevant_chunks", []))

        # 5. Calcular métricas a K principal
        p = _precision_at_k(retrieved_ids, relevant, k)
        r = _recall_at_k(retrieved_ids, relevant, k)
        ap = _average_precision(retrieved_ids, relevant)
        rr = _reciprocal_rank(retrieved_ids, relevant)
        ndcg = _ndcg_at_k(retrieved_ids, relevant, k)
        t1 = 1.0 if retrieved_ids and retrieved_ids[0] in relevant else 0.0

        p_at_k.append(p)
        r_at_k.append(r)
        aps.append(ap)
        rrs.append(rr)
        top1.append(t1)
        ndcgs.append(ndcg)

        # 6. Métricas fijas a K=5 (Tabla 6 del paper)
        #    Nota: se calculan sobre el mismo retrieved_ids ya deduplicado,
        #    truncando a 5 explícitamente.
        top5_ids = retrieved_ids[:5]
        p5.append(_precision_at_k(top5_ids, relevant, 5))
        r5.append(_recall_at_k(top5_ids, relevant, 5))
        n5.append(_ndcg_at_k(top5_ids, relevant, 5))

        per_query.append({
            "query": q["query"],
            "retrieved": retrieved_ids,
            "relevant": sorted(relevant),
            "hits": sum(1 for r in retrieved_ids if r in relevant),
            "P@K": round(p, 4),
            "R@K": round(r, 4),
            "AP": round(ap, 4),
            "RR": round(rr, 4),
            "NDCG@K": round(ndcg, 4),
            "Top1": t1,
            "P@5": round(p5[-1], 4),
            "R@5": round(r5[-1], 4),
            "NDCG@5": round(n5[-1], 4),
        })

    n = len(queries) or 1
    positive_aps = [ap for ap in aps if ap > 0.0]

    return {
        "K": k,
        "n_queries": len(queries),

        # Métricas a K principal
        "Precision@K": round(sum(p_at_k) / n, 4),
        "Recall@K":    round(sum(r_at_k) / n, 4),
        "MAP":         round(sum(aps) / n, 4),
        "MAP+":        round(sum(positive_aps) / len(positive_aps), 4)
                       if positive_aps else 0.0,
        "MRR":         round(sum(rrs) / n, 4),
        "NDCG@K":      round(sum(ndcgs) / n, 4),
        "Top1":        round(sum(top1) / n, 4),

        # Métricas fijas a K=5 (Tabla 6 del paper)
        "P@5":         round(sum(p5) / n, 4),
        "R@5":         round(sum(r5) / n, 4),
        "NDCG@5":      round(sum(n5) / n, 4),

        # Trazabilidad
        "per_query":   per_query,
    }

# ================================================================
# Archivo: main.py
# ================================================================
#!/usr/bin/env python
# [dedup] import os
import sys
import json
import time
# [dedup] import logging
import datetime
import inspect
from ai import env

from ai.paths import output_base, under_output
from ai.services.vector_store import (
  check_existing_vector_db,
  should_recreate_vector_db,
  create_vector_db
)
from ai.services.ingestion import ingest_puml, split_documents
from ai.services.retrieval import create_retriever, create_chain, create_direct_chain
from ai.services.migration_generator import (
  generate_sql_migrations_with_rag,
  generate_sql_migrations_direct,
  parse_migration_blocks,
  enforce_original_names,
  save_migration_files
)
from ai.services.fallback import generate_direct_migrations
# [dedup] from ai.services.puml_parser import parse_puml_schema
# [dedup] from ai.services.sql_parser import parse_sql_schema
from ai.services.structural_validator import validate_schema
from ai.services.evaluation import compute_structural_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_MODES = ("llm_only", "rag", "rag_validation")

# 🔧 CAMBIO: máximo de iteraciones del bucle de corrección en rag_validation.
# Configurable por env var AI_MAX_CORRECTION_ITERS (default 3, igual que el paper).
MAX_CORRECTION_ITERATIONS = int(os.getenv("AI_MAX_CORRECTION_ITERS", "3"))

# 🔧 CAMBIO: detecta si migration_generator.py soporta feedback de errores.
# Si no lo soporta, rag_validation degrada a una sola pasada (y lo avisa).
_HAS_EXTRA_INSTRUCTIONS = (
  "extra_instructions" in inspect.signature(
    generate_sql_migrations_with_rag
  ).parameters
)

_AI_TIMING = os.getenv("AI_TIMING", "0") == "1"


def _timed(label, fn, *args, **kwargs):
  if not _AI_TIMING:
    return fn(*args, **kwargs)
  t0 = time.perf_counter()
  try:
    return fn(*args, **kwargs)
  finally:
    print(f"⏱ [timing] {label}: {time.perf_counter()-t0:.3f}s")


def _build_chain(mode: str, vector_db, puml_file: str):
  if mode == "llm_only":
    return create_direct_chain()
  retriever = create_retriever(vector_db, source_file=puml_file)
  return create_chain(retriever)


def _generate_migrations(mode: str, chain, db_type: str, puml_file: str) -> str:
  """Genera las migraciones según el modo (una sola pasada, sin corrección)."""
  if mode == "llm_only":
    return generate_sql_migrations_direct(chain, db_type, puml_file)

  complete = generate_sql_migrations_with_rag(chain, db_type, puml_file)

  refused = (
    "No puedo cumplir" in complete
    or "I cannot fulfill" in complete
    or complete.startswith("Error:")
  )
  if refused:
    print("⚠️ El modelo rechazó generar migraciones. Usando método alternativo...")
    complete = generate_direct_migrations(puml_file, db_type)
  return complete


# 🔧 CAMBIO: bucle de generación + validación + corrección (modo rag_validation).
def _generate_with_correction(chain, db_type: str, puml_file: str,
                              max_iter: int = MAX_CORRECTION_ITERATIONS):
    """
    Genera migraciones con bucle de corrección (modo rag_validation).

    🔧 FIX 3: guarda la MEJOR iteración (no la última) según un score
    compuesto que prioriza FullSchema y FK. Garantiza que rag_validation
    nunca sea peor que rag en las métricas estructurales clave.

    Returns:
        (best_sql, best_iter, best_report, best_metrics)
    """
    def _score(metrics):
        if not metrics:
            return -1.0
        return (
            metrics.get("table_accuracy", 0) * 2.0
            + (metrics.get("foreign_key_accuracy") or 0) * 3.0
            + metrics.get("f1", 0)
            + metrics.get("full_schema_accuracy", 0) * 5.0
        )

    # Primera pasada (idéntica a 'rag')
    sql = _generate_migrations("rag", chain, db_type, puml_file)
    if not sql or sql.startswith("Error:"):
        return sql, 0, None, None

    best = {
        "sql": sql,
        "score": -1.0,
        "iter": 0,
        "report": None,
        "metrics": None,
    }

    for i in range(max_iter):
        try:
            report, metrics = _validate_structure(
                puml_file, sql, db_type, verbose=False
            )
        except Exception as e:
            logger.error(f"Error validando iteración {i}: {e}")
            break

        score = _score(metrics)
        logger.info(f"[iter {i}] score={score:.2f} "
                    f"TA={metrics.get('table_accuracy') if metrics else '?'} "
                    f"FK={metrics.get('foreign_key_accuracy') if metrics else '?'} "
                    f"F1={metrics.get('f1') if metrics else '?'} "
                    f"Full={metrics.get('full_schema_accuracy') if metrics else '?'}")

        if score > best["score"]:
            best = {
                "sql": sql,
                "score": score,
                "iter": i,
                "report": report,
                "metrics": metrics,
            }

        # Éxito: no hay nada que corregir
        if report is None or report.is_valid:
            if i > 0:
                print(f"✅ Validación OK tras {i} iteración(es)")
            return sql, i, report, metrics

        # ¿Podemos pasar feedback al LLM?
        if not _HAS_EXTRA_INSTRUCTIONS:
            logger.warning(
                "migration_generator no acepta 'extra_instructions'. "
                "Bucle de corrección desactivado."
            )
            return best["sql"], best["iter"], best["report"], best["metrics"]

        # Reportar errores y re-generar
        n_missing_tables = len(report.missing_tables)
        n_missing_cols = sum(len(v) for v in report.missing_columns.values())
        n_type = sum(len(v) for v in report.type_mismatches.values())
        n_pk = len(report.pk_mismatches)
        n_fk = len(report.fk_mismatches)
        print(
            f"🔄 Corrección {i+1}/{max_iter}: "
            f"{n_missing_tables} tablas, {n_missing_cols} cols, "
            f"{n_type} tipos, {n_pk} PKs, {n_fk} FKs"
        )

        sql = generate_sql_migrations_with_rag(
            chain, db_type, puml_file,
            extra_instructions=report.summary(),
        )
        if not sql or sql.startswith("Error:"):
            break

    # Devolver la MEJOR iteración encontrada
    if best["iter"] != max_iter - 1:
        print(f"🔙 Revertido a iteración {best['iter']} (score={best['score']:.2f})")
    return best["sql"], best["iter"], best["report"], best["metrics"]

def _load_vector_db(puml_file: str):
  vector_db = check_existing_vector_db()
  if should_recreate_vector_db(puml_file, vector_db):
    print("🔄 Creando nueva base de datos vectorial...")
    content = ingest_puml(puml_file)
    if not content:
      return None
    chunks = split_documents(content, puml_file)
    vector_db = create_vector_db(chunks, puml_file)
    print(f"✅ Vector DB recreada con {len(chunks)} chunks.")
  else:
    print("✅ Usando base de datos vectorial existente.")
  return vector_db


# 🔧 CAMBIO: parámetro 'verbose' para no spamear en el bucle de corrección.
def _validate_structure(puml_file: str, complete_migrations: str, db_type: str,
                        verbose: bool = True):
  """Valida la estructura generada contra el modelo PUML esperado."""
  if verbose:
    print("\n" + "=" * 60)
    print("VALIDACIÓN ESTRUCTURAL CONTRA EL MODELO PUML")
    print("=" * 60)

  try:
    expected_schema = parse_puml_schema(puml_file)
  except Exception as e:
    logger.error(f"Error parsing PUML schema: {e}")
    return None, None

  try:
    generated_schema = parse_sql_schema(complete_migrations, db_type)
  except Exception as e:
    logger.error(f"Error parsing generated SQL: {e}")
    return expected_schema, None

  report = validate_schema(expected_schema, generated_schema)

  if verbose:
    print(report.summary())

  metrics = compute_structural_metrics(report)

  if verbose:
    print("\n" + "-" * 60)
    print("MÉTRICAS ESTRUCTURALES")
    print("-" * 60)
    for key, value in metrics.items():
      print(f"  {key}: {value}")

  return report, metrics


# 🔧 CAMBIO: parámetro 'correction_iters' para persistirlo en metrics_*.json.
def _persist_reports(puml_basename: str, mode: str, db_type: str,
                     report, metrics, tables_dict,
                     correction_iters: int = 0) -> None:
  """Guarda el reporte de validación y las métricas en JSON dentro de tmp/."""
  run_id = os.getenv("AI_RUN_ID")
  if run_id:
    base = f"{run_id}_{puml_basename}_{db_type}_{mode}"
  else:
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    base = f"{puml_basename}_{db_type}_{mode}_{ts}"

  # Añadir iteraciones de corrección a las métricas (útil para el paper)
  if metrics is not None and correction_iters is not None:
    metrics = dict(metrics)
    metrics["correction_iterations"] = correction_iters

  if report is not None:
    report_file = under_output(f"validation_report_{base}.json")
    with open(report_file, "w", encoding="utf-8") as f:
      json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"✓ Reporte de validación guardado en: {report_file}")

  if metrics is not None:
    metrics_file = under_output(f"metrics_{base}.json")
    with open(metrics_file, "w", encoding="utf-8") as f:
      json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"✓ Métricas guardadas en: {metrics_file}")

  if tables_dict:
    dict_file = under_output(f"migrations_dict_{base}.json")
    with open(dict_file, "w", encoding="utf-8") as f:
      json.dump({k: v.__dict__ for k, v in tables_dict.items()},
                f, indent=2, ensure_ascii=False)
    print(f"✓ Diccionario de migraciones guardado en: {dict_file}")


def execute(folder_path: str, db_type: str, mode: str = "rag_validation"):
  """
  Orquesta la generación y validación de migraciones SQL desde PUML.

  Args:
    folder_path: carpeta que contiene modelo.puml
    db_type: sqlite | mysql | postgres
    mode: llm_only | rag | rag_validation
  Returns:
    (resultado, exito)
  """
  if mode not in VALID_MODES:
    return f"❌ Modo inválido: {mode}. Use uno de {VALID_MODES}", False

  print(f"DEMO - Generación de migraciones SQL desde PUML (modo={mode})")

  puml_file = os.path.join(folder_path, "modelo.puml")
  if not os.path.exists(puml_file):
    print(f"❌ Archivo PUML no encontrado en {puml_file}")
    return "❌ Archivo no encontrado", False

  # 1. Base vectorial (solo si el modo la requiere)
  vector_db = None
  if mode in ("rag", "rag_validation"):
    vector_db = _load_vector_db(puml_file)

  # 2. Construir cadena
  chain = _build_chain(mode, vector_db, puml_file)

  # 3. Generar migraciones
  print(f"🔄 Generando migraciones SQL para {puml_file} (db={db_type}, mode={mode})...")

  # 🔧 CAMBIO: rama con/sin bucle de corrección
  correction_iters = 0
  report = None
  metrics = None

  if mode == "rag_validation":
    complete_migrations, correction_iters, report, metrics = _timed(
      "llm_generation_with_correction",
      _generate_with_correction, chain, db_type, puml_file
    )
    print(f"✓ Generación con corrección completada en {correction_iters} iteración(es)")
  else:
    complete_migrations = _timed(
      "llm_generation",
      _generate_migrations, mode, chain, db_type, puml_file
    )

  if not complete_migrations or complete_migrations.startswith("Error:"):
    print("❌ No se pudieron generar migraciones.")
    return "❌ No se pudieron generar migraciones.", False

  # 4. Mostrar resultado
  print("\n" + "=" * 60)
  print(f"MIGRACIONES SQL GENERADAS PARA: {puml_file}")
  print("=" * 60)
  print(complete_migrations)

  # 5. Parsear y organizar
  print("\n" + "=" * 60)
  print("ORGANIZANDO EN DICCIONARIO:")
  print("=" * 60)
  tables_dict = parse_migration_blocks(complete_migrations)
  if not tables_dict:
    print("❌ No se pudieron parsear las migraciones.")
    return "❌ No se pudieron parsear las migraciones.", False

  tables_dict = enforce_original_names(puml_file, tables_dict)

  resp = []
  print(f"\n✅ Se procesaron {len(tables_dict)} tablas ÚNICAS:\n")
  for key, table in tables_dict.items():
    print(f"Tabla {key} ({table.table_name}):")
    print(f"  UP:   {table.up}")
    print(f"  DOWN: {table.down}")
    print("-" * 80)
    resp.append(table.__dict__)

  # 6. Validación estructural final para el reporte
  #    - rag_validation: ya viene del bucle -> no repetir
  #    - llm_only / rag: validar ahora
  if report is None:
    report, metrics = _timed(
      "structural_validation",
      _validate_structure, puml_file, complete_migrations, db_type
    )

  if report is None:
    print("⚠️ No se pudo completar la validación estructural.")
  elif report.is_valid:
    print("✅ Validación estructural: SIN ERRORES detectados.")
  else:
    print("⚠️ Validación estructural: se detectaron diferencias.")

  # 7. Guardar archivos
  puml_basename = os.getenv("AI_PUML_BASENAME") or \
                os.path.splitext(os.path.basename(puml_file))[0]
  save_migration_files(tables_dict, puml_basename, db_type, complete_migrations)

  _persist_reports(
    puml_basename, mode, db_type, report, metrics, tables_dict,
    correction_iters=correction_iters,
  )

  return resp, True


def run_comparison(folder_path: str, db_type: str):
  """
  Ejecuta los tres modos sobre el mismo PUML y compara resultados.
  Útil para responder al Reviewer 1 (LLM vs RAG vs RAG+validación).
  """
  results = {}
  for mode in VALID_MODES:
    print("\n" + "#" * 70)
    print(f"# MODO: {mode}")
    print("#" * 70)
    resp, ok = execute(folder_path, db_type, mode=mode)
    results[mode] = {"success": ok, "tables": len(resp) if ok else 0}

  print("\n" + "=" * 70)
  print("RESUMEN COMPARATIVO")
  print("=" * 70)
  for mode, data in results.items():
    status = "✅" if data["success"] else "❌"
    print(f"  {status} {mode}: {data['tables']} tablas")

  summary_file = f"comparison_{os.path.basename(folder_path)}_{db_type}.json"
  with open(summary_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
  print(f"\n✓ Resumen comparativo guardado en: {summary_file}")
  return results


if __name__ == "__main__":
  if len(sys.argv) < 3:
    print("Uso: python -m ai.main <carpeta_o_puml> <tipo_db> [modo]")
    print("  modo: llm_only | rag | rag_validation | compare | errors | pipeline")
    sys.exit(1)

  folder = sys.argv[1]
  db = sys.argv[2]
  mode = sys.argv[3] if len(sys.argv) > 3 else "rag_validation"

  if mode == "compare":
    run_comparison(folder, db)
  elif mode == "errors":
    from ai.pipeline import run_structural_validation_tests
    result = run_structural_validation_tests(folder, db)
    print("\n" + "=" * 60)
    print("RESULTADO DE TESTS DE VALIDACIÓN ESTRUCTURAL")
    print("=" * 60)
    print("Aggregate:", result["aggregate"])
    for etype, m in result["per_error_type"].items():
      print(f"  {etype}: {m}")
  elif mode == "pipeline":
    from ai.pipeline import run_from_config
    cfg_path = sys.argv[4] if len(sys.argv) > 4 else "pipeline_config.json"
    run_from_config(cfg_path)
  else:
    execute(folder, db, mode=mode)

# ================================================================
# Archivo: models/migration.py
# ================================================================
# ai/models/migration.py
from dataclasses import dataclass


@dataclass
class TableMigration:
  """Representa una migración para una tabla."""
  table_name: str
  up: str          # sentencia CREATE TABLE
  down: str        # sentencia DROP TABLE
  complete_block: str  # bloque completo con -- migrate:up/down
  index: int = 0   # orden de aparición

# ================================================================
# Archivo: models/schema.py
# ================================================================
# ai/models/schema.py
from dataclasses import dataclass, field

@dataclass
class ColumnSchema:
  """Columna dentro de una tabla."""
  name: str
  type: str
  is_pk: bool = False
  is_nullable: bool = True
  is_unique: bool = False
  default: str | None = None


@dataclass
class ForeignKeySchema:
  """Relación de clave foránea."""
  column: str
  ref_table: str
  ref_column: str


@dataclass
class TableSchema:
  """Tabla con sus columnas y FKs."""
  name: str
  columns: dict[str, ColumnSchema] = field(default_factory=dict)
  foreign_keys: list[ForeignKeySchema] = field(default_factory=list)


@dataclass
class SchemaModel:
  """Modelo de esquema completo (esperado o generado)."""
  tables: dict[str, TableSchema] = field(default_factory=dict)

  def table(self, name: str) -> TableSchema | None:
    return self.tables.get(name.lower())

  def add_table(self, table: TableSchema) -> None:
    self.tables[table.name.lower()] = table

# ================================================================
# Archivo: paths.py
# ================================================================
# ai/paths.py
# [dedup] import os

DEFAULT_OUTPUT_DIR = "./tmp"


def output_base() -> str:
    """
    Devuelve el directorio base donde se escriben todos los artefactos.
    Se controla con la variable de entorno APP_OUTPUT_DIR.
    Por defecto: ./tmp (relativo al cwd desde donde se ejecuta).
    """
    base = os.environ.get("APP_OUTPUT_DIR", DEFAULT_OUTPUT_DIR)
    os.makedirs(base, exist_ok=True)
    return base


def under_output(*parts: str) -> str:
    """Une el base con los fragmentos dados, creando la carpeta si hace falta."""
    path = os.path.join(output_base(), *parts)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path

# ================================================================
# Archivo: pipeline/config.py
# ================================================================
# ai/pipeline/config.py
"""
Configuración única del pipeline.

Se puede construir a mano (PipelineConfig(...)) o cargar desde JSON:

    cfg = PipelineConfig.from_json("pipeline_config.json")

Acepta "inputs" o "folder_paths" en el JSON. Cada entrada de `inputs` puede ser:
  - una carpeta que contiene "modelo.puml"
  - una carpeta que contiene algún .puml / .plantuml / .pu
  - la ruta directa a un archivo .puml / .plantuml / .pu
"""

from dataclasses import dataclass, field, asdict
# [dedup] import json
from typing import List


# Stages disponibles (referencia rápida; el runner los registra):
#
#   GENERATION_STAGES:
#     - execute             -> llama a main.execute (genera migraciones)
#     - retrieval_metrics   -> MAP, MRR, P@K, R@K, Top-1  (Flores et al. Table 11)
#     - execution_metrics   -> EX, FLEX                    (Flores et al. Table 15)
#     - nlg_metrics         -> BERTScore, BLEU, ROUGE      (Flores et al. Table 16)
#     - faithfulness        -> Faithfulness (RAGAS-lite)   (Flores et al. Table 16)
#
#   ERROR_STAGES:
#     - inject_and_validate -> inyecta errores estructurales conocidos
#     - measure_detection   -> TP/FN/FP, precision, recall, F1


@dataclass
class PipelineConfig:
    # ------------------------------------------------------------------ #
    # Inputs                                                             #
    # ------------------------------------------------------------------ #
    # Cada entrada puede ser carpeta o archivo .puml (ver docstring arriba).
    inputs: List[str] = field(default_factory=list)

    db_types: List[str] = field(default_factory=lambda: ["sqlite"])
    modes: List[str] = field(default_factory=lambda: [
        "llm_only", "rag", "rag_validation"
    ])

    # ------------------------------------------------------------------ #
    # Stages activos                                                     #
    # ------------------------------------------------------------------ #
    # Fase 1: generación + validación + métricas tipo Flores et al.
    generation_stages: List[str] = field(default_factory=lambda: [
        "execute",
        "build_retriever",
        # Los siguientes requieren benchmarks en benchmark_dir.
        # Si no existen, el stage se salta silenciosamente.
        "build_retriever",
        "retrieval_metrics",
        "execution_metrics",
        "nlg_metrics",
        "faithfulness",
    ])

    # Fase 2: tests de errores inyectados (Reviewer 1)
    error_stages: List[str] = field(default_factory=lambda: [
        "inject_and_validate",
        "measure_detection",
    ])

    # ------------------------------------------------------------------ #
    # Configuración de los tests de errores                              #
    # ------------------------------------------------------------------ #
    error_types: List[str] = field(default_factory=lambda: [
        "drop_table",
        "drop_column",
        "change_type",
        "drop_pk",
        "drop_fk",
        "rename_table",
    ])
    include_clean_baseline: bool = True

    # ------------------------------------------------------------------ #
    # Configuración de benchmarks / métricas tipo Flores et al.          #
    # ------------------------------------------------------------------ #
    # Carpeta donde viven los benchmarks por PUML:
    #   <benchmark_dir>/<puml_basename>_retrieval.json   -> MAP/MRR/P@K/R@K/Top1
    #   <benchmark_dir>/<puml_basename>_gold.json        -> EX/FLEX/BLEU/ROUGE
    benchmark_dir: str = "./benchmarks"

    # K para Precision@K / Recall@K del retriever
    retrieval_k: int = 5

    # ------------------------------------------------------------------ #
    # Salida                                                             #
    # ------------------------------------------------------------------ #
    output_dir: str = "./tmp/pipeline_results"
    save_individual_reports: bool = True

    # ------------------------------------------------------------------ #
    # Compatibilidad hacia atrás: "folder_paths" como alias de "inputs"   #
    # ------------------------------------------------------------------ #
    @property
    def folder_paths(self) -> List[str]:
        return self.inputs

    @folder_paths.setter
    def folder_paths(self, value: List[str]) -> None:
        self.inputs = value

    # ------------------------------------------------------------------ #
    # Serialización                                                      #
    # ------------------------------------------------------------------ #
    @classmethod
    def from_json(cls, path: str) -> "PipelineConfig":
        """
        Carga la config desde JSON. Acepta "inputs" o "folder_paths".
        Ignora silenciosamente claves desconocidas para tolerar configs
        antiguas o comentarios extra.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Alias folder_paths -> inputs
        if "folder_paths" in data and "inputs" not in data:
            data["inputs"] = data.pop("folder_paths")

        # Filtrar solo campos declarados en el dataclass
        valid_keys = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in data.items() if k in valid_keys}

        return cls(**filtered)

    def to_json(self, path: str) -> None:
        """
        Guarda la config como JSON. Útil para congelar la corrida y adjuntarla
        como material suplementario (reproducibilidad, Reviewer 2).
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------ #
    # Utilidades                                                         #
    # ------------------------------------------------------------------ #
    def enabled_generation_stages(self) -> List[str]:
        """Devuelve solo los stages de generación no vacíos."""
        return [s for s in self.generation_stages if s]

    def enabled_error_stages(self) -> List[str]:
        """Devuelve solo los stages de error no vacíos."""
        return [s for s in self.error_stages if s]

    def describe(self) -> str:
        """Resumen legible para logs."""
        lines = [
            "PipelineConfig:",
            f"  inputs            = {self.inputs}",
            f"  db_types          = {self.db_types}",
            f"  modes             = {self.modes}",
            f"  generation_stages = {self.generation_stages}",
            f"  error_stages      = {self.error_stages}",
            f"  error_types       = {self.error_types}",
            f"  benchmark_dir     = {self.benchmark_dir}",
            f"  retrieval_k       = {self.retrieval_k}",
            f"  output_dir        = {self.output_dir}",
        ]
        return "\n".join(lines)

# ================================================================
# Archivo: pipeline/flores_export.py
# ================================================================
# ai/pipeline/flores_export.py
"""
Exporta métricas tipo Flores et al. (Tables 11-16) en un JSON por corrida:
    flores_metrics_{ts}_{model}_{test_type}.json

Consolida:
  - structural metrics (table/col/type/pk/fk accuracy, precision/recall/f1)
  - retrieval metrics (MAP, MRR, P@K, R@K, Top-1)        [Table 11]
  - execution metrics (EX, FLEX)                         [Table 15]
  - NLG metrics (BERTScore, BLEU, ROUGE)                 [Table 16]
  - faithfulness (RAGAS-lite)                            [Table 16]
  - timings (por stage + total)                          [Table 18]
"""
# [dedup] import os
# [dedup] import json
# [dedup] import datetime
from typing import Any

# [dedup] from ai import env


def _flores_bundle_for_item(item: dict, structural: dict | None) -> dict:
    """
    Agrupa las métricas Flores del item, tolerando ausencias.
    Prioriza los datos del item sobre el argumento `structural`.
    """
    # Preferir el structural del item (cada modo tiene el suyo)
    if not structural:
        structural = item.get("structural_metrics")

    bundle = {
        "structural": structural or {},
        "retrieval": item.get("retrieval_metrics") or {},
        "execution": item.get("execution_metrics") or {},
        "nlg": item.get("nlg_metrics") or {},
        "faithfulness": item.get("faithfulness") or {},
        "timings": item.get("timings") or {},
    }

    # Filtrar solo si el .env explícitamente desactiva algo.
    # Por defecto (sin .env) se incluyen todas.
# [dedup]     import os
    filtered = {}
    for k, v in bundle.items():
        if k in ("structural", "timings"):
            filtered[k] = v
            continue
        key = f"AI_FLORES_{k.upper()}"
        flag = os.getenv(key, "1").strip().lower()
        if flag in ("1", "true", "yes"):
            filtered[k] = v

    return filtered

def export_flores_metrics(
    generation_items: list[dict],
    structural_metrics_by_run: dict[str, dict] | None = None,
    output_dir: str | None = None,
    run_id: str | None = None,
) -> str | None:
    """
    Genera un único JSON con todas las métricas Flores agregadas.

    Args:
      generation_items: lista de resultados de run_generation()
      structural_metrics_by_run: {run_id: metrics_dict} con las salidas de
                                 compute_structural_metrics (de main._persist_reports)
      output_dir: carpeta destino (default: PIPELINE_OUTPUT_DIR del .env)
      run_id: identificador de corrida (default: se deriva del primer item)

    Returns:
      path del archivo generado o None si está desactivado en .env.
    """
    if not env.flores_export_enabled():
        return None

    output_dir = output_dir or os.getenv(
        "PIPELINE_OUTPUT_DIR", "./tmp/pipeline_results"
    )
    os.makedirs(output_dir, exist_ok=True)

    if not generation_items:
        return None

    if run_id is None:
        run_id = generation_items[0].get("run_id") or datetime.datetime.now().strftime(
            "%Y%m%d_%H%M%S_unknown_mixed"
        )

    # Modelo y test_type del run_id (asumiendo formato {ts}_{model}_{type})
    parts = run_id.split("_")
    model = parts[2] if len(parts) > 2 else "unknown"

    # Estructura del JSON final
    payload = {
        "run_id": run_id,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "n_runs": len(generation_items),
        "runs": [],
    }

    for item in generation_items:
        structural = None
        if structural_metrics_by_run:
            structural = structural_metrics_by_run.get(item.get("run_id"))

        payload["runs"].append({
            "puml": item.get("puml"),
            "mode": item.get("mode"),
            "db_type": item.get("db_type"),
            "tables": item.get("tables"),
            "flores": _flores_bundle_for_item(item, structural),
        })

    # Añadir agregados por modo (media de métricas)
    payload["aggregates_by_mode"] = _aggregate_by_mode(payload["runs"])

    filename = f"flores_metrics_{run_id}.json"
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def _aggregate_by_mode(runs: list[dict]) -> dict[str, dict[str, Any]]:
    """Media simple por modo de las métricas numéricas."""
    from collections import defaultdict

    by_mode: dict[str, list[dict]] = defaultdict(list)
    for r in runs:
        by_mode[r["mode"]].append(r)

    out: dict[str, dict[str, Any]] = {}
    for mode, items in by_mode.items():
        numeric_keys: dict[str, list[float]] = defaultdict(list)

        def _walk(prefix, obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    _walk(f"{prefix}.{k}" if prefix else k, v)
            elif isinstance(obj, (int, float)):
                numeric_keys[prefix].append(float(obj))

        for it in items:
            _walk("", it["flores"])

        out[mode] = {
            k: round(sum(v) / len(v), 4)
            for k, v in numeric_keys.items()
            if v
        }
    return out

# ================================================================
# Archivo: pipeline/runner.py
# ================================================================
# ai/pipeline/runner.py
"""
Pipeline construido ENCIMA de main.execute.

Reglas de oro:
  * No modifica main.execute ni ai/services/*.
  * El stage "execute" solo invoca main.execute(folder, db_type, mode).
  * Los stages de error-detection usan parse_puml_schema + inject_errors + validate_schema.
  * Los imports de main son diferidos para evitar ciclos al arrancar Flask.
"""
# [dedup] import os
# [dedup] import json
import copy
import glob
# [dedup] import logging
import shutil
import tempfile
# [dedup] import datetime
from itertools import product
from typing import Dict, Callable
from contextlib import contextmanager
from pathlib import Path

# [dedup] from ai import env
from ai.services.retrieval import MODEL_NAME as LLM_MODEL_NAME
from ai.pipeline.timing import TimingCollector
# [dedup] from ai.services.puml_parser import parse_puml_schema
# [dedup] from ai.services.structural_validator import validate_schema
from ai.services.evaluation import inject_errors

from ai.evaluation.retrieval_metrics import compute_retrieval_metrics
from ai.evaluation.migration_metrics import compute_execution_metrics
from ai.evaluation.nlg_metrics import compute_nlg_metrics
from ai.evaluation.ragas_lite import compute_faithfulness

from .config import PipelineConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers de nombres / metadata
# ---------------------------------------------------------------------------
def _make_run_id(config, phase: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    model = LLM_MODEL_NAME or env.get_model_name() or "unknown"
    model = "".join(c if c.isalnum() or c in "-_." else "_" for c in model)
    if phase == "generation":
        test_type = "-".join(config.modes) if config.modes else "none"
    elif phase == "error_detection":
        test_type = "errors"
    else:
        test_type = phase
    return f"{ts}_{model}_{test_type}"


def _make_summary_filename(config, phase: str, run_id: str) -> str:
    prefix = "generation_summary" if phase == "generation" else "error_detection_summary"
    return os.path.join(config.output_dir, f"{prefix}_{run_id}.json")


def _add_run_metadata(item: dict, run_id: str, phase: str) -> dict:
    item["run_id"] = run_id
    parts = run_id.split("_")
    item["run_timestamp"] = f"{parts[0]}_{parts[1]}" if len(parts) >= 2 else run_id
    item["phase"] = phase
    item["model"] = LLM_MODEL_NAME or "unknown"
    return item


def _benchmark_base(ctx) -> str:
    original = ctx.get("input_path") or ctx["puml_file"]
    return os.path.splitext(os.path.basename(original))[0]


def _load_latest_metrics(puml_basename: str, db_type: str, mode: str):
    """Lee el metrics_*.json más reciente escrito por main._persist_reports."""
    tmp_dir = os.getenv("APP_OUTPUT_DIR", "./tmp")
    pattern = os.path.join(tmp_dir, f"metrics_*{puml_basename}_{db_type}_{mode}.json")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if not files:
        return None
    with open(files[0], "r", encoding="utf-8") as f:
        return json.load(f)


def _load_latest_complete_sql(puml_basename: str, db_type: str, mode: str):
    """Lee el complete_migrations_*.sql más reciente para este basename+db+mode."""
    tmp_dir = os.getenv("APP_OUTPUT_DIR", "./tmp")
    # Buscar primero con el sufijo del modo (si aplicaste el fix opcional)
    patterns = [
        os.path.join(tmp_dir, f"complete_migrations_*{puml_basename}_{db_type}_{mode}.sql"),
        os.path.join(tmp_dir, f"complete_migrations_*{puml_basename}_{db_type}.sql"),
    ]
    for pattern in patterns:
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        if files:
            with open(files[0], "r", encoding="utf-8") as f:
                return f.read(), files[0]
    return None, None


# ---------------------------------------------------------------------------
# Resolver de input a carpeta con modelo.puml
# ---------------------------------------------------------------------------
@contextmanager
def resolve_input_to_folder(input_path: str):
    p = Path(input_path).resolve()

    if p.is_dir() and (p / "modelo.puml").exists():
        yield str(p)
        return

    if p.is_dir():
        pumls = list(p.glob("*.puml")) + list(p.glob("*.plantuml"))
        if pumls:
            tmpdir = tempfile.mkdtemp(prefix="pipeline_puml_")
            shutil.copy(pumls[0], os.path.join(tmpdir, "modelo.puml"))
            try:
                yield tmpdir
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)
            return

    if p.is_file() and p.suffix.lower() in (".puml", ".plantuml", ".pu"):
        tmpdir = tempfile.mkdtemp(prefix="pipeline_puml_")
        shutil.copy(p, os.path.join(tmpdir, "modelo.puml"))
        try:
            yield tmpdir
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
        return

    raise FileNotFoundError(
        f"Entrada no reconocida: {input_path}. Debe ser una carpeta con "
        f"modelo.puml, una carpeta con algún .puml, o un archivo .puml."
    )


# ---------------------------------------------------------------------------
# Registro de stages
# ---------------------------------------------------------------------------
GENERATION_STAGES: Dict[str, Callable] = {}
ERROR_STAGES: Dict[str, Callable] = {}


def gen_stage(name: str):
    def deco(fn):
        GENERATION_STAGES[name] = fn
        return fn
    return deco


def err_stage(name: str):
    def deco(fn):
        ERROR_STAGES[name] = fn
        return fn
    return deco


def _save(path, payload):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    logger.info("Guardado: %s", path)


# ---------------------------------------------------------------------------
# STAGE: execute (delega en main.execute, luego carga SQL + métricas)
# ---------------------------------------------------------------------------
@gen_stage("execute")
def execute_stage(ctx, config):
    from ai.main import execute

    original = ctx.get("input_path") or ctx["puml_file"]
    basename = os.path.splitext(os.path.basename(original))[0]

    os.environ["AI_RUN_ID"] = ctx["run_id"]
    os.environ["AI_PUML_BASENAME"] = basename
    os.environ["AI_MODE"] = ctx["mode"]

    try:
        resp, ok = execute(ctx["folder"], ctx["db_type"], mode=ctx["mode"])
    finally:
        os.environ.pop("AI_RUN_ID", None)
        os.environ.pop("AI_PUML_BASENAME", None)
        os.environ.pop("AI_MODE", None)

    ctx["execute_ok"] = ok
    ctx["execute_tables"] = len(resp) if ok else 0

    # Cargar el SQL completo y el metrics_*.json recién escritos
    sql_text, sql_path = _load_latest_complete_sql(
        basename, ctx["db_type"], ctx["mode"]
    )
    if sql_text:
        ctx["migrations_text"] = sql_text
        logger.info("migrations_text cargado (%d chars) desde %s",
                    len(sql_text), sql_path)
    else:
        ctx["migrations_text"] = None
        logger.warning("No se encontró complete_migrations_*.sql para %s", basename)

    ctx["structural_metrics"] = _load_latest_metrics(
        basename, ctx["db_type"], ctx["mode"]
    )
    if ctx["structural_metrics"]:
        logger.info("structural_metrics cargado para mode=%s", ctx["mode"])


# ---------------------------------------------------------------------------
# STAGE: build_retriever (robusto contra ChromaDB vacío/corrupto)
# ---------------------------------------------------------------------------
@gen_stage("build_retriever")
def build_retriever_stage(ctx, config):
    if ctx["mode"] == "llm_only":
        ctx["retriever"] = None
        return

    from ai.services.retrieval import create_retriever
# [dedup]     from ai.services.vector_store import (
        check_existing_vector_db, create_vector_db,
        should_recreate_vector_db, clear_vector_db,
    )
# [dedup]     from ai.services.ingestion import ingest_puml, split_documents

    puml_file = ctx["puml_file"]

    try:
        vdb = check_existing_vector_db()
    except Exception as e:
        logger.warning("ChromaDB corrupta: %s. Recreando...", e)
        clear_vector_db()
        vdb = None

    if vdb is None or should_recreate_vector_db(puml_file, vdb):
        content = ingest_puml(puml_file)
        if not content:
            ctx["retriever"] = None
            return
        chunks = split_documents(content, puml_file)
        vdb = create_vector_db(chunks, puml_file)

    # 🔧 CAMBIO: garantizar al menos K=5 docs para calcular P@5/R@5/NDCG@5
    retriever_k = max(5, config.retrieval_k)
    ctx["retriever"] = create_retriever(
        vdb, source_file=puml_file, k=retriever_k
    )

# ---------------------------------------------------------------------------
# STAGES: métricas Flores
# ---------------------------------------------------------------------------
@gen_stage("retrieval_metrics")
def retrieval_metrics_stage(ctx, config):
    if ctx["mode"] == "llm_only":
        return
    if not config.benchmark_dir:
        return
    path = os.path.join(config.benchmark_dir,
                        f"{_benchmark_base(ctx)}_retrieval.json")
    if not os.path.exists(path):
        logger.warning("Sin benchmark de retrieval: %s", path)
        return
    with open(path, encoding="utf-8") as f:
        bench = json.load(f)
    retriever = ctx.get("retriever")
    if retriever is None:
        logger.warning("No hay retriever en ctx; se omite retrieval_metrics.")
        return
    try:
        ctx["retrieval_metrics"] = compute_retrieval_metrics(
            bench["queries"], retriever, k=config.retrieval_k
        )
    except Exception as e:
        logger.error("retrieval_metrics falló: %s", e)

@gen_stage("execution_metrics")
def execution_metrics_stage(ctx, config):
    if not config.benchmark_dir or not ctx.get("migrations_text"):
        return

    path = os.path.join(
        config.benchmark_dir,
        f"{_benchmark_base(ctx)}_gold.json"
    )
    if not os.path.exists(path):
        logger.warning("Sin benchmark de gold migrations: %s", path)
        return

    with open(path, encoding="utf-8") as f:
        bench = json.load(f)

    samples = [{
        "id": s.get("id"),
        "generated": ctx["migrations_text"],
        "gold": s["gold"],
    } for s in bench["samples"]]

    from ai.services.retrieval import create_flex_chain
    chain = create_flex_chain()

    try:
        ctx["execution_metrics"] = compute_execution_metrics(
            samples, ctx["db_type"], chain=chain
        )
    except Exception as e:
        logger.error("execution_metrics falló: %s", e)


@gen_stage("nlg_metrics")
def nlg_metrics_stage(ctx, config):
    if not config.benchmark_dir or not ctx.get("migrations_text"):
        return

    path = os.path.join(
        config.benchmark_dir,
        f"{_benchmark_base(ctx)}_gold.json"
    )
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as f:
        bench = json.load(f)

    golds = [s["gold"] for s in bench["samples"]]
    gens = [ctx["migrations_text"]] * len(golds)

    try:
        ctx["nlg_metrics"] = compute_nlg_metrics(gens, golds)
    except Exception as e:
        logger.error("nlg_metrics falló: %s", e)


@gen_stage("faithfulness")
def faithfulness_stage(ctx, config):
    if not ctx.get("migrations_text"):
        return

    try:
        ctx["faithfulness"] = compute_faithfulness(
            ctx["migrations_text"], ctx["puml_file"], ctx["db_type"]
        )
    except Exception as e:
        logger.error("faithfulness falló: %s", e)


# ---------------------------------------------------------------------------
# STAGES: detección de errores inyectados
# ---------------------------------------------------------------------------
DETECTION_RULES = {
    "drop_table":   lambda r: bool(r.missing_tables),
    "drop_column":  lambda r: bool(r.missing_columns),
    "change_type":  lambda r: bool(r.type_mismatches),
    "drop_pk":      lambda r: bool(r.pk_mismatches),
    "drop_fk":      lambda r: bool(r.fk_mismatches),
    "rename_table": lambda r: bool(r.missing_tables) and bool(r.extra_tables),
}


@err_stage("inject_and_validate")
def inject_and_validate(ctx, config):
    puml_file = ctx["puml_file"]
    try:
        expected = parse_puml_schema(puml_file)
    except Exception as e:
        logger.error("PUML parse error: %s", e)
        ctx["error_results"] = []
        return

    samples = []

    if config.include_clean_baseline:
        r = validate_schema(expected, copy.deepcopy(expected))
        samples.append({
            "error_type": "clean",
            "detected": not r.is_valid,
            "report_dict": r.to_dict(),
        })

    for etype in config.error_types:
        before = copy.deepcopy(expected)
        mutated = inject_errors(expected, [etype])

        if mutated == before:
            samples.append({
                "error_type": etype,
                "skipped": "no-op injection",
                "detected": False,
                "report_dict": None,
            })
            continue

        r = validate_schema(before, mutated)
        rule = DETECTION_RULES.get(etype)
        detected = bool(rule(r)) if rule else not r.is_valid

        samples.append({
            "error_type": etype,
            "detected": detected,
            "report_dict": r.to_dict(),
        })

    ctx["error_results"] = samples


@err_stage("measure_detection")
def measure_detection(ctx, config):
    samples = ctx.get("error_results", [])
    per_type = {}

    for s in samples:
        etype = s["error_type"]
        per_type.setdefault(etype, {"TP": 0, "FN": 0, "FP": 0, "skipped": 0})
        if s.get("skipped"):
            per_type[etype]["skipped"] += 1
            continue
        if etype == "clean":
            if s["detected"]:
                per_type[etype]["FP"] += 1
            continue
        per_type[etype]["TP" if s["detected"] else "FN"] += 1

    tp = sum(v["TP"] for k, v in per_type.items() if k != "clean")
    fn = sum(v["FN"] for k, v in per_type.items() if k != "clean")
    fp = per_type.get("clean", {}).get("FP", 0)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)

    ctx["detection_metrics"] = {
        "per_error_type": per_type,
        "aggregate": {
            "TP": tp, "FN": fn, "FP": fp,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        },
        "samples": samples,
    }


# ---------------------------------------------------------------------------
# Runners
# ---------------------------------------------------------------------------
def run_generation(config: PipelineConfig, write_summary: bool = True):
    run_id = _make_run_id(config, "generation")
    results = []

    for input_path, db_type, mode in product(
        config.inputs, config.db_types, config.modes
    ):
        try:
            with resolve_input_to_folder(input_path) as folder:
                puml_file = os.path.join(folder, "modelo.puml")
                ctx = {
                    "run_id": run_id,
                    "input_path": input_path,
                    "folder": folder,
                    "puml_file": puml_file,
                    "db_type": db_type,
                    "mode": mode,
                    "timings": TimingCollector(),
                }

                for name in config.generation_stages:
                    fn = GENERATION_STAGES.get(name)
                    if fn is None:
                        logger.warning("Stage desconocido: %s", name)
                        continue
                    logger.info("[gen] %s (%s / %s)", name, mode, db_type)
                    with ctx["timings"].time(name):
                        try:
                            fn(ctx, config)
                        except Exception as e:
                            logger.error("Stage '%s' falló: %s", name, e)
                            break

                item = {
                    "input": input_path,
                    "puml": os.path.basename(puml_file),
                    "db_type": db_type,
                    "mode": mode,
                    "success": ctx.get("execute_ok"),
                    "tables": ctx.get("execute_tables"),
                    "timings": ctx["timings"].summary(),
                    # --- Métricas Flores (todas) ---
                    "structural_metrics": ctx.get("structural_metrics"),
                    "retrieval_metrics": ctx.get("retrieval_metrics"),
                    "execution_metrics": ctx.get("execution_metrics"),
                    "nlg_metrics": ctx.get("nlg_metrics"),
                    "faithfulness": ctx.get("faithfulness"),
                    "migrations_text_len": len(ctx.get("migrations_text") or ""),
                }
                results.append(_add_run_metadata(item, run_id, "generation"))
        except FileNotFoundError as e:
            logger.warning("%s", e)
            continue

    summary_path = None
    if write_summary:
        summary_path = _make_summary_filename(config, "generation", run_id)
        _save(summary_path, results)
        logger.info("Summary guardado: %s", summary_path)

    return {"run_id": run_id, "results": results, "summary_path": summary_path}


def run_error_detection(config: PipelineConfig, write_summary: bool = True):
    run_id = _make_run_id(config, "error_detection")
    results = []

    for input_path, db_type in product(config.inputs, config.db_types):
        try:
            with resolve_input_to_folder(input_path) as folder:
                puml_file = os.path.join(folder, "modelo.puml")
                ctx = {
                    "input_path": input_path,
                    "folder": folder,
                    "puml_file": puml_file,
                    "db_type": db_type,
                    "timings": TimingCollector(),
                }

                for name in config.error_stages:
                    fn = ERROR_STAGES.get(name)
                    if fn is None:
                        logger.warning("Stage desconocido: %s", name)
                        continue
                    logger.info("[err] %s", name)
                    with ctx["timings"].time(name):
                        fn(ctx, config)

                item = {
                    "input": input_path,
                    "puml": os.path.basename(puml_file),
                    "db_type": db_type,
                    "detection_metrics": ctx.get("detection_metrics"),
                    "timings": ctx["timings"].summary(),
                }
                results.append(_add_run_metadata(item, run_id, "error_detection"))
        except FileNotFoundError as e:
            logger.warning("%s", e)
            continue

    summary_path = None
    if write_summary:
        summary_path = _make_summary_filename(config, "error_detection", run_id)
        _save(summary_path, results)
        logger.info("Summary guardado: %s", summary_path)

    return {"run_id": run_id, "results": results, "summary_path": summary_path}


# ---------------------------------------------------------------------------
# API pública de alto nivel
# ---------------------------------------------------------------------------
def run_from_config(config_path: str) -> None:
    cfg = PipelineConfig.from_json(config_path)
    logger.info("Config cargada: %s", config_path)

    print("=== Fase 1: generación (delegada a main.execute) ===")
    gen = run_generation(cfg)
    print(f"  run_id: {gen['run_id']}")
    print(f"  summary: {gen['summary_path']}")

    # Export métricas Flores
    from ai.pipeline.flores_export import export_flores_metrics

    # Construir structural_metrics_by_run por (run_id, mode)
    structural_by_run = {}
    for item in gen["results"]:
        if item.get("structural_metrics"):
            key = f"{item['run_id']}__{item['mode']}"
            structural_by_run[key] = item["structural_metrics"]

    flores_path = export_flores_metrics(
        generation_items=gen["results"],
        structural_metrics_by_run=structural_by_run,
        output_dir=cfg.output_dir,
        run_id=gen["run_id"],
    )
    if flores_path:
        print(f"  flores: {flores_path}")
    else:
        print("  flores: (no generado — revisa AI_FLORES_EXPORT en .env)")

    print("=== Fase 2: detección de errores inyectados ===")
    err = run_error_detection(cfg)
    print(f"  run_id: {err['run_id']}")
    print(f"  summary: {err['summary_path']}")

# ================================================================
# Archivo: pipeline/tests_api.py
# ================================================================
# ai/pipeline/test_api.py
"""
API pública para los tests del Reviewer 1.

Función independiente: run_structural_validation_tests(...)
Pero por dentro usa el mismo PipelineConfig + PipelineRunner.
"""
# [dedup] import os
from typing import Optional, Sequence

# [dedup] from .config import PipelineConfig
from .runner import run_error_detection


def run_structural_validation_tests(
    folder_path: str,
    db_type: str = "sqlite",
    error_types=None,
    include_clean_baseline: bool = True,
    output_dir: str = "./tmp/pipeline_results",
    write_summary: bool = True,
) -> dict:
    cfg = PipelineConfig(
        inputs=[folder_path],
        db_types=[db_type],
        generation_stages=[],
        error_stages=["inject_and_validate", "measure_detection"],
        include_clean_baseline=include_clean_baseline,
        output_dir=output_dir,
    )
    if error_types:
        cfg.error_types = list(error_types)

    puml_file = os.path.join(folder_path, "modelo.puml")
    if not os.path.exists(puml_file):
        raise FileNotFoundError(f"PUML no encontrado: {puml_file}")

    result = run_error_detection(cfg, write_summary=write_summary)
    results_list = result["results"]
    if not results_list:
        raise RuntimeError(f"No se generaron resultados para {puml_file}")

    payload = results_list[0]
    metrics = payload.get("detection_metrics") or {}

    return {
        "run_id": result["run_id"],
        "input": payload["input"],
        "puml": payload["puml"],
        "db_type": payload["db_type"],
        "per_error_type": metrics.get("per_error_type", {}),
        "aggregate": metrics.get("aggregate", {}),
        "samples": metrics.get("samples", []),
        "timings": payload.get("timings", {}),
        "summary_path": result["summary_path"],
    }

# ================================================================
# Archivo: pipeline/timing.py
# ================================================================
# ai/pipeline/timing.py
# [dedup] import time
import statistics
# [dedup] from contextlib import contextmanager
from typing import Dict, Any


class TimingCollector:
    def __init__(self):
        self.records: Dict[str, list[float]] = {}
        self._t0 = time.perf_counter()

    @contextmanager
    def time(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.records.setdefault(name, []).append(elapsed)

    def total_seconds(self) -> float:
        return time.perf_counter() - self._t0

    def summary(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for name, samples in self.records.items():
            out[name] = _stats(samples)
        out["__total__"] = {"seconds": round(self.total_seconds(), 3)}
        return out


def _stats(samples: list[float]) -> Dict[str, float]:
    if not samples:
        return {}
    n = len(samples)
    mean = statistics.fmean(samples)
    out = {
        "seconds_mean": round(mean, 3),
        "seconds_total": round(sum(samples), 3),
        "n_runs": n,
    }
    if n >= 2:
        out["seconds_std"] = round(statistics.pstdev(samples), 3)
        k = max(0, int(round(0.95 * (n - 1))))
        out["seconds_p95"] = round(sorted(samples)[k], 3)
    return out

# ================================================================
# Archivo: prompts/templates.py
# ================================================================
# ai/prompts/templates.py
from langchain.prompts import PromptTemplate, ChatPromptTemplate

# Plantilla para generar variaciones de preguntas (MultiQueryRetriever)
QUERY_PROMPT = PromptTemplate(
  input_variables=["question"],
  template="""Eres un asistente especializado en diagramas UML y bases de datos. 
  Genera 3 versiones diferentes de la siguiente pregunta para mejorar la búsqueda de información relevante.
  
  Pregunta original: {question}
  
  Genera 3 variaciones diferentes:"""
)

# Plantilla principal para la cadena RAG (generación de SQL)
CHAIN_TEMPLATE = """Eres un experto en bases de datos y diagramas UML. 
Tu tarea es ANALIZAR el diagrama PUML proporcionado y GENERAR código SQL.

CONTEXTO del diagrama PUML:
{context}

INSTRUCCIONES para la pregunta: {question}

- Analiza las entidades (entity) y sus relaciones del diagrama
- Genera código SQL funcional y válido
- Especifica el tipo de base de datos objetivo
- Incluye todas las tablas, relaciones y constraints necesarios
- SÉ ESPECÍFICO y PRÁCTICO"""

CHAIN_PROMPT = ChatPromptTemplate.from_template(template=CHAIN_TEMPLATE)

# ================================================================
# Archivo: services/evaluation.py
# ================================================================
# ai/services/evaluation.py
# [dedup] import logging
from ai.services.structural_validator import ValidationReport

logger = logging.getLogger(__name__)


def _safe_div(num: int, den: int) -> float:
  return round(num / den, 4) if den else 0.0


def compute_structural_metrics(report: ValidationReport) -> dict:
  """
  Calcula métricas desglosadas a partir de un ValidationReport.
  Cubre la observación del Reviewer 1 (no basta Table Accuracy).
  """
  s = report.stats

  table_acc = _safe_div(s.get('matched_tables', 0), s.get('expected_tables', 0))
  col_acc = _safe_div(s.get('matched_columns', 0), s.get('expected_columns', 0))
  type_acc = _safe_div(s.get('matched_types', 0), s.get('expected_types', 0))
  pk_acc = _safe_div(s.get('matched_pks', 0), s.get('expected_pks', 0))
  fk_acc = _safe_div(s.get('matched_fks', 0), s.get('expected_fks', 0)) \
         if s.get('expected_fks', 0) else None

  # Full-schema: sólo correcto si las 5 anteriores son 1.0
  full_schema = 1.0 if all([
    table_acc == 1.0,
    col_acc == 1.0,
    type_acc == 1.0,
    pk_acc == 1.0,
    fk_acc == 1.0
  ]) else 0.0

  # Precision/Recall a nivel de "unidad estructural"
  # Tomamos como unidades: columnas + tipos + FKs esperadas
  expected_units = (
    s.get('expected_columns', 0)
    + s.get('expected_types', 0)
    + s.get('expected_fks', 0)
  )
  matched_units = (
    s.get('matched_columns', 0)
    + s.get('matched_types', 0)
    + s.get('matched_fks', 0)
  )

  # Unidades generadas = mismas que esperadas + extras detectadas
  extra_cols = sum(len(v) for v in report.extra_columns.values())
  extra_fks = sum(
    len([d for d in diff['diffs'] if 'extra' in d])
    for diff in report.fk_mismatches
  )
  generated_units = matched_units + extra_cols + extra_fks

  precision = _safe_div(matched_units, generated_units)
  recall = _safe_div(matched_units, expected_units)
  f1 = (
    round(2 * precision * recall / (precision + recall), 4)
    if (precision + recall) > 0 else 0.0
  )

  return {
    'table_accuracy': table_acc,
    'column_accuracy': col_acc,
    'data_type_accuracy': type_acc,
    'primary_key_accuracy': pk_acc,
    'foreign_key_accuracy': fk_acc,
    'full_schema_accuracy': full_schema,
    'precision': precision,
    'recall': recall,
    'f1': f1,
    'counts': {
      'expected_tables': s.get('expected_tables', 0),
      'generated_tables': s.get('generated_tables', 0),
      'missing_tables': len(report.missing_tables),
      'extra_tables': len(report.extra_tables),
      'missing_columns': sum(len(v) for v in report.missing_columns.values()),
      'extra_columns': extra_cols,
      'type_mismatches': sum(len(v) for v in report.type_mismatches.values()),
      'pk_mismatches': len(report.pk_mismatches),
      'fk_mismatches': sum(len(v['diffs']) for v in report.fk_mismatches),
    }
  }


def inject_errors(schema, error_types: list[str]):
  """
  Devuelve una copia del SchemaModel con errores inyectados.
  Útil para medir falsos negativos del validador (Reviewer 1).
  """
# [dedup]   import copy
  mutated = copy.deepcopy(schema)

  for etype in error_types:
    if etype == 'drop_table' and mutated.tables:
      mutated.tables.pop(next(iter(mutated.tables)))
    elif etype == 'drop_column':
      for t in mutated.tables.values():
        if len(t.columns) > 1:
          t.columns.pop(next(k for k in t.columns if not t.columns[k].is_pk))
          break
    elif etype == 'change_type':
      for t in mutated.tables.values():
        for c in t.columns.values():
          c.type = 'blob'
          break
        break
    elif etype == 'drop_pk':
      for t in mutated.tables.values():
        for c in t.columns.values():
          c.is_pk = False
        break
    elif etype == 'drop_fk':
      for t in mutated.tables.values():
        if t.foreign_keys:
          t.foreign_keys.pop()
          break
    elif etype == 'rename_table' and mutated.tables:
      old = next(iter(mutated.tables))
      table = mutated.tables.pop(old)
      table.name = table.name + '_x'
      mutated.tables[table.name.lower()] = table

  return mutated

# ================================================================
# Archivo: services/fallback.py
# ================================================================
# ai/services/fallback.py
# [dedup] import re
# [dedup] import logging

logger = logging.getLogger(__name__)


def map_puml_to_sql(puml_type: str, db_type: str) -> str:
  """Mapea tipos PUML a tipos SQL según la base de datos."""
  puml_type = puml_type.lower().strip()
  type_mappings = {
    'sqlite': {
      'string': 'TEXT', 'int': 'INTEGER', 'integer': 'INTEGER',
      'boolean': 'INTEGER', 'date': 'TEXT', 'datetime': 'TEXT',
      'float': 'REAL', 'double': 'REAL', 'text': 'TEXT'
    },
    'mysql': {
      'string': 'VARCHAR(255)', 'int': 'INT', 'integer': 'INT',
      'boolean': 'BOOLEAN', 'date': 'DATE', 'datetime': 'DATETIME',
      'float': 'FLOAT', 'double': 'DOUBLE', 'text': 'TEXT'
    },
    'postgres': {
      'string': 'VARCHAR(255)', 'int': 'INTEGER', 'integer': 'INTEGER',
      'boolean': 'BOOLEAN', 'date': 'DATE', 'datetime': 'TIMESTAMP',
      'float': 'REAL', 'double': 'DOUBLE PRECISION', 'text': 'TEXT'
    }
  }
  return type_mappings.get(db_type, {}).get(puml_type, 'TEXT')


def generate_direct_migrations(puml_file: str, db_type: str) -> str:
  """Genera migraciones directamente desde el PUML (fallback)."""
  logger.info("Using direct migration generation as fallback...")
  try:
    with open(puml_file, 'r', encoding='utf-8') as f:
      content = f.read()

    entity_pattern = r'entity\s+(\w+)\s*\{([^}]+)\}'
    entities = re.findall(entity_pattern, content, re.IGNORECASE | re.DOTALL)
    migrations = []

    for entity_name, entity_content in entities:
      attr_pattern = r'\s*(\w+)\s*:\s*([^\n]+)'
      attributes = re.findall(attr_pattern, entity_content)

      create_lines = [f"CREATE TABLE {entity_name} ("]
      create_lines.append("  id SERIAL PRIMARY KEY," if db_type == 'postgres' else "  id INTEGER PRIMARY KEY AUTOINCREMENT,")

      for attr_name, attr_type in attributes:
        sql_type = map_puml_to_sql(attr_type, db_type)
        create_lines.append(f"  {attr_name} {sql_type},")

      create_lines[-1] = create_lines[-1].rstrip(',')
      create_lines.append(");")
      create_stmt = "\n".join(create_lines)
      drop_stmt = f"DROP TABLE IF EXISTS {entity_name};"
      migration_block = f"-- migrate:up\n\n{create_stmt}\n\n-- migrate:down\n\n{drop_stmt}\n"
      migrations.append(migration_block)

    return "\n".join(migrations)
  except Exception as e:
    logger.error(f"Error in direct migration generation: {e}")
    return ""

# ================================================================
# Archivo: services/ingestion.py
# ================================================================
# ai/services/ingestion.py
# [dedup] import os
# [dedup] import re
import hashlib
# [dedup] import logging
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def ingest_puml(puml_path: str) -> str | None:
  """Lee el contenido del archivo PUML."""
  if os.path.exists(puml_path):
    with open(puml_path, 'r', encoding='utf-8') as f:
      content = f.read()
    logger.info("PUML file loaded successfully.")
    return content
  logger.error("PUML file not found at path: %s", puml_path)
  return None


def split_documents(content: str, puml_path: str):
  """
  Divide el contenido PUML en fragmentos semánticos.
  Usa SHA-256 (determinista) para que el hash coincida con vector_store.
  """
  file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
  chunks = []

  # 1. Entidades
  entity_pattern = r'(entity\s+"?[A-Za-z_]\w*"?\s*(?:as\s+\w+)?\s*\{[^}]+\})'
  entities = re.findall(entity_pattern, content, re.IGNORECASE | re.DOTALL)
  if entities:
    logger.info("Found %d entities.", len(entities))
    for entity in entities:
      chunks.append(Document(
        page_content=entity,
        metadata={
          "source": "puml_file",
          "chunk_id": len(chunks),
          "chunk_type": "entity",
          "source_file": os.path.abspath(puml_path),
          "source_file_hash": file_hash
        }
      ))

  # 2. Relaciones
  relationship_pattern = r'(\w+\s+--\s+\w+|"\w+"\s+--\s+"\w+")'
  relationships = re.findall(relationship_pattern, content)
  if relationships:
    logger.info("Found %d relationships.", len(relationships))
    relationship_chunk = "Relationships:\n" + "\n".join(relationships)
    chunks.append(Document(
      page_content=relationship_chunk,
      metadata={
        "source": "puml_file",
        "chunk_id": len(chunks),
        "chunk_type": "relationships",
        "source_file": os.path.abspath(puml_path),
        "source_file_hash": file_hash
      }
    ))

  # 3. Fallback: dividir por líneas
  if not chunks:
    logger.info("Using line-based chunking as fallback.")
    lines = content.splitlines()
    chunk_size = 15
    for i in range(0, len(lines), chunk_size):
      chunk_text = "\n".join(lines[i:i + chunk_size])
      chunks.append(Document(
        page_content=chunk_text,
        metadata={
          "source": "puml_file",
          "chunk_id": len(chunks),
          "chunk_type": "line_chunk",
          "source_file": os.path.abspath(puml_path),
          "source_file_hash": file_hash
        }
      ))

  logger.info("PUML content split into %d chunks.", len(chunks))
  return chunks

# ================================================================
# Archivo: services/migration_generator.py
# ================================================================
# ai/services/migration_generator.py
# [dedup] import os
# [dedup] import re
# [dedup] import json
# [dedup] import shutil
# [dedup] import logging
# [dedup] import datetime
from typing import Dict, List, Tuple
from ..models.migration import TableMigration
from .fallback import generate_direct_migrations
from ai.paths import under_output

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Helper: extrae relaciones explícitas del PUML (🔧 FIX 2)
# --------------------------------------------------------------------------- #
def _extract_relationships_summary(puml_content: str) -> str:
    """
    Devuelve un bloque legible con las relaciones del PUML.
    Cada línea incluye el nombre de la columna FK entre paréntesis para que
    el LLM sepa exactamente qué columna usar.

    Formato de salida:
        - customers -- orders (FK column: customer_id)
        - employees -- employees (FK column: reports_to_id)
    """
    rel_pattern = re.compile(
        r'([A-Za-z_]\w*)\s+(["\|o\{\}]+)\s*--\s*(["\|o\{\}]+)\s+([A-Za-z_]\w*)'
        r'(?:\s*:\s*([^\n]+))?',
        re.IGNORECASE,
    )
    lines = []
    for m in rel_pattern.finditer(puml_content):
        left, lcard, rcard, right = m.group(1), m.group(2), m.group(3), m.group(4)
        label = (m.group(5) or "").strip().strip('"').strip("'")

        # Identificar el lado "muchos" (el que tiene `{`)
        many_side = None
        if '{' in rcard:
            many_side = right
        elif '{' in lcard:
            many_side = left

        suffix = f" (FK column: {label})" if label else ""
        arrow = f" --[many: {many_side}]--> " if many_side else " -- "
        lines.append(f"- {left}{arrow}{right}{suffix}")

    return "\n".join(lines) if lines else "(no relationships declared)"


# --------------------------------------------------------------------------- #
# Helper: extrae la lista de entidades (para el prompt)
# --------------------------------------------------------------------------- #
def _extract_entities_summary(puml_content: str) -> str:
    entity_pattern = r'entity\s+(\w+)\s*\{([^}]+)\}'
    entities = re.findall(entity_pattern, puml_content, re.IGNORECASE | re.DOTALL)
    lines = []
    for entity_name, entity_content in entities:
        attributes = re.findall(r'\s*\*?\s*(\w+)\s*:\s*([^\n]+)', entity_content)
        lines.append(f"Entidad: {entity_name}, Atributos: {attributes}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Prompt builder (compartido por RAG y direct) (🔧 FIX 2)
# --------------------------------------------------------------------------- #
def _build_prompt(puml_file: str, db_type: str,
                  entities_summary: str,
                  relationships_summary: str,
                  extra_instructions: str = "") -> str:
    query = f"""
ANÁLISIS DE DIAGRAMA UML Y GENERACIÓN DE MIGRACIONES SQL

ARCHIVO: {puml_file}
TIPO DE BASE DE DATOS: {db_type.upper()}

ENTIDADES ENCONTRADAS EN EL DIAGRAMA:
{entities_summary}

RELACIONES EXPLÍCITAS DEL DIAGRAMA:
{relationships_summary}

REGLAS CRÍTICAS PARA FOREIGN KEYS:
1. Por CADA relación de la lista anterior, añade una FOREIGN KEY en la tabla
   del lado "muchos" (la que aparece después de "--[many: X]-->").
2. La columna FK es el texto entre paréntesis `(FK column: X)`.
3. Si la columna FK NO existe en la tabla, créala con ese nombre exacto.
4. Si la relación es self-reference (misma tabla), apunta a `id` de la misma tabla.
5. Usa el nombre de columna indicado; NO inventes uno distinto.

INSTRUCCIONES ESPECÍFICAS:

1. ANALIZA cada entidad del diagrama UML y conviértela en una sentencia CREATE TABLE
2. USA el formato EXACTO de migración que se muestra a continuación
3. PRESERVA los nombres ORIGINALES de las entidades y atributos
4. GENERA código SQL VÁLIDO para {db_type.upper()}

FORMATO REQUERIDO para CADA tabla:

-- migrate:up

CREATE TABLE nombre_tabla (
  id INTEGER PRIMARY KEY,
  columna1 TIPO_DATO,
  columna2 TIPO_DATO,
  FOREIGN KEY (columna_fk) REFERENCES tabla_padre(id)
);

-- migrate:down

DROP TABLE IF EXISTS nombre_tabla;

REQUISITOS TÉCNICOS:
- Para {db_type.upper()}, usa tipos de datos apropiados
- Cada tabla tiene `id INTEGER PRIMARY KEY` como clave primaria
- Incluye TODAS las FOREIGN KEYS deducidas de las relaciones listadas
- Mantén los nombres ORIGINALES en inglés (NO traduzcas)
- Genera EXACTAMENTE una migración por cada entidad encontrada

RESPONDE ÚNICAMENTE con las sentencias SQL en el formato especificado, sin explicaciones.
"""

    if extra_instructions:
        query += (
            f"\n\nERRORES DETECTADOS EN LA ITERACIÓN ANTERIOR:\n"
            f"{extra_instructions}\n\n"
            f"Corrige TODOS los errores listados y devuelve el SQL COMPLETO "
            f"corregido (todas las tablas, no solo las modificadas). No omitas "
            f"tablas que ya estaban correctas: la respuesta debe ser el script "
            f"completo y válido. Asegúrate de incluir TODAS las FOREIGN KEYS "
            f"declaradas en las relaciones del diagrama."
        )

    return query


# --------------------------------------------------------------------------- #
# Generación con RAG (🔧 FIX 2: pasa relaciones al prompt)
# --------------------------------------------------------------------------- #
def generate_sql_migrations_with_rag(chain, db_type: str, puml_file: str,
                                     extra_instructions: str = "") -> str:
    """
    Genera migraciones usando la cadena RAG.

    Args:
      chain: cadena RAG (retriever | prompt | llm | parser).
      db_type: 'sqlite' | 'mysql' | 'postgres'.
      puml_file: ruta al archivo .puml.
      extra_instructions: feedback de errores de la iteración anterior
        (usado por el bucle de corrección de rag_validation en ai/main.py).
    """
    with open(puml_file, 'r', encoding='utf-8') as f:
        puml_content = f.read()

    entities_summary = _extract_entities_summary(puml_content)
    relationships_summary = _extract_relationships_summary(puml_content)

    query = _build_prompt(
        puml_file=puml_file,
        db_type=db_type,
        entities_summary=entities_summary,
        relationships_summary=relationships_summary,
        extra_instructions=extra_instructions,
    )

    logger.info("Generating SQL migrations (RAG)...")
    try:
        response = chain.invoke(query)
        return response
    except Exception as e:
        logger.error(f"Error generating migrations: {e}")
        return f"Error: {e}"


# --------------------------------------------------------------------------- #
# Generación directa, sin RAG (🔧 FIX 2: también pasa relaciones)
# --------------------------------------------------------------------------- #
def generate_sql_migrations_direct(chain, db_type: str, puml_file: str) -> str:
    """
    Igual que generate_sql_migrations_with_rag pero sin retriever.
    Se usa en el modo llm_only para la comparación pedida por el Reviewer 1.
    """
    with open(puml_file, 'r', encoding='utf-8') as f:
        puml_content = f.read()

    entities_summary = _extract_entities_summary(puml_content)
    relationships_summary = _extract_relationships_summary(puml_content)

    query = _build_prompt(
        puml_file=puml_file,
        db_type=db_type,
        entities_summary=entities_summary,
        relationships_summary=relationships_summary,
    )

    logger.info("Generating SQL migrations (direct, no RAG)...")
    try:
        response = chain.invoke({"context": "(sin contexto RAG)", "question": query})
        return response
    except Exception as e:
        logger.error(f"Error generating migrations (direct): {e}")
        return f"Error: {e}"


# --------------------------------------------------------------------------- #
# Parseo y organización (sin cambios)
# --------------------------------------------------------------------------- #
def extract_table_name(sql_statement: str) -> str | None:
    """Extrae el nombre de la tabla de una sentencia SQL."""
    patterns = [
        r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?`?([^\s`(;]+)`?',
        r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?([^\s(;]+)',
        r'DROP TABLE\s+(?:IF EXISTS\s+)?`?([^\s`;]+)`?',
    ]
    for pattern in patterns:
        match = re.search(pattern, sql_statement, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def parse_migration_blocks(complete_migrations: str) -> Dict[int, TableMigration]:
    """Parsea el texto de migraciones en un diccionario de TableMigration."""
    if complete_migrations.startswith("Error:") or "No puedo cumplir" in complete_migrations:
        logger.error(f"Model refused to generate migrations: {complete_migrations}")
        return {}

    patterns = [
        r'--\s*migrate:up\s*(CREATE TABLE[^;]+;)\s*--\s*migrate:down\s*(DROP TABLE[^;]+;)',
        r'(CREATE TABLE[^;]+;)',
    ]

    tables = {}
    seen_tables = set()

    for pattern in patterns:
        matches = re.findall(pattern, complete_migrations, re.IGNORECASE | re.DOTALL)
        if matches:
            logger.info(f"Found {len(matches)} matches using pattern")
            for i, match in enumerate(matches, len(tables) + 1):
                if isinstance(match, tuple):
                    create_stmt, drop_stmt = match
                else:
                    create_stmt = match
                    table_name = extract_table_name(create_stmt)
                    drop_stmt = (
                        f"DROP TABLE IF EXISTS {table_name};"
                        if table_name else "DROP TABLE unknown_table;"
                    )

                table_name = extract_table_name(create_stmt)
                if table_name and table_name in seen_tables:
                    logger.info(f"Skipping duplicate table: {table_name}")
                    continue
                seen_tables.add(table_name)

                clean_create = re.sub(r'\s+', ' ', create_stmt.strip())
                clean_drop = re.sub(r'\s+', ' ', drop_stmt.strip())
                complete_block = (
                    f"-- migrate:up\n\n{create_stmt.strip()}\n\n"
                    f"-- migrate:down\n\n{drop_stmt.strip()}"
                )

                tables[i] = TableMigration(
                    table_name=table_name,
                    up=clean_create,
                    down=clean_drop,
                    complete_block=complete_block,
                    index=i,
                )
    logger.info(f"Se encontraron {len(tables)} tablas únicas.")
    return tables


def validate_entity_count(puml_file: str,
                          tables_dict: Dict[int, TableMigration]) -> Tuple[int, int]:
    """Valida que el número de entidades coincida con el de tablas generadas."""
    try:
        with open(puml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        entity_pattern = r'entity\s+(\w+)'
        entities = re.findall(entity_pattern, content, re.IGNORECASE)
        expected = len(entities)
        actual = len(tables_dict)
        logger.info(f"Expected entities: {expected}, Generated tables: {actual}")
        if expected != actual:
            print(f"⚠️  ADVERTENCIA: Se esperaban {expected} tablas pero se generaron {actual}")
            generated = [t.table_name for t in tables_dict.values() if t.table_name]
            missing = set(entities) - set(generated)
            if missing:
                print(f"📋 Entidades faltantes: {', '.join(missing)}")
            if generated:
                print(f"📋 Tablas generadas: {', '.join(generated)}")
        return expected, actual
    except Exception as e:
        logger.error(f"Error validating entity count: {e}")
        return 0, len(tables_dict)


def enforce_original_names(puml_file: str,
                           tables_dict: Dict[int, TableMigration]) -> Dict[int, TableMigration]:
    """Corrige los nombres de tabla para que coincidan exactamente con las entidades del PUML."""
    try:
        with open(puml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        entity_pattern = r'entity\s+(\w+)'
        original_entities = re.findall(entity_pattern, content, re.IGNORECASE)

        corrected = {}
        for key, table in tables_dict.items():
            current = table.table_name
            matching = None
            for entity in original_entities:
                if entity.lower() == current.lower():
                    matching = entity
                    break
            if matching and matching != current:
                corrected_up = re.sub(
                    f'TABLE\\s+{re.escape(current)}',
                    f'TABLE {matching}',
                    table.up,
                    flags=re.IGNORECASE,
                )
                corrected_down = re.sub(
                    f'TABLE\\s+{re.escape(current)}',
                    f'TABLE {matching}',
                    table.down,
                    flags=re.IGNORECASE,
                )
                corrected_block = re.sub(
                    f'TABLE\\s+{re.escape(current)}',
                    f'TABLE {matching}',
                    table.complete_block,
                    flags=re.IGNORECASE,
                )
                corrected[key] = TableMigration(
                    table_name=matching,
                    up=corrected_up,
                    down=corrected_down,
                    complete_block=corrected_block,
                    index=table.index,
                )
                print(f"✓ Corregido: '{current}' -> '{matching}'")
            else:
                corrected[key] = table
        return corrected
    except Exception as e:
        logger.error(f"Error enforcing original names: {e}")
        return tables_dict


def save_migration_files(tables_dict, puml_basename, db_type, complete_migrations):
    """Guarda las migraciones en tmp/ (archivo completo + carpeta por tabla)."""
    if not tables_dict:
        print("❌ No hay migraciones para guardar.")
        return

    run_id = os.getenv("AI_RUN_ID")
    if run_id:
        complete_filename = under_output(
            f"complete_migrations_{run_id}_{puml_basename}_{db_type}.sql"
        )
        migrations_dir = under_output(
            f"migrations_{run_id}_{puml_basename}_{db_type}"
        )
        base_ts = run_id
    else:
        complete_filename = under_output(
            f"complete_migrations_{puml_basename}_{db_type}.sql"
        )
        migrations_dir = under_output(
            f"migrations_{puml_basename}_{db_type}"
        )
        base_ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    with open(complete_filename, 'w', encoding='utf-8') as f:
        f.write(f"-- Migraciones generadas desde: {puml_basename}.puml\n")
        f.write(f"-- Tipo de base de datos: {db_type}\n")
        if run_id:
            f.write(f"-- Run ID: {run_id}\n")
        f.write(f"-- Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Total de tablas: {len(tables_dict)}\n\n")
        f.write(complete_migrations)
    print(f"✓ Migraciones completas guardadas en: {complete_filename}")

    if os.path.exists(migrations_dir):
        shutil.rmtree(migrations_dir)
    os.makedirs(migrations_dir, exist_ok=True)

    for key, table in tables_dict.items():
        if run_id:
            ts = f"{base_ts}_{key:02d}"
        else:
            ts = str(int(base_ts) + key)
        filename = os.path.join(migrations_dir, f"{ts}_create_{table.table_name}.sql")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(table.complete_block)
        print(f"✓ Migración {key} ({table.table_name}) guardada en: {filename}")

# ================================================================
# Archivo: services/puml_parser.py
# ================================================================
# ai/services/puml_parser.py
# [dedup] import os
# [dedup] import re
# [dedup] import logging
from ai.models.schema import (
  ColumnSchema,
  ForeignKeySchema,
  TableSchema,
  SchemaModel
)

logger = logging.getLogger(__name__)


# Tipos PUML aceptados -> etiqueta normalizada interna
PUML_TYPE_ALIASES = {
  'string': 'string',
  'varchar': 'string',
  'text': 'string',
  'int': 'int',
  'integer': 'int',
  'long': 'int',
  'bigint': 'int',
  'smallint': 'int',
  'tinyint': 'int',
  'mediumint': 'int',
  'serial': 'int',
  'bigserial': 'int',
  'float': 'float',
  'double': 'float',
  'real': 'float',
  'decimal': 'float',
  'numeric': 'float',
  'boolean': 'boolean',
  'bool': 'boolean',
  'date': 'date',
  'datetime': 'datetime',
  'timestamp': 'datetime',
  'time': 'time',
  'uuid': 'uuid',
  'blob': 'blob',
  'binary': 'blob',
  'varbinary': 'blob',
}


def _normalize_puml_type(raw: str) -> str:
  """Reduce el tipo PUML a una etiqueta interna."""
  if not raw:
    return 'string'
  clean = raw.strip().lower()
  # Quitar estereotipos y modificadores
  clean = re.sub(r'<<[^>]*>>', '', clean).strip()
  clean = re.sub(r'\{[^}]*\}', '', clean).strip()
  # Quedarse con la primera palabra (ignora "varchar(255)")
  clean = re.split(r'[\(\s]', clean)[0]
  return PUML_TYPE_ALIASES.get(clean, clean or 'string')


def _strip_visibility(token: str) -> str:
  """Quita marcadores de visibilidad y obligatoriedad."""
  return token.lstrip('+-#~*').strip()


def _parse_entity_attributes(body: str) -> list[ColumnSchema]:
    """Extrae columnas del cuerpo de un entity."""
    columns: list[ColumnSchema] = []
    
    # 🔧 NUEVO: detectar la posición del separador '--'
    # Convención PlantUML: todo lo anterior al '--' son claves primarias
    lines = body.splitlines()
    try:
        separator_idx = next(i for i, l in enumerate(lines) if l.strip() == '--')
    except StopIteration:
        separator_idx = -1  # no hay separador
    
    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue
        if line == '--':
            continue
        if line.startswith('--') or line.startswith('..'):
            continue
        if line.startswith("'"):
            continue
        
        line = line.rstrip(',')
        if ':' in line:
            name_part, type_part = line.split(':', 1)
        else:
            name_part, type_part = line, ''
        
        # 🔧 MODIFICADO: PK si está antes del separador, o por marcador, o si se llama 'id'
        is_pk = (
            (separator_idx >= 0 and idx < separator_idx)  # antes del '--'
            or bool(re.search(r'<<\s*PK\s*>>', type_part, re.IGNORECASE))
            or bool(re.search(r'\{\s*PK\s*\}', type_part, re.IGNORECASE))
            or bool(re.search(r'<<\s*id\s*>>', type_part, re.IGNORECASE))
        )
        
        raw_type = re.sub(r'(<<[^>]*>>|\{[^}]*\})', '', type_part).strip()
        clean_name = _strip_visibility(name_part)
        name = clean_name.split()[0] if clean_name.split() else ''
        name = name.split('(')[0].strip()
        if not name:
            continue
        
        normalized_type = _normalize_puml_type(raw_type)
        if name.lower() == 'id' and not is_pk:
            is_pk = True
        
        columns.append(ColumnSchema(
            name=name,
            type=normalized_type,
            is_pk=is_pk,
            is_nullable=not is_pk
        ))
    return columns


def _infer_fk_column(ref_table: str) -> str:
  """Convención: <tabla_referenciada>_id en minúsculas."""
  return f"{ref_table.lower()}_id"

def _find_existing_fk(table: TableSchema, ref_table: str,
                      label: str | None = None) -> str | None:
    # 1. Label tiene prioridad (nombre exacto de la columna FK)
    if label:
        clean = label.lower()
        if clean in table.columns:
            return clean
    # 2. Convención <table>_id / <singular>_id
    ref = ref_table.lower()
    if ref.endswith('ies'):
        singular = ref[:-3] + 'y'
    elif ref.endswith('s'):
        singular = ref[:-1]
    else:
        singular = ref
    for cand in (f"{ref}_id", f"{singular}_id"):
        if cand in table.columns:
            return cand
    return None

def _parse_relationships(content: str) -> list[tuple[str, str, str, str, str]]:
  """Devuelve (left, lcard, rcard, right, label)."""
  pattern = re.compile(
    r'([A-Za-z_]\w*)\s+(["\|o\{\}]+)\s*--\s*(["\|o\{\}]+)\s+([A-Za-z_]\w*)'
    r'(?:\s*:\s*([^\n]+))?',
    re.IGNORECASE
  )
  return [(m.group(1), m.group(2), m.group(3), m.group(4),
            (m.group(5) or "").strip().strip('"').strip("'"))
          for m in pattern.finditer(content)]


def _card_is_many(card: str) -> bool:
  """Detecta si la cardinalidad implica 'muchos' (acepta '{' o '}')."""
  return '{' in card or '}' in card


def _apply_relationships(schema, relationships):
    for left, lcard, rcard, right, label in relationships:
        lt, rt = schema.table(left), schema.table(right)
        if not lt or not rt:
            continue
        if _card_is_many(rcard) and not _card_is_many(lcard):
            fk = _find_existing_fk(rt, lt.name, label) or _infer_fk_column(lt.name)
            _ensure_fk_column(rt, fk, lt.name)
            rt.foreign_keys.append(ForeignKeySchema(
                column=fk, ref_table=lt.name, ref_column=_primary_key_name(lt)))
        elif _card_is_many(lcard) and not _card_is_many(rcard):
            fk = _find_existing_fk(lt, rt.name, label) or _infer_fk_column(rt.name)
            _ensure_fk_column(lt, fk, rt.name)
            lt.foreign_keys.append(ForeignKeySchema(
                column=fk, ref_table=rt.name, ref_column=_primary_key_name(rt)))


def _primary_key_name(table: TableSchema) -> str:
  for col in table.columns.values():
    if col.is_pk:
      return col.name
  return 'id'


def _ensure_fk_column(table: TableSchema, fk_col: str, ref_table: str) -> None:
  """Si la columna FK no existe, la añade como int nullable."""
  if fk_col.lower() in table.columns:
    return
  table.columns[fk_col.lower()] = ColumnSchema(
    name=fk_col,
    type='int',
    is_pk=False,
    is_nullable=True
  )


def parse_puml_schema(puml_file: str) -> SchemaModel:
  """
  Parsea un archivo PlantUML y devuelve un SchemaModel con:
    - tablas (entity)
    - columnas con tipo y PK
    - FKs inferidas a partir de relaciones 1-N
  """
  if not os.path.exists(puml_file):
    raise FileNotFoundError(f"PUML no encontrado: {puml_file}")

  with open(puml_file, 'r', encoding='utf-8') as f:
    content = f.read()

  schema = SchemaModel()

  entity_pattern = re.compile(
    r'entity\s+("?[A-Za-z_]\w*"?)\s*(?:as\s+\w+)?\s*\{([^}]*)\}',
    re.IGNORECASE | re.DOTALL
  )

  for match in entity_pattern.finditer(content):
    raw_name = match.group(1).strip().strip('"')
    body = match.group(2)
    columns = _parse_entity_attributes(body)

    # Asegurar PK explícita
    if not any(c.is_pk for c in columns):
      for col in columns:
        if col.name.lower() == 'id':
          col.is_pk = True
          col.is_nullable = False
          break
      else:
        columns.insert(0, ColumnSchema(
          name='id',
          type='int',
          is_pk=True,
          is_nullable=False
        ))

    table = TableSchema(
      name=raw_name,
      columns={c.name.lower(): c for c in columns}
    )
    schema.add_table(table)

  relationships = _parse_relationships(content)
  _apply_relationships(schema, relationships)

  logger.info(
    "PUML parsed: %d tables, %d relationships",
    len(schema.tables),
    len(relationships)
  )
  return schema

# ================================================================
# Archivo: services/retrieval.py
# ================================================================
# ai/services/retrieval.py
# [dedup] import os
from langchain_ollama import ChatOllama
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ..prompts.templates import QUERY_PROMPT, CHAIN_PROMPT

MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.2")
TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))
NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
NUM_GPU = int(os.getenv("OLLAMA_NUM_GPU", "99"))
VERBOSE = os.getenv("OLLAMA_VERBOSE", "true").lower() == "true"

print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
print(f"              {MODEL_NAME}               ")
print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")

def create_llm() -> ChatOllama:
  return ChatOllama(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    num_ctx=NUM_CTX,
    num_gpu=NUM_GPU,
    verbose=VERBOSE,
    timeout=600,          # <-- NUEVO: 10 min por llamada
    keep_alive="10m",     # <-- NUEVO: mantener modelo cargado
  )


def create_retriever(vector_db, source_file: str | None = None, k: int = 5):
    search_kwargs = {"k": k}
    if source_file:
        search_kwargs["filter"] = {"source_file": os.path.abspath(source_file)}
    return vector_db.as_retriever(search_kwargs=search_kwargs)


def create_chain(retriever):
  llm = create_llm()
  return (
    {"context": retriever, "question": RunnablePassthrough()}
    | CHAIN_PROMPT
    | llm
    | StrOutputParser()
  )


def create_direct_chain():
  llm = create_llm()
  return CHAIN_PROMPT | llm | StrOutputParser()

def create_flex_chain():
    """Chain simple que recibe {"input": str} para el juez FLEX."""
    from langchain.prompts import ChatPromptTemplate
    llm = create_llm()
    tmpl = ChatPromptTemplate.from_template("{input}")
    return tmpl | llm | StrOutputParser()


# ================================================================
# Archivo: services/sql_parser.py
# ================================================================
# ai/services/sql_parser.py
# [dedup] import re
# [dedup] import logging
# [dedup] from ai.models.schema import (
  ColumnSchema,
  ForeignKeySchema,
  TableSchema,
  SchemaModel
)

logger = logging.getLogger(__name__)


CONSTRAINT_KEYWORDS = {
  'PRIMARY', 'NOT', 'NULL', 'UNIQUE', 'DEFAULT',
  'AUTOINCREMENT', 'AUTO_INCREMENT', 'REFERENCES',
  'CHECK', 'CONSTRAINT', 'GENERATED', 'COLLATE'
}

TABLE_CONSTRAINT_PREFIXES = (
  'PRIMARY KEY',
  'FOREIGN KEY',
  'UNIQUE',
  'CONSTRAINT',
  'CHECK'
)


def _tokenize(part: str) -> list[str]:
  """Divide respetando paréntesis balanceados."""
  tokens, buf, depth = [], '', 0
  for ch in part:
    if ch == '(':
      depth += 1
      buf += ch
    elif ch == ')':
      depth -= 1
      buf += ch
    elif ch.isspace() and depth == 0:
      if buf:
        tokens.append(buf)
        buf = ''
    else:
      buf += ch
  if buf:
    tokens.append(buf)
  return tokens


def _split_top_level(body: str) -> list[str]:
  """Separa por comas de primer nivel."""
  parts, current, depth = [], [], 0
  for ch in body:
    if ch == '(':
      depth += 1
      current.append(ch)
    elif ch == ')':
      depth -= 1
      current.append(ch)
    elif ch == ',' and depth == 0:
      parts.append(''.join(current).strip())
      current = []
    else:
      current.append(ch)
  if current:
    parts.append(''.join(current).strip())
  return [p for p in parts if p]


def _normalize_sql_type(raw: str) -> str:
  """Normaliza el tipo SQL a una etiqueta comparable con el PUML."""
  if not raw:
    return 'string'
  t = raw.strip().lower()
  t = re.sub(r'\(.*\)', '', t).strip()  # quitar tamaño
  aliases = {
    'varchar': 'string',
    'char': 'string',
    'nvarchar': 'string',
    'text': 'string',
    'string': 'string',
    'int': 'int',
    'integer': 'int',
    'bigint': 'int',
    'smallint': 'int',
    'serial': 'int',
    'bigserial': 'int',
    'float': 'float',
    'double': 'float',
    'double precision': 'float',
    'tinyint': 'int',           # 🔧 NUEVO
    'mediumint': 'int',         # 🔧 NUEVO
    'real': 'float',
    'decimal': 'float',
    'numeric': 'float',
    'boolean': 'boolean',
    'bool': 'boolean',
    'date': 'date',
    'datetime': 'datetime',
    'timestamp': 'datetime',
    'time': 'time',
    'uuid': 'uuid',
    'blob': 'blob',
    'binary': 'blob',           # 🔧 NUEVO
    'varbinary': 'blob',        # 🔧 NUEVO
  }
  return aliases.get(t, t)


def _parse_column_definition(part: str) -> ColumnSchema | None:
  """Convierte una definición de columna en ColumnSchema."""
  tokens = _tokenize(part)
  if len(tokens) < 2:
    return None
  name = tokens[0].strip('`"[]').strip()
  if not name:
    return None

  type_tokens = []
  rest_tokens = []
  i = 1
  while i < len(tokens):
    tok_upper = tokens[i].upper()
    if tok_upper in CONSTRAINT_KEYWORDS:
      break
    type_tokens.append(tokens[i])
    i += 1
  rest_tokens = tokens[i:]

  raw_type = ' '.join(type_tokens) if type_tokens else 'text'
  rest = ' '.join(rest_tokens).upper()

  is_pk = 'PRIMARY KEY' in rest
  is_not_null = 'NOT NULL' in rest
  is_unique = 'UNIQUE' in rest
  default_match = re.search(r'DEFAULT\s+(.+?)(?:\s+(?:NOT|NULL|UNIQUE|PRIMARY|REFERENCES|CHECK)\b|$)', rest)
  default_value = default_match.group(1) if default_match else None

  return ColumnSchema(
    name=name,
    type=_normalize_sql_type(raw_type),
    is_pk=is_pk,
    is_nullable=not is_not_null and not is_pk,
    is_unique=is_unique,
    default=default_value
  )


def _parse_primary_key_constraint(part: str) -> list[str]:
  m = re.search(r'PRIMARY\s+KEY\s*\(([^)]+)\)', part, re.IGNORECASE)
  if not m:
    return []
  return [c.strip().strip('`"[]') for c in m.group(1).split(',')]


def _parse_foreign_key_constraint(part: str) -> ForeignKeySchema | None:
  m = re.search(
    r'FOREIGN\s+KEY\s*\(\s*[`"\[]?(\w+)[`"\]]?\s*\)\s*'
    r'REFERENCES\s+[`"\[]?(\w+)[`"\]]?\s*\(\s*[`"\[]?(\w+)[`"\]]?\s*\)',
    part,
    re.IGNORECASE
  )
  if not m:
    return None
  return ForeignKeySchema(column=m.group(1), ref_table=m.group(2), ref_column=m.group(3))


def _parse_create_body(table_name: str, body: str) -> TableSchema:
  """Construye TableSchema a partir del cuerpo de un CREATE TABLE."""
  table = TableSchema(name=table_name)
  column_pks = []
  table_level_pks = []

  for part in _split_top_level(body):
    upper = part.upper().lstrip()
    if upper.startswith('PRIMARY KEY'):
      table_level_pks.extend(_parse_primary_key_constraint(part))
      continue
    if upper.startswith('FOREIGN KEY'):
      fk = _parse_foreign_key_constraint(part)
      if fk:
        table.foreign_keys.append(fk)
      continue
    if upper.startswith('CONSTRAINT'):
      # CONSTRAINT name FOREIGN KEY (...) REFERENCES ...
      fk = _parse_foreign_key_constraint(part)
      if fk:
        table.foreign_keys.append(fk)
      pks = _parse_primary_key_constraint(part)
      if pks:
        table_level_pks.extend(pks)
      continue
    if upper.startswith('UNIQUE') or upper.startswith('CHECK'):
      continue

    col = _parse_column_definition(part)
    if col is None:
      continue
    table.columns[col.name.lower()] = col
    if col.is_pk:
      column_pks.append(col.name)

  # Si hay PK a nivel tabla, marcar las columnas
  for pk_name in set(table_level_pks + column_pks):
    key = pk_name.lower()
    if key in table.columns:
      table.columns[key].is_pk = True
      table.columns[key].is_nullable = False
    else:
      table.columns[key] = ColumnSchema(
        name=pk_name, type='int', is_pk=True, is_nullable=False
      )

  return table


def _extract_create_statements(sql_text: str) -> list[tuple[str, str]]:
  """Devuelve [(nombre_tabla, cuerpo_create)] de todo el SQL."""
  pattern = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?'
    r'[`"\[]?(\w+)[`"\]]?\s*\((.*?)\)\s*;',
    re.IGNORECASE | re.DOTALL
  )
  results = []
  for m in pattern.finditer(sql_text):
    results.append((m.group(1), m.group(2)))
  return results


def parse_sql_schema(sql_text: str, db_type: str = 'sqlite') -> SchemaModel:
  """Parsea el SQL generado y devuelve un SchemaModel."""
  schema = SchemaModel()
  if not sql_text:
    return schema

  for table_name, body in _extract_create_statements(sql_text):
    try:
      table = _parse_create_body(table_name, body)
      schema.add_table(table)
    except Exception as e:
      logger.warning("Error parseando tabla %s: %s", table_name, e)

  logger.info("SQL parsed: %d tables", len(schema.tables))
  return schema

# ================================================================
# Archivo: services/structural_validator.py
# ================================================================
# ai/services/structural_validator.py
# [dedup] import logging
# [dedup] from dataclasses import dataclass, field
from ai.models.schema import SchemaModel

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
  """Resultado de comparar el esquema esperado vs el generado."""
  # Tablas
  missing_tables: list[str] = field(default_factory=list)
  extra_tables: list[str] = field(default_factory=list)
  # Columnas
  missing_columns: dict[str, list[str]] = field(default_factory=dict)
  extra_columns: dict[str, list[str]] = field(default_factory=dict)
  # Tipos
  type_mismatches: dict[str, list[dict]] = field(default_factory=dict)
  # PKs
  pk_mismatches: list[dict] = field(default_factory=list)
  # FKs
  fk_mismatches: list[dict] = field(default_factory=list)
  # Not-null / unique (opcional, útil para el paper)
  nullability_mismatches: dict[str, list[dict]] = field(default_factory=dict)

  # Estadísticas
  stats: dict = field(default_factory=dict)

  @property
  def is_valid(self) -> bool:
    return not any([
      self.missing_tables,
      self.extra_tables,
      self.missing_columns,
      self.extra_columns,
      self.type_mismatches,
      self.pk_mismatches,
      self.fk_mismatches,
      self.nullability_mismatches,
    ])

  def summary(self) -> str:
    lines = []
    if self.is_valid:
      lines.append("✅ Sin errores estructurales detectados.")
      return "\n".join(lines)

    if self.missing_tables:
      lines.append(f"  • Tablas faltantes: {', '.join(self.missing_tables)}")
    if self.extra_tables:
      lines.append(f"  • Tablas extra: {', '.join(self.extra_tables)}")
    for t, cols in self.missing_columns.items():
      lines.append(f"  • [{t}] columnas faltantes: {', '.join(cols)}")
    for t, cols in self.extra_columns.items():
      lines.append(f"  • [{t}] columnas extra: {', '.join(cols)}")
    for t, diffs in self.type_mismatches.items():
      for d in diffs:
        lines.append(
          f"  • [{t}] tipo de '{d['column']}': "
          f"esperado={d['expected']} generado={d['generated']}"
        )
    for diff in self.pk_mismatches:
      lines.append(
        f"  • [{diff['table']}] PK esperada={diff['expected']} "
        f"generada={diff['generated']}"
      )
    for diff in self.fk_mismatches:
      for d in diff['diffs']:
        kind = 'faltante' if 'missing' in d else 'extra'
        lines.append(f"  • [{diff['table']}] FK {kind}: {d.get('missing') or d.get('extra')}")
    for t, diffs in self.nullability_mismatches.items():
      for d in diffs:
        lines.append(
          f"  • [{t}] nullability de '{d['column']}': "
          f"esperado={'NULL' if d['expected'] else 'NOT NULL'} "
          f"generado={'NULL' if d['generated'] else 'NOT NULL'}"
        )
    return "\n".join(lines)

  def to_dict(self) -> dict:
    return {
      'is_valid': self.is_valid,
      'missing_tables': self.missing_tables,
      'extra_tables': self.extra_tables,
      'missing_columns': self.missing_columns,
      'extra_columns': self.extra_columns,
      'type_mismatches': self.type_mismatches,
      'pk_mismatches': self.pk_mismatches,
      'fk_mismatches': self.fk_mismatches,
      'nullability_mismatches': self.nullability_mismatches,
      'stats': self.stats
    }


def _normalize(name: str) -> str:
  return name.strip().strip('`"[]').lower()


def validate_schema(expected: SchemaModel, generated: SchemaModel) -> ValidationReport:
  """Compara dos SchemaModel y devuelve un ValidationReport detallado."""
  report = ValidationReport()

  exp_tables = {k.lower(): v for k, v in expected.tables.items()}
  gen_tables = {k.lower(): v for k, v in generated.tables.items()}

  # ----- Tablas -----
  matched_tables = 0
  for tname in exp_tables:
    if tname not in gen_tables:
      report.missing_tables.append(exp_tables[tname].name)
    else:
      matched_tables += 1
  for tname in gen_tables:
    if tname not in exp_tables:
      report.extra_tables.append(gen_tables[tname].name)

  # Contadores para métricas
  stats = {
    'expected_tables': len(exp_tables),
    'generated_tables': len(gen_tables),
    'matched_tables': matched_tables,
    'expected_columns': 0,
    'generated_columns': 0,
    'matched_columns': 0,
    'expected_types': 0,
    'matched_types': 0,
    'expected_pks': 0,
    'matched_pks': 0,
    'expected_fks': 0,
    'matched_fks': 0,
  }

  # ----- Por tabla -----
  for tname, exp_table in exp_tables.items():
    if tname not in gen_tables:
      continue
    gen_table = gen_tables[tname]

    exp_cols = {k.lower(): v for k, v in exp_table.columns.items()}
    gen_cols = {k.lower(): v for k, v in gen_table.columns.items()}

    stats['expected_columns'] += len(exp_cols)
    stats['generated_columns'] += len(gen_cols)

    missing = [exp_cols[c].name for c in exp_cols if c not in gen_cols]
    extra = [gen_cols[c].name for c in gen_cols if c not in exp_cols]
    if missing:
      report.missing_columns[exp_table.name] = missing
    if extra:
      report.extra_columns[exp_table.name] = extra

    # Tipos y nullability en las columnas coincidentes
    type_diffs = []
    null_diffs = []
    for ckey in exp_cols:
      if ckey not in gen_cols:
        continue
      stats['matched_columns'] += 1
      ec = exp_cols[ckey]
      gc = gen_cols[ckey]
      stats['expected_types'] += 1
      if _normalize(ec.type) == _normalize(gc.type):
        stats['matched_types'] += 1
      else:
        type_diffs.append({
          'column': ec.name,
          'expected': ec.type,
          'generated': gc.type
        })
      if bool(ec.is_nullable) != bool(gc.is_nullable):
        null_diffs.append({
          'column': ec.name,
          'expected': ec.is_nullable,
          'generated': gc.is_nullable
        })
    if type_diffs:
      report.type_mismatches[exp_table.name] = type_diffs
    if null_diffs:
      report.nullability_mismatches[exp_table.name] = null_diffs

    # ----- PKs -----
    exp_pks = sorted([c.name.lower() for c in exp_table.columns.values() if c.is_pk])
    gen_pks = sorted([c.name.lower() for c in gen_table.columns.values() if c.is_pk])
    if exp_pks:
      stats['expected_pks'] += 1
      if exp_pks == gen_pks:
        stats['matched_pks'] += 1
      else:
        report.pk_mismatches.append({
          'table': exp_table.name,
          'expected': exp_pks,
          'generated': gen_pks
        })

    # ----- FKs -----
    exp_fk_set = {
      (fk.column.lower(), fk.ref_table.lower(), fk.ref_column.lower())
      for fk in exp_table.foreign_keys
    }
    gen_fk_set = {
      (fk.column.lower(), fk.ref_table.lower(), fk.ref_column.lower())
      for fk in gen_table.foreign_keys
    }
    stats['expected_fks'] += len(exp_fk_set)
    stats['matched_fks'] += len(exp_fk_set & gen_fk_set)

    fk_diffs = []
    for fk in exp_fk_set - gen_fk_set:
      fk_diffs.append({'missing': list(fk)})
    for fk in gen_fk_set - exp_fk_set:
      fk_diffs.append({'extra': list(fk)})
    if fk_diffs:
      report.fk_mismatches.append({
        'table': exp_table.name,
        'diffs': fk_diffs
      })

  report.stats = stats
  logger.info("Structural validation finished. Valid=%s", report.is_valid)
  return report

# ================================================================
# Archivo: services/vector_store.py
# ================================================================
# ai/services/vector_store.py
# [dedup] import os
# [dedup] import json
# [dedup] import shutil
# [dedup] import hashlib
# [dedup] import logging
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

EMBEDDING_MODEL = "nomic-embed-text"
VECTOR_STORE_NAME = "puml-rag"
PERSIST_DIRECTORY = "./chroma_db"
META_FILE = os.path.join(PERSIST_DIRECTORY, "meta.json")

from ai.paths import output_base
# [dedup] import os

PERSIST_DIRECTORY = os.path.join(output_base(), "chroma_db")
META_FILE = os.path.join(PERSIST_DIRECTORY, "meta.json")

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Hash determinista del PUML
# ---------------------------------------------------------------------------
def get_puml_file_hash(puml_path: str) -> str | None:
  """
  SHA-256 del contenido del PUML. Determinista entre procesos
  (a diferencia de hash() que usa PYTHONHASHSEED aleatorio).
  """
  if not os.path.exists(puml_path):
    return None
  with open(puml_path, 'rb') as f:
    return hashlib.sha256(f.read()).hexdigest()


# ---------------------------------------------------------------------------
# Metadata persistida (archivo + hash del último ingest)
# ---------------------------------------------------------------------------
def _read_meta() -> dict:
  if os.path.exists(META_FILE):
    try:
      with open(META_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
      return {}
  return {}


def _write_meta(data: dict) -> None:
  os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
  with open(META_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Decisión de recrear
# ---------------------------------------------------------------------------
def should_recreate_vector_db(puml_file: str, vector_db) -> bool:
  """
  Recrea si:
    - no hay DB,
    - el hash del PUML cambió,
    - cambió la ruta del PUML,
    - la metadata no existe (DB creada por versión antigua).
  """
  if vector_db is None:
    logger.info("No vector DB found -> recreate.")
    return True

  current_hash = get_puml_file_hash(puml_file)
  if current_hash is None:
    logger.warning("PUML no encontrado al calcular hash.")
    return True

  meta = _read_meta()
  stored_hash = meta.get("source_file_hash")
  stored_file = meta.get("source_file")

  if stored_hash is None:
    logger.info("No metadata found -> recreate (old DB).")
    return True

  if stored_hash != current_hash:
    logger.info(
      "PUML changed (hash %s -> %s) -> recreate.",
      stored_hash[:8], current_hash[:8]
    )
    return True

  if stored_file and os.path.abspath(stored_file) != os.path.abspath(puml_file):
    logger.info(
      "Different PUML file (%s -> %s) -> recreate.",
      stored_file, puml_file
    )
    return True

  logger.info("Vector DB is up-to-date (hash %s).", current_hash[:8])
  return False


# ---------------------------------------------------------------------------
# Limpieza
# ---------------------------------------------------------------------------
def clear_vector_db() -> bool:
  """Elimina el directorio de la base vectorial de forma segura."""
  if not os.path.exists(PERSIST_DIRECTORY):
    return True
  try:
    shutil.rmtree(PERSIST_DIRECTORY)
    logger.info("Cleared existing vector database.")
    return True
  except Exception as e:
    logger.error("Error clearing vector DB: %s", e)
    try:
      import subprocess
      subprocess.run(['rm', '-rf', PERSIST_DIRECTORY], check=True)
      logger.info("Cleared vector database using alternative method.")
      return True
    except Exception as e2:
      logger.error("Failed to clear vector database: %s", e2)
      return False


# ---------------------------------------------------------------------------
# Carga / creación
# ---------------------------------------------------------------------------
def check_existing_vector_db():
  """Carga la base vectorial existente si existe y tiene documentos."""
  if not os.path.exists(PERSIST_DIRECTORY):
    return None
  try:
    vector_db = Chroma(
      persist_directory=PERSIST_DIRECTORY,
      embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
      collection_name=VECTOR_STORE_NAME
    )
    count = vector_db._collection.count()
    if count > 0:
      logger.info("Found existing vector database with %d documents.", count)
      return vector_db
    logger.info("Existing vector DB is empty.")
  except Exception as e:
    logger.warning("Existing DB issue: %s", e)
  return None


def create_vector_db(chunks, puml_path: str):
  """
  Crea la base vectorial desde cero.
  SIEMPRE limpia el directorio antes para evitar mezclar PUMLs.
  """
  logger.info("Recreating vector DB from scratch (%d chunks).", len(chunks))

  # Borrado total para no arrastrar embeddings viejos
  if not clear_vector_db():
    logger.error("No se pudo limpiar la DB. Abortando para evitar mezcla.")
    raise RuntimeError("No se pudo limpiar chroma_db")

  embedding = OllamaEmbeddings(model=EMBEDDING_MODEL)

  try:
    os.makedirs(PERSIST_DIRECTORY, exist_ok=True, mode=0o755)
    vector_db = Chroma.from_documents(
      documents=chunks,
      embedding=embedding,
      collection_name=VECTOR_STORE_NAME,
      persist_directory=PERSIST_DIRECTORY
    )
    vector_db.persist()

    # Verificación de conteo
    count = vector_db._collection.count()
    if count != len(chunks):
      logger.warning(
        "Chunks esperados=%d, persistidos=%d", len(chunks), count
      )

    # Guardar metadata con el hash del PUML
    _write_meta({
      "source_file": os.path.abspath(puml_path),
      "source_file_hash": get_puml_file_hash(puml_path),
      "chunk_count": count,
    })

    logger.info("Vector DB created for %s (%d chunks).", puml_path, count)
    return vector_db

  except Exception as e:
    logger.error("Error creating persistent vector DB: %s", e)
    # Fallback en memoria (no persiste, evita el problema de mezcla)
    return Chroma.from_documents(
      documents=chunks,
      embedding=embedding,
      collection_name=VECTOR_STORE_NAME
    )


def load_vector_db():
  """Carga la base vectorial desde disco."""
  try:
    return Chroma(
      persist_directory=PERSIST_DIRECTORY,
      embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
      collection_name=VECTOR_STORE_NAME
    )
  except Exception as e:
    logger.error("Error loading vector DB: %s", e)
    return None

