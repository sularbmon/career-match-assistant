from app.database.session import SessionLocal
from app.services.knowledge_loader import load_knowledge
from app.services.text_chunker import create_chunks
from app.services.embedding_service import create_embeddings
from app.services.knowledge_service import save_knowledge_chunks
from app.models.knowledge import KnowledgeChunk

def seed_knowledge():
    db = SessionLocal()
    try:
        knowledge = load_knowledge()
        print(f"Loaded Knowledge: {len(knowledge)}")
        chunks = create_chunks(knowledge)
        print(f"Created chunks: {len(chunks)}")
        existing = {
            (row.skill, row.title, row.content)
            for row in db.query(KnowledgeChunk).all()
        }
        chunks = [chunk for chunk in chunks
                  if (chunk["skill"], chunk["title"], chunk["content"]) not in existing]
        if not chunks:
            print("Knowledge is already seeded; nothing to add.")
            return
        embedded_chunks = create_embeddings(chunks)
        print(f"Created embeddings: {len(embedded_chunks)}")
        save_chunks = save_knowledge_chunks(db, embedded_chunks)
        print(f"Saved {len(save_chunks)} knowledge chunks.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_knowledge()
