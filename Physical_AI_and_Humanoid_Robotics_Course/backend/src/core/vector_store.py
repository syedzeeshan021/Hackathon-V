from qdrant_client import QdrantClient

# These should come from config.py
QDRANT_HOST = "your_qdrant_host" 
QDRANT_API_KEY = "your_qdrant_api_key"

client = QdrantClient(
    host=QDRANT_HOST, 
    api_key=QDRANT_API_KEY,
)

async def get_qdrant_client():
    return client