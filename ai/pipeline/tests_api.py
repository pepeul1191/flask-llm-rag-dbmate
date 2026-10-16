# ai/pipeline/test_api.py
"""
API pública para los tests del Reviewer 1.

Función independiente: run_structural_validation_tests(...)
Pero por dentro usa el mismo PipelineConfig + PipelineRunner.
"""
import os
from typing import Optional, Sequence

from .config import PipelineConfig
from .runner import run_error_detection


def run_structural_validation_tests(
    folder_path: str,
    db_type: str = "sqlite",
    error_types=None,
    include_clean_baseline: bool = True,
    output_dir: str = "./pipeline_results",
    write_summary: bool = True,
) -> dict:
    cfg = PipelineConfig(
        inputs=[folder_path],     # <-- acepta carpeta o .puml
        db_types=[db_type],
        generation_stages=[],
        error_stages=["inject_and_validate", "measure_detection"],
        include_clean_baseline=include_clean_baseline,
        output_dir=output_dir,
    )
    if error_types:
        cfg.error_types = list(error_types)

    results = run_error_detection(cfg, write_summary=write_summary)
    if not results:
        raise FileNotFoundError(
            f"Entrada no válida o sin .puml: {folder_path}"
        )
    payload = results[0]
    metrics = payload.get("detection_metrics") or {}
    return {
        "input": payload["input"],
        "puml": payload["puml"],
        "db_type": payload["db_type"],
        "per_error_type": metrics.get("per_error_type", {}),
        "aggregate": metrics.get("aggregate", {}),
        "samples": metrics.get("samples", []),
        "summary_path": (
            os.path.join(output_dir, "error_detection_summary.json")
            if write_summary else None
        ),
    }