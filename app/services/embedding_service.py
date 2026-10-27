from functools import lru_cache

MODEL_NAME = "all-MiniLM-L6-v2"
@lru_cache(maxsize=1)
def get_model():
    """Load the model only when embeddings are requested."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)

def create_embeddings(chunks : list[dict]) -> list[dict]:
    texts = [chunk["content"] for chunk in chunks]
    if not texts:
        return []
    embeddings = get_model().encode(texts, convert_to_numpy=True)
    embedded_chunks = []
    for chunk, embedding in zip(chunks, embeddings):
        embedded_chunks.append({**chunk, "embedding": embedding.tolist()})
    return embedded_chunks

def create_query_embedding(text: str) -> list[float]:
    embedding = get_model().encode(text, convert_to_numpy=True)
    return embedding.tolist()

