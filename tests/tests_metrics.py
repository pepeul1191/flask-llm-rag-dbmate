import os
import re
import numpy as np
import chromadb

# =========================================================
# CONFIGURACIÓN
# =========================================================

RUNS = [
    "20251211_111124_llama3.2:3b_mysql",
    "20251211_111233_llama3.2:3b_sqlite",
    "20251211_111352_llama3.2:3b_postgres",
]

PUML_FILE = "basico.puml"
K = 10


# =========================================================
# PATHS
# =========================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

CHROMA_PATH = os.path.join(BASE_PATH, "chroma_db")

client = chromadb.PersistentClient(path=CHROMA_PATH)


# =========================================================
# SANITIZAR NOMBRE (CLAVE PARA CHROMA)
# =========================================================

def sanitize_collection_name(name: str):
    """
    Chroma solo permite: [a-zA-Z0-9._-]
    """
    name = name.lower()
    name = re.sub(r"[^a-z0-9._-]", "_", name)
    name = name.strip("_")
    return name


# =========================================================
# PUML PARSER
# =========================================================

def parse_puml(puml_text):
    tables = set()
    relationships = set()

    for line in puml_text.splitlines():
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
# MÉTRICAS
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


def precision_at_k(rel, k):
    return sum(rel[:k]) / k if k else 0


def recall_at_k(rel, total_rel, k):
    return sum(rel[:k]) / total_rel if total_rel else 0


def mrr(rel):
    for i, r in enumerate(rel):
        if r:
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


# =========================================================
# CHROMA RETRIEVAL
# =========================================================

def get_collection(run_name):
    clean_name = sanitize_collection_name(run_name)
    return client.get_or_create_collection(clean_name)


def retrieve_chunks(run_name, query, k):
    collection = get_collection(run_name)

    results = collection.query(
        query_texts=[query],
        n_results=k
    )

    return results["documents"][0]


# =========================================================
# EVALUACIÓN POR RUN
# =========================================================

def evaluate_run(run_name, puml_text, k):

    tables, relationships = parse_puml(puml_text)

    chunks = retrieve_chunks(run_name, puml_text, k)

    rel = build_rel(chunks, tables, relationships)
    total_rel = sum(rel)

    return {
        "run": run_name,
        "Precision@K": precision_at_k(rel, k),
        "Recall@K": recall_at_k(rel, total_rel, k),
        "MRR": mrr(rel),
        "MAP": map_score(rel)
    }


# =========================================================
# BATCH EVALUATION
# =========================================================

def run_batch():

    with open(PUML_FILE, "r", encoding="utf-8") as f:
        puml_text = f.read()

    results = []

    print("\n🚀 EVALUACIÓN BATCH RAG\n")

    for run in RUNS:
        print(f"\n▶ Run: {run}")

        res = evaluate_run(run, puml_text, K)
        results.append(res)

        for k, v in res.items():
            if k != "run":
                print(f"{k}: {round(v, 4)}")

    print("\n📊 RESUMEN FINAL\n")

    for r in results:
        print(r)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    run_batch()