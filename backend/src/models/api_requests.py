from pydantic import BaseModel
from typing import List, Optional


class IngestionJobRequest(BaseModel):
    urls: List[str]
    config: Optional[dict] = None


class ReingestionRequest(BaseModel):
    force_reingest: bool = False
    urls: List[str]


class IngestionConfig(BaseModel):
    chunk_size: int = 512
    chunk_overlap: int = 50
    batch_size: int = 10


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 5
    min_similarity: float = 0.5


class RetrievalResponse(BaseModel):
    query: str
    results: List[dict]
    total_results: int
    search_time: float