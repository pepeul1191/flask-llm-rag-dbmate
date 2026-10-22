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
import os
import json
import datetime
from typing import Any

from ai import env


def _flores_bundle_for_item(item: dict, structural: dict | None) -> dict:
    """Agrupa todo lo tipo Flores que exista en el ctx/item."""
    bundle = {
        "structural": structural or {},
        "retrieval": item.get("retrieval_metrics") or {},
        "execution": item.get("execution_metrics") or {},
        "nlg": item.get("nlg_metrics") or {},
        "faithfulness": item.get("faithfulness") or {},
        "timings": item.get("timings") or {},
    }
    # Filtrar según lo que esté activado en .env
    return {
        k: v for k, v in bundle.items()
        if k == "structural" or env.flores_enabled(k) or k == "timings"
    }


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