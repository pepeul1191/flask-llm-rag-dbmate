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
import json
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