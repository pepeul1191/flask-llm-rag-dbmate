# ai/pipeline/runner.py
"""
Pipeline construido ENCIMA de main.execute.

Reglas de oro:
  * No modifica main.execute ni ai/services/*.
  * El stage "execute" solo invoca main.execute(folder, db_type, mode).
  * Los stages de error-detection usan parse_puml_schema + inject_errors + validate_schema.
  * Los imports de main son diferidos para evitar ciclos al arrancar Flask.
"""
import os
import json
import copy
import glob
import logging
import shutil
import tempfile
import datetime
from itertools import product
from typing import Dict, Callable
from contextlib import contextmanager
from pathlib import Path

from ai import env
from ai.services.retrieval import MODEL_NAME as LLM_MODEL_NAME
from ai.pipeline.timing import TimingCollector
from ai.services.puml_parser import parse_puml_schema
from ai.services.structural_validator import validate_schema
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
    from ai.services.vector_store import (
        check_existing_vector_db, create_vector_db,
        should_recreate_vector_db, clear_vector_db,
    )
    from ai.services.ingestion import ingest_puml, split_documents

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