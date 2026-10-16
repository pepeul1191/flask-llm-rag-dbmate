# ai/evaluation/retrieval_metrics.py
"""
Precision@K, Recall@K, MAP, MRR, Top-1 Accuracy.
Idénticas a las de Flores et al. (2025), adaptadas al retriever del PUML.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def _precision_at_k(retrieved: List[str], relevant: set, k: int) -> float:
    topk = retrieved[:k]
    return sum(1 for r in topk if r in relevant) / k if k else 0.0


def _recall_at_k(retrieved: List[str], relevant: set, k: int) -> float:
    if not relevant:
        return 0.0
    topk = retrieved[:k]
    return sum(1 for r in topk if r in relevant) / len(relevant)


def _average_precision(retrieved: List[str], relevant: set) -> float:
    if not relevant:
        return 0.0
    hits, precisions = 0, []
    for i, r in enumerate(retrieved, 1):
        if r in relevant:
            hits += 1
            precisions.append(hits / i)
    return sum(precisions) / len(relevant) if precisions else 0.0


def _reciprocal_rank(retrieved: List[str], relevant: set) -> float:
    for i, r in enumerate(retrieved, 1):
        if r in relevant:
            return 1.0 / i
    return 0.0


def compute_retrieval_metrics(
    queries: List[Dict],
    retriever,
    k: int = 10,
) -> Dict:
    """
    queries: [{"query": "...", "relevant_chunks": ["chunk_3", "chunk_5"]}]
    retriever: el de create_retriever() de ai.services.retrieval

    Devuelve agregados MAP, MRR, P@K, R@K, Top-1 y detalle por query.
    """
    p_at_k, r_at_k, aps, rrs, top1 = [], [], [], [], []
    per_query = []

    for q in queries:
        docs = retriever.invoke(q["query"])
        retrieved_ids = [
            d.metadata.get("chunk_id") for d in docs
        ][:k]
        relevant = set(q["relevant_chunks"])

        p = _precision_at_k(retrieved_ids, relevant, k)
        r = _recall_at_k(retrieved_ids, relevant, k)
        ap = _average_precision(retrieved_ids, relevant)
        rr = _reciprocal_rank(retrieved_ids, relevant)
        t1 = 1.0 if retrieved_ids and retrieved_ids[0] in relevant else 0.0

        p_at_k.append(p); r_at_k.append(r); aps.append(ap)
        rrs.append(rr); top1.append(t1)

        per_query.append({
            "query": q["query"],
            "retrieved": retrieved_ids,
            "relevant": list(relevant),
            "P@K": round(p, 4), "R@K": round(r, 4),
            "AP": round(ap, 4), "RR": round(rr, 4), "Top1": t1,
        })

    n = len(queries) or 1
    return {
        "K": k,
        "n_queries": len(queries),
        "Precision@K": round(sum(p_at_k) / n, 4),
        "Recall@K":    round(sum(r_at_k) / n, 4),
        "MAP":         round(sum(aps) / n, 4),
        "MRR":         round(sum(rrs) / n, 4),
        "Top1":        round(sum(top1) / n, 4),
        "per_query": per_query,
    }