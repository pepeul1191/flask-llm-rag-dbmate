# tools/dump_chunk_ids.py
import sys
from pathlib import Path

# Añadir la raíz del proyecto (padre de tools/) a sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.services.ingestion import ingest_puml, split_documents

for path in sys.argv[1:]:
    content = ingest_puml(path)
    if content is None:
        print(f"❌ No se pudo leer {path}")
        continue
    chunks = split_documents(content, path)
    print(f"\n=== {path} ({len(chunks)} chunks) ===")
    for c in chunks:
        preview = c.page_content.replace("\n", " ")[:80]
        print(f"  [{c.metadata['chunk_id']:>2}] {c.metadata['chunk_type']:<15} {preview}")