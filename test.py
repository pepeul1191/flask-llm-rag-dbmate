#!/usr/bin/env python
"""
run_pipeline.py — orquesta las corridas del pipeline sobre LLMs × DBs × schemas.

Cada combinación (llm, db, schema) genera un JSON temporal con:
    - inputs     = [schema actual]          (sobrescribe el del JSON base)
    - output_dir = ./runs/pipeline_results  (sobrescribe el del JSON base)

Uso:
    python run_pipeline.py                              # matriz completa
    python run_pipeline.py --llms llama3.2              # solo 1 modelo
    python run_pipeline.py --db sqlite                  # solo 1 DB
    python run_pipeline.py --schemas schemas/basico.puml
    python run_pipeline.py --skip-consolidate -y
"""
import os
import sys
import json
import shlex
import argparse
import tempfile
import subprocess
from pathlib import Path
from itertools import product


# ============================================================
# CONFIGURACIÓN — edita aquí si cambian los modelos / schemas
# ============================================================
DEFAULT_LLMS = [
    "llama3.2",
    "qwen2.5:3b",
    "gemma2:2b",
    "phi3",
    "deepseek-r1:1.5b-qwen-distill-q8_0",
]

DEFAULT_DB_CONFIGS = [
    ("sqlite",   "pipeline_sqlite.json"),
    ("mysql",    "pipeline_mysql.json"),
    ("postgres", "pipeline_postgres.json"),
]

# Nombres EXACTOS de los .puml que existen en schemas/
DEFAULT_SCHEMAS = [
    "./schemas/basico.puml",
    "./schemas/biblio.puml",
    "./schemas/innova.puml",
    "./schemas/northwind.puml",    
    "./schemas/postulaciones.puml",
]


# ============================================================
# HELPERS
# ============================================================
def _sanitize(name: str) -> str:
    return name.replace(":", "_").replace("/", "_")


def _extract_path_from_log(log_path: Path, keyword: str,
                            suffix: str = ".json") -> str | None:
    """Busca la última línea 'keyword: path' y devuelve el path."""
    if not log_path.exists():
        return None
    last = None
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if keyword in line and suffix in line:
            for tok in line.split():
                if tok.endswith(suffix):
                    last = tok
    return last


def _fmt(v) -> str:
    return str(v) if v is not None else "-"


