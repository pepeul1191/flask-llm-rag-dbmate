#!/usr/bin/env python3
"""
tools/apply_updates.py — Aplica/revierte parches de la herramienta.

Uso:
    python tools/apply_updates.py             # aplica parches
    python tools/apply_updates.py --check     # dry-run, no escribe nada
    python tools/apply_updates.py --restore   # revierte desde .bak
    python tools/apply_updates.py --verify    # solo muestra FKs por PUML

Parches:
    1. ai/services/puml_parser.py : _card_is_many acepta '{' o '}'  (fix FK=0)
    2. ai/services/ingestion.py   : regex acepta entity "foo" { ... } (fix innova)
    3. ai/pipeline/config.py      : 'build_retriever' en generation_stages (fix MAP="-")
    4. tools/*.py                 : añade bootstrap sys.path (fix ModuleNotFoundError)
    5. tools/__init__.py          : crea si no existe
    6. benchmarks/                : crea si no existe
"""
import argparse
import contextlib
import io
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Parches de código (search → replace, primer match)
# ---------------------------------------------------------------------------
PATCHES = [
    {
        "name": "puml_parser: _card_is_many acepta '}'",
        "file": ROOT / "ai/services/puml_parser.py",
        "search": """def _card_is_many(card: str) -> bool:
  \"\"\"Detecta si la cardinalidad implica 'muchos' (lleva llave).\"\"\"
  return '{' in card""",
        "replace": """def _card_is_many(card: str) -> bool:
  \"\"\"Detecta si la cardinalidad implica 'muchos' (acepta '{' o '}').\"\"\"
  return '{' in card or '}' in card""",
    },
    {
        "name": "ingestion: regex acepta entity \"foo\" { ... }",
        "file": ROOT / "ai/services/ingestion.py",
        "search": r"""  entity_pattern = r'(entity\s+\w+\s*\{[^}]+\})'""",
        "replace": r"""  entity_pattern = r'(entity\s+"?[A-Za-z_]\w*"?\s*(?:as\s+\w+)?\s*\{[^}]+\})'""",
    },
    {
        "name": "config: 'build_retriever' en generation_stages",
        "file": ROOT / "ai/pipeline/config.py",
        "search": """    generation_stages: List[str] = field(default_factory=lambda: [
        "execute",
        # Los siguientes""",
        "replace": """    generation_stages: List[str] = field(default_factory=lambda: [
        "execute",
        "build_retriever",
        # Los siguientes""",
    },
]

# Bootstrap que se antepone a cada tools/*.py (fix ModuleNotFoundError: ai)
TOOLS_BOOTSTRAP = """import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
"""


# ---------------------------------------------------------------------------
# Helpers de backup / restore
# ---------------------------------------------------------------------------
def _backup(path: Path) -> Path:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(path, bak)
    return bak


def _restore(path: Path) -> bool:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        return False
    shutil.copy2(bak, path)
    bak.unlink()
    return True


# ---------------------------------------------------------------------------
# Parches
# ---------------------------------------------------------------------------
def patch_code(dry: bool = False) -> None:
    print("== Parches de código ==")
    for p in PATCHES:
        f: Path = p["file"]
        if not f.exists():
            print(f"[SKIP] {p['name']} — no existe {f}")
            continue
        text = f.read_text(encoding="utf-8")
        if p["replace"] in text:
            print(f"[OK]   {p['name']} — ya aplicado")
            continue
        if p["search"] not in text:
            print(f"[FAIL] {p['name']} — patrón no encontrado en {f.name}")
            continue
        if dry:
            print(f"[DRY]  {p['name']} — se aplicaría")
            continue
        _backup(f)
        f.write_text(text.replace(p["search"], p["replace"], 1), encoding="utf-8")
        print(f"[DONE] {p['name']} — aplicado (backup: {f.name}.bak)")


