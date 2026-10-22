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