import os
import chromadb

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MIGRATIONS_PATH = os.path.join(BASE_PATH, "tests/20251211_111124_llama3.2:3b_mysql/migrations")
CHROMA_PATH = os.path.join(BASE_PATH, "chroma_db")

client = chromadb.PersistentClient(path=CHROMA_PATH)

collection = client.get_or_create_collection("migrations")


def load_sql_files():
    docs = []
    ids = []

    for i, file in enumerate(os.listdir(MIGRATIONS_PATH)):
        if file.endswith(".sql"):
            path = os.path.join(MIGRATIONS_PATH, file)

            with open(path, "r", encoding="utf-8") as f:
                docs.append(f.read())
                ids.append(str(i))

    return docs, ids


docs, ids = load_sql_files()

collection.add(
    documents=docs,
    ids=ids
)

print("✅ ChromaDB indexado correctamente")