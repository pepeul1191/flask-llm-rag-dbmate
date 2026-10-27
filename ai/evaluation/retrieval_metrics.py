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
import logging
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