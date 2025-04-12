import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Any, Optional
import pickle
from pathlib import Path


class StartupVectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.id_to_text = {}
        self.id_to_metadata = {}

    def build_index(
        self, texts: Dict[str, str], metadata: Optional[Dict[str, dict]] = None
    ):
        """Build FAISS index from texts"""
        if not texts:
            raise ValueError("No texts provided to build index")

        # Convert texts to embeddings
        text_ids = list(texts.keys())
        text_list = [texts[text_id] for text_id in text_ids]

        # Generate embeddings
        embeddings = self.model.encode(text_list)

        # Ensure embeddings are 2D
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)

        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype("float32"))

        # Store text and metadata mappings
        self.id_to_text = {i: texts[text_id] for i, text_id in enumerate(text_ids)}
        if metadata:
            self.id_to_metadata = {
                i: metadata[text_id] for i, text_id in enumerate(text_ids)
            }

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar texts"""
        if self.index is None:
            raise ValueError("Index not built. Call build_index first.")

        # Convert query to embedding
        query_embedding = self.model.encode([query])

        # Ensure query embedding is 2D
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # Search in FAISS index
        distances, indices = self.index.search(query_embedding.astype("float32"), k)

        # Prepare results
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            result = {
                "text": self.id_to_text[idx],
                "score": float(
                    1 / (1 + distance)
                ),  # Convert distance to similarity score
                "metadata": self.id_to_metadata.get(idx, {}),
            }
            results.append(result)

        return results

    def save(self, path: str):
        """Save vector store to disk"""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, str(path / "index.faiss"))

        # Save mappings
        with open(path / "mappings.pkl", "wb") as f:
            pickle.dump(
                {"id_to_text": self.id_to_text, "id_to_metadata": self.id_to_metadata},
                f,
            )

    def load(self, path: str):
        """Load vector store from disk"""
        path = Path(path)

        # Load FAISS index
        self.index = faiss.read_index(str(path / "index.faiss"))

        # Load mappings
        with open(path / "mappings.pkl", "rb") as f:
            mappings = pickle.load(f)
            self.id_to_text = mappings["id_to_text"]
            self.id_to_metadata = mappings["id_to_metadata"]
