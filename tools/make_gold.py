import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# tools/make_gold.py
import json, sys, os
from ai.services.fallback import generate_direct_migrations

puml, db_type, out = sys.argv[1:4]
sql = generate_direct_migrations(puml, db_type)
payload = {"samples": [{"id": f"{os.path.splitext(os.path.basename(puml))[0]}_gold_1",
                        "gold": sql}]}
with open(out, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)
print(f"✓ {out} ({len(sql)} chars)")