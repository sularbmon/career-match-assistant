from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeChunk

def search_similar_chunks(db: Session, query_embedding: list[float], skill: str | None = None,
                          top_k: int=3) -> list[KnowledgeChunk]:

    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")
    query = db.query(KnowledgeChunk).filter(KnowledgeChunk.embedding.is_not(None))
    if skill:
        query = query.filter(KnowledgeChunk.skill == skill)
    return query.order_by(
        KnowledgeChunk.embedding.cosine_distance(query_embedding), KnowledgeChunk.id
    ).limit(top_k).all()