def _append_metrics_table(log_path: Path, flores_file: str,
                           base: str, db: str, llm: str) -> None:
    try:
        data = json.loads(Path(flores_file).read_text(encoding="utf-8"))
    except Exception as e:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n⚠️  No se pudo leer {flores_file}: {e}\n")
        return

    lines = [
        "",
        "=" * 64,
        f"MÉTRICAS ESTRUCTURALES — {base} / {db} / {llm}",
        "=" * 64,
        f"{'Mode':<16} {'F1':<8} {'FK':<8} {'MAP':<8} {'EX':<6} {'FLEX':<6} {'BLEU':<8} {'Faith':<8}",
        "-" * 80,
    ]
    for r in data.get("runs", []):
        f_ = r.get("flores") or {}
        st = f_.get("structural") or {}
        rt = f_.get("retrieval") or {}
        ex = f_.get("execution") or {}
        nl = f_.get("nlg") or {}
        fa = f_.get("faithfulness") or {}
        lines.append(
            f"{r.get('mode', '-'):<16} "
            f"{_fmt(st.get('f1')):<8} "
            f"{_fmt(st.get('foreign_key_accuracy')):<8} "
            f"{_fmt(rt.get('MAP')):<8} "
            f"{_fmt(ex.get('EX')):<6} "
            f"{_fmt(ex.get('FLEX')):<6} "
            f"{_fmt(nl.get('BLEU')):<8} "
            f"{_fmt(fa.get('faithfulness')):<8}"
        )
    lines.append("")
    lines.append(f"JSON fuente: {flores_file}")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _append_detection_table(log_path: Path, error_file: str, base: str) -> None:
    try:
        data = json.loads(Path(error_file).read_text(encoding="utf-8"))
    except Exception as e:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n⚠️  No se pudo leer {error_file}: {e}\n")
        return

    lines = [
        "",
        "=" * 64,
        f"DETECCIÓN DE ERRORES INYECTADOS — {base}",
        "=" * 64,
    ]
    for r in data:
        m = r.get("detection_metrics") or {}
        per = m.get("per_error_type") or {}
        lines.append(f"Aggregate: {m.get('aggregate')}")
        lines.append(f"{'Error type':<20} {'TP':<4} {'FN':<4} {'FP':<4}")
        lines.append("-" * 38)
        for et, v in per.items():
            lines.append(
                f"{et:<20} {v.get('TP', 0):<4} {v.get('FN', 0):<4} {v.get('FP', 0):<4}"
            )

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ============================================================
# CORE: una invocación con JSON temporal
# ============================================================
def run_one(llm: str, db: str, cfg: str, puml: str,
            runs_dir: Path, root: Path) -> bool:
    """
    1. Lee el JSON base (pipeline_{db}.json)
    2. Sobrescribe inputs=[puml] y output_dir
    3. Escribe a un JSON temporal
    4. Ejecuta python -m ai.main ... pipeline <temp.json>
    5. Añade tablas de métricas al log
    """
    llm_safe = _sanitize(llm)
    base = Path(puml).stem
    log = runs_dir / f"full_{llm_safe}_{db}_{base}.log"

    # --- Leer JSON base y sobrescribir campos ---
    base_cfg = root / cfg
    if not base_cfg.exists():
        print(f"❌ No existe {base_cfg}")
        return False

    with open(base_cfg, "r", encoding="utf-8") as f:
        config = json.load(f)

    config["inputs"] = [puml]
    config["output_dir"] = str(runs_dir / "pipeline_results")

    # --- JSON temporal ---
    tmp_fd, tmp_path = tempfile.mkstemp(
        suffix=".json", prefix=f"cfg_{llm_safe}_{db}_{base}_"
    )
    os.close(tmp_fd)
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # --- Env ---
    env = os.environ.copy()
    env["APP_OUTPUT_DIR"] = str(runs_dir)
    env["OLLAMA_MODEL"] = llm

    cmd = [sys.executable, "-m", "ai.main", puml, db, "pipeline", tmp_path]

    print(f"\n{'=' * 60}")
    print(f"[RUN] {llm} | {db} | {base}")
    print(f"      cmd: {' '.join(shlex.quote(c) for c in cmd)}")
    print(f"      log: {log}")
    print(f"{'=' * 60}")

    try:
        with open(log, "w", encoding="utf-8") as f_log:
            result = subprocess.run(
                cmd, cwd=root, env=env,
                stdout=f_log, stderr=subprocess.STDOUT,
                timeout=None,
            )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if result.returncode != 0:
        print(f"❌ Falló (exit={result.returncode}): {log}")
        return False

    # --- Extraer flores + error_detection del log ---
    flores_file = _extract_path_from_log(log, "flores:", ".json")
    error_file = _extract_path_from_log(log, "error_detection_summary", ".json")

    if flores_file and Path(flores_file).exists():
        _append_metrics_table(log, flores_file, base, db, llm)
    else:
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"\n⚠️  Sin flores_metrics para {base}/{db}/{llm}\n")

    if error_file and Path(error_file).exists():
        _append_detection_table(log, error_file, base)

    print(f"✅ {log}")
    return True


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llms", nargs="+", default=DEFAULT_LLMS,
                        help="Modelos a probar (default: los 5 predefinidos)")
    parser.add_argument("--schemas", nargs="+", default=DEFAULT_SCHEMAS,
                        help="Rutas de los .puml")
    parser.add_argument("--db", nargs="+", default=None,
                        help="Filtro opcional: sqlite mysql postgres")
    parser.add_argument("--skip-consolidate", action="store_true",
                        help="No ejecutar test.py al final")
    parser.add_argument("--test-script", default="test.py")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="No pedir confirmación")
    args = parser.parse_args()

    root = Path.cwd()
    runs_dir = root / "runs"
    (runs_dir / "pipeline_results").mkdir(parents=True, exist_ok=True)

    # Filtrar schemas inexistentes
    existing_schemas = []
    for s in args.schemas:
        if Path(s).exists():
            existing_schemas.append(s)
        else:
            print(f"⚠️  Schema no existe y se omite: {s}")
    if not existing_schemas:
        print("❌ Ningún schema válido.")
        sys.exit(1)

    # Filtrar DBs
    db_configs = DEFAULT_DB_CONFIGS
    if args.db:
        db_configs = [(d, c) for d, c in DEFAULT_DB_CONFIGS if d in args.db]
        if not db_configs:
            print(f"❌ Ninguna DB válida en {args.db}")
            sys.exit(1)

    combos = list(product(args.llms, db_configs, existing_schemas))
    print(f"\nTotal invocaciones: {len(combos)}")
    for llm, (db, _cfg), puml in combos:
        print(f"  • {llm:<32} {db:<10} {Path(puml).stem}")

    if not args.yes:
        if input("\n¿Continuar? [y/N] ").strip().lower() != "y":
            print("Cancelado.")
            return

    total = ok = fail = 0
    for llm, (db, cfg), puml in combos:
        total += 1
        print(f"\n[{total}/{len(combos)}]")
        if run_one(llm, db, cfg, puml, runs_dir, root):
            ok += 1
        else:
            fail += 1

    print(f"\n{'=' * 60}")
    print("RESUMEN")
    print(f"{'=' * 60}")
    print(f"Total:  {total}")
    print(f"OK:     {ok}")
    print(f"Fallos: {fail}")

    if not args.skip_consolidate and (root / args.test_script).exists():
        print(f"\n{'=' * 60}")
        print("CONSOLIDANDO RESULTADOS")
        print(f"{'=' * 60}")
        subprocess.run([sys.executable, args.test_script], cwd=root)
    else:
        print("\n(Consolidación omitida)")


if __name__ == "__main__":
    main()