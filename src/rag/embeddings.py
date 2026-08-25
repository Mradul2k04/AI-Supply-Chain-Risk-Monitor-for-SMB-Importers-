import os
import hashlib
import logging
from typing import List, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Config options from .env (defaults to HuggingFace)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface").strip().lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5").strip()

try:
    from chromadb import EmbeddingFunction
except ImportError:
    class EmbeddingFunction:
        pass

class MockEmbeddingFunction(EmbeddingFunction):
    """
    A lightweight, deterministic fallback embedding function for local development
    that does not require downloading large PyTorch/transformers models.
    """
    def __init__(self, dimensionality: int = 384):
        self.dimensionality = dimensionality

    def name(self) -> str:
        return "MockEmbeddingFunction"

    def embed_query(self, input: Any) -> Any:
        if isinstance(input, list):
            return [self.embed_query(x) for x in input]
            
        hash_digest = hashlib.sha256(str(input).encode('utf-8')).digest()
        vector = []
        for i in range(self.dimensionality):
            byte_val = hash_digest[(i * 3) % len(hash_digest)]
            val = (byte_val / 255.0) - 0.5
            vector.append(val)
        return vector

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(t) for t in texts]

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.embed_documents(input)

class ChromaLangChainEmbeddingAdapter(EmbeddingFunction):
    """
    Adapter to bridge LangChain embedding providers with ChromaDB's EmbeddingFunction interface.
    """
    def __init__(self, langchain_embeddings: Any):
        self.langchain_embeddings = langchain_embeddings

    def name(self) -> str:
        if hasattr(self.langchain_embeddings, "model_name"):
            return str(self.langchain_embeddings.model_name)
        elif hasattr(self.langchain_embeddings, "model"):
            return str(self.langchain_embeddings.model)
        return self.langchain_embeddings.__class__.__name__

    def __call__(self, input: Any) -> Any:
        if isinstance(input, str):
            return self.langchain_embeddings.embed_query(input)
        return self.langchain_embeddings.embed_documents(input)

    def embed_documents(self, input: Any = None, texts: Any = None) -> List[List[float]]:
        docs = input if input is not None else (texts if texts is not None else [])
        if isinstance(docs, str):
            docs = [docs]
        return self.langchain_embeddings.embed_documents(docs)

    def embed_query(self, input: Any = None, text: Any = None) -> List[float]:
        q = input if input is not None else text
        if isinstance(q, list):
            return [self.embed_query(x) for x in q]
        return self.langchain_embeddings.embed_query(q)


def get_embedding_provider():
    """
    Loads Hugging Face embedding function (BAAI/bge-small-en-v1.5).
    Falls back to MockEmbeddingFunction if load fails.
    """
    # Ensure HF_TOKEN is populated from HUGGINGFACEHUB_API_TOKEN if set
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token
        os.environ["HUGGINGFACE_HUB_TOKEN"] = hf_token

    # Try loading HuggingFaceEmbeddings
    try:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings

        encode_kwargs = {'normalize_embeddings': True}
        hf_emb = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            encode_kwargs=encode_kwargs
        )
        logger.info(f"Successfully loaded HuggingFaceEmbeddings model: {EMBEDDING_MODEL}")
        return ChromaLangChainEmbeddingAdapter(hf_emb)
    except Exception as e:
        logger.warning(f"Failed to load HuggingFaceEmbeddings ({e}). Using Mock fallback.")
            
    # Default fallback
    logger.info("Using deterministic MockEmbeddingFunction.")
    return MockEmbeddingFunction()