def patch_tools(dry: bool = False) -> None:
    print("== Bootstrap sys.path en tools/*.py ==")
    tools = ROOT / "tools"
    if not tools.exists():
        print("[SKIP] tools/ no existe")
        return
    for py in sorted(tools.glob("*.py")):
        if py.name == "apply_updates.py":
            continue
        text = py.read_text(encoding="utf-8")
        if "sys.path.insert" in text:
            print(f"[OK]   tools/{py.name} — ya tiene bootstrap")
            continue
        if dry:
            print(f"[DRY]  tools/{py.name} — se añadiría bootstrap")
            continue

        lines = text.splitlines(keepends=True)
        if lines and lines[0].startswith("#!"):
            new_text = lines[0] + TOOLS_BOOTSTRAP + "\n" + "".join(lines[1:])
        else:
            new_text = TOOLS_BOOTSTRAP + "\n" + text

        _backup(py)
        py.write_text(new_text, encoding="utf-8")
        print(f"[DONE] tools/{py.name} — bootstrap añadido")


def create_dirs(dry: bool = False) -> None:
    print("== Directorios y archivos base ==")
    for d in [ROOT / "benchmarks", ROOT / "tools"]:
        if d.exists():
            print(f"[OK]   {d.name}/ existe")
        elif dry:
            print(f"[DRY]  {d.name}/ se crearía")
        else:
            d.mkdir(parents=True, exist_ok=True)
            print(f"[DONE] {d.name}/ creado")

    init = ROOT / "tools/__init__.py"
    if init.exists():
        print("[OK]   tools/__init__.py existe")
    elif not dry:
        init.write_text("", encoding="utf-8")
        print("[DONE] tools/__init__.py creado")


# ---------------------------------------------------------------------------
# Restore
# ---------------------------------------------------------------------------
def restore_all() -> None:
    print("== Restaurando desde .bak ==")
    any_restored = False
    for p in PATCHES:
        if _restore(p["file"]):
            print(f"[RESTORE] {p['file'].relative_to(ROOT)}")
            any_restored = True
    tools = ROOT / "tools"
    if tools.exists():
        for bak in tools.glob("*.py.bak"):
            real = bak.with_suffix("")
            shutil.copy2(bak, real)
            bak.unlink()
            print(f"[RESTORE] tools/{real.name}")
            any_restored = True
    if not any_restored:
        print("(nada que restaurar)")


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------
def verify() -> None:
    print("== FKs inferidas por PUML (post-parche) ==")
    try:
        # Silenciar el banner de retrieval.py al importar ai.services
        with contextlib.redirect_stdout(io.StringIO()):
            from ai.services.puml_parser import parse_puml_schema
    except Exception as e:
        print(f"[ERROR] no se pudo importar puml_parser: {e}")
        return

    schemas_dir = ROOT / "schemas"
    if not schemas_dir.exists():
        print(f"  (no existe {schemas_dir})")
        return

    for puml in sorted(schemas_dir.glob("*.puml")):
        try:
            schema = parse_puml_schema(str(puml))
            n_tables = len(schema.tables)
            fk_count = sum(len(t.foreign_keys) for t in schema.tables.values())
            status = "✅" if fk_count > 0 else "⚠️ "
            print(f"  {status} {puml.name:<22} {n_tables:>2} tablas, {fk_count:>2} FKs")
        except Exception as e:
            print(f"  ❌ {puml.name:<22} ERROR: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--check",   action="store_true", help="dry-run: no escribe nada")
    ap.add_argument("--restore", action="store_true", help="restaurar desde .bak")
    ap.add_argument("--verify",  action="store_true", help="solo mostrar FKs por PUML")
    args = ap.parse_args()

    if args.restore:
        restore_all()
        return
    if args.verify:
        verify()
        return

    print(f"Raíz del proyecto: {ROOT}\n")
    create_dirs(dry=args.check);  print()
    patch_code(dry=args.check);   print()
    patch_tools(dry=args.check);  print()

    if args.check:
        print("Modo dry-run: nada escrito.")
    else:
        print("Listo. Verificación:\n")
        verify()


if __name__ == "__main__":
    main()