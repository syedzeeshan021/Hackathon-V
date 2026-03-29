from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from qdrant_client import models
from qdrant_client.http.exceptions import UnexpectedResponse

# Assuming these are available from core.config and core.vector_store
from backend.src.core.config import settings
from backend.src.core.vector_store import get_qdrant_client
from backend.scripts.ingest_docs import generate_embedding # Reusing placeholder embedding function

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    context: str = "" # Optional context, though typically retrieved from Qdrant internally

class ChatResponse(BaseModel):
    answer: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    qdrant_client = Depends(get_qdrant_client)
):
    # 1. Generate embedding for the question
    question_embedding = await generate_embedding(request.question) # Reusing placeholder

    # 2. Retrieve context from Qdrant
    retrieved_context = ""
    try:
        search_result = await qdrant_client.search(
            collection_name="textbook_chunks",
            query_vector=question_embedding,
            limit=3, # Retrieve top 3 relevant chunks
            query_filter=None, # No filtering for now
        )
        context_chunks = [hit.payload["text"] for hit in search_result]
        retrieved_context = "\n".join(context_chunks)
    except UnexpectedResponse as e:
        raise HTTPException(status_code=500, detail=f"Qdrant search failed: {e.reason}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during Qdrant search: {e}")

    # 3. Generate answer (placeholder for LLM integration)
    # In a real application, this would involve calling an LLM
    # with the question and the retrieved_context
    if retrieved_context:
        answer = (
            f"Based on the textbook content:\n\n"
            f"{retrieved_context}\n\n"
            f"Regarding your question: '{request.question}', "
            f"a detailed explanation would be provided here by an LLM."
        )
    else:
        answer = (
            f"I couldn't find relevant information in the textbook for your question: '{request.question}'. "
            f"Please try rephrasing or asking a different question."
        )

    return ChatResponse(answer=answer)