import json
from pathlib import Path
from ai.services.fallback import generate_direct_migrations

Path("benchmarks").mkdir(exist_ok=True)
for puml in Path("schemas").glob("*.puml"):
    target = Path("benchmarks") / f"{puml.stem}_gold.json"
    if target.exists():
        print(f"= {target} (ya existe)")
        continue
    gold = generate_direct_migrations(str(puml), "sqlite")
    out = {"samples": [{"id": f"{puml.stem}_v1", "gold": gold}]}
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"✓ {target}")
