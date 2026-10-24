import json
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "nl_query_examples.json"
STORE_DIR = ROOT / "vector_store"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

STORE_DIR.mkdir(parents=True, exist_ok=True)

with DATA_FILE.open("r", encoding="utf-8-sig") as file:
    examples = json.load(file)

questions = [item["question"] for item in examples]

print(f"Loading multilingual model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)

embeddings = model.encode(
    questions,
    convert_to_numpy=True,
    normalize_embeddings=True,
    show_progress_bar=True,
).astype("float32")

index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(embeddings)

faiss.write_index(index, str(STORE_DIR / "queries.faiss"))

with (STORE_DIR / "examples.json").open("w", encoding="utf-8") as file:
    json.dump(examples, file, indent=2, ensure_ascii=False)

print("\nMultilingual FAISS index created successfully.")
print(f"Examples indexed: {index.ntotal}")
print(f"Vector dimensions: {embeddings.shape[1]}")
print(f"Index location: {STORE_DIR / 'queries.faiss'}")
