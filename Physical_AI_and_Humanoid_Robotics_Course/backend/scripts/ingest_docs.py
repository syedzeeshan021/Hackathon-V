import os
import asyncio
from pathlib import Path
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client import AsyncQdrantClient, models

# Assuming these are available from core.config
# from backend.src.core.config import settings
# from backend.src.core.vector_store import get_qdrant_client

# Placeholder for actual settings and Qdrant client
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "textbook_chunks"
DOCS_PATH = Path("frontend/docs")

# Placeholder for an embedding model (replace with actual model integration)
async def generate_embedding(text: str) -> list[float]:
    # In a real scenario, this would call an embedding model API or local model
    # For now, return a dummy embedding
    return [0.1] * 768 # Assuming a 768-dimensional embedding

def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    # Very basic chunking for demonstration purposes
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - chunk_overlap
    return chunks

async def ingest_docs():
    qdrant_client = AsyncQdrantClient(host=QDRANT_HOST, api_key=QDRANT_API_KEY)

    # Ensure collection exists
    try:
        await qdrant_client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        print(f"Collection '{COLLECTION_NAME}' recreated successfully.")
    except Exception as e:
        print(f"Could not recreate collection, might already exist: {e}")
        # If it already exists, just continue
        pass

    markdown_files = list(DOCS_PATH.glob("**/*.md"))

    points = []
    for md_file in markdown_files:
        print(f"Processing {md_file.name}...")
        content = md_file.read_text(encoding="utf-8")
        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
            embedding = await generate_embedding(chunk)
            points.append(
                models.PointStruct(
                    id=f"{md_file.stem}_{i}",
                    vector=embedding,
                    payload={"text": chunk, "source": str(md_file)}
                )
            )
    
    if points:
        # Upload points in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            await qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points[i:i + batch_size],
                wait=True,
            )
        print(f"Ingested {len(points)} chunks into Qdrant.")
    else:
        print("No markdown files found or processed.")


if __name__ == "__main__":
    asyncio.run(ingest_docs())