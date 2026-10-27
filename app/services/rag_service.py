from sqlalchemy.orm import Session
from app.services.embedding_service import create_query_embedding
from app.services.vector_search import search_similar_chunks

def generate_recommendations(db: Session, missing_skills: list[str],
                             top_k: int=2) -> list[dict]:

    recommendations = []
    for skill in missing_skills:
        query = (f"Learning resources & career guidance for {skill}")
        query_embedding = create_query_embedding(query)
        relevant_chunks = search_similar_chunks(
            db=db, query_embedding=query_embedding, skill=skill, top_k=top_k
        )
        retrieved_knowledge = []
        for chunk in relevant_chunks:
            retrieved_knowledge.append({
                "knowledge_id": chunk.id,
                "skill": chunk.skill,
                "title": chunk.title,
                "content": chunk.content,
                "level": chunk.level
            })
        recommendations.append({
            "missing_skills": skill,
            "recommendations": (
                f"Use the retrieved materials to practice {skill}."
                if retrieved_knowledge else
                f"No curated material is available for {skill} yet."
            ),
            "retrieved_knowledge": retrieved_knowledge
        })

    return recommendations
