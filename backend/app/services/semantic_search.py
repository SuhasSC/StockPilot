import json
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[3]
STORE_DIR = ROOT / "vector_store"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class SemanticSearch:
    def __init__(self):
        index_path = STORE_DIR / "queries.faiss"
        examples_path = STORE_DIR / "examples.json"

        if not index_path.exists() or not examples_path.exists():
            raise RuntimeError(
                "FAISS index not found. Run scripts/build_vector_index.py first."
            )

        self.model = SentenceTransformer(MODEL_NAME)
        self.index = faiss.read_index(str(index_path))

        if self.index.d != self.model.get_sentence_embedding_dimension():
            raise RuntimeError(
                "FAISS index dimension does not match the embedding model. "
                "Rebuild the index using scripts/build_vector_index.py."
            )

        with examples_path.open("r", encoding="utf-8") as file:
            self.examples = json.load(file)

        if self.index.ntotal != len(self.examples):
            raise RuntimeError(
                "FAISS index and example count do not match. Rebuild the index."
            )

    def search(self, question: str, top_k: int = 3):
        vector = self.model.encode(
            [question],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        count = min(top_k, len(self.examples))
        scores, indices = self.index.search(vector, count)

        matches = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                matches.append({
                    "similarity": round(float(score), 4),
                    "example": self.examples[int(idx)],
                })

        return matches
