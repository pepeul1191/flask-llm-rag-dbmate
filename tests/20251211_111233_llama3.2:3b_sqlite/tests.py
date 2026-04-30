import os
import json
import numpy as np
import chromadb

# =========================================================
# 1. RUTAS ABSOLUTAS (CRÍTICO EN TU CASO)
# =========================================================

# test.py está en:
# BASE_PATH/tests/20251211_.../

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

RUN_DIR = CURRENT_DIR
BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CHROMA_PATH = os.path.join(BASE_PATH, "chroma_db")

SCHEMA_PATH = os.path.join(RUN_DIR, "schema.puml")
MIGRATIONS_PATH = os.path.join(RUN_DIR, "migrations")


# =========================================================
# 2. CHROMA CLIENT
# =========================================================

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection("migrations")


# =========================================================
# 3. CARGAR PUML
# =========================================================

def load_puml():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return f.read()


def parse_puml(puml: str):
    tables = set()
    relationships = set()

    for line in puml.splitlines():
        line = line.strip()

        if line.startswith("entity"):
            parts = line.split()
            if len(parts) >= 2:
                tables.add(parts[1].lower())

        if "--" in line and ":" in line:
            try:
                left, rest = line.split("--")
                right = rest.split(":")[0]

                relationships.add((
                    left.strip().lower(),
                    right.strip().lower()
                ))
            except:
                pass

    return tables, relationships


# =========================================================
# 4. RETRIEVAL DESDE CHROMA
# =========================================================

def retrieve_chunks(puml_text, k=10):
    results = collection.query(
        query_texts=[puml_text],
        n_results=k
    )
    return results["documents"][0]


# =========================================================
# 5. RELEVANCIA
# =========================================================

def is_relevant(chunk, tables, relationships):
    text = chunk.lower()

    if any(t in text for t in tables):
        return True

    for a, b in relationships:
        if a in text and b in text:
            return True

    return False


def build_rel(chunks, tables, relationships):
    return [1 if is_relevant(c, tables, relationships) else 0 for c in chunks]


# =========================================================
# 6. MÉTRICAS
# =========================================================

def precision_at_k(rel, k):
    return sum(rel[:k]) / k if k > 0 else 0


def recall_at_k(rel, total_rel, k):
    return sum(rel[:k]) / total_rel if total_rel > 0 else 0


def top1(rel):
    return 1 if rel and rel[0] == 1 else 0


def mrr(rel):
    for i, r in enumerate(rel):
        if r == 1:
            return 1 / (i + 1)
    return 0


def map_score(rel):
    hits = 0
    scores = []

    for i, r in enumerate(rel):
        if r:
            hits += 1
            scores.append(hits / (i + 1))

    return np.mean(scores) if scores else 0


def avg_rank(rel):
    for i, r in enumerate(rel):
        if r:
            return i + 1
    return None


# =========================================================
# 7. EVALUACIÓN PRINCIPAL
# =========================================================

def evaluate(k=10):
    puml = load_puml()

    tables, relationships = parse_puml(puml)

    chunks = retrieve_chunks(puml, k)

    rel = build_rel(chunks, tables, relationships)
    total_rel = sum(rel)

    return {
        "Precision@K": precision_at_k(rel, k),
        "Recall@K": recall_at_k(rel, total_rel, k),
        "Top1 Accuracy": top1(rel),
        "MRR": mrr(rel),
        "MAP": map_score(rel),
        "Average Rank": avg_rank(rel),
        "Chunks": chunks
    }


# =========================================================
# 8. MAIN
# =========================================================

if __name__ == "__main__":

    print("\n🚀 Evaluando RAG...\n")

    result = evaluate(k=10)

    for k, v in result.items():
        if k != "Chunks":
            print(f"{k}: {v}")

    print("\n📦 Retrieved Chunks:\n")
    for i, c in enumerate(result["Chunks"]):
        print(f"\n--- Chunk {i+1} ---\n{c}")