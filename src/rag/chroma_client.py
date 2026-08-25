import os
import logging
import chromadb
from chromadb.config import Settings
from src.rag.embeddings import get_embedding_provider

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Config persistence path from settings
CHROMA_DB_DIR = settings.CHROMA_DB_PATH

class ChromaDBManager:
    """
    Manages connections and initialization for ChromaDB collections.
    """
    def __init__(self):
        # Create storage folder if not exist
        os.makedirs(CHROMA_DB_DIR, exist_ok=True)
        
        # Initialize client
        logger.info(f"Connecting to ChromaDB at: {CHROMA_DB_DIR}")
        self.client = chromadb.PersistentClient(
            path=CHROMA_DB_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get embedding provider
        self.embedding_provider = get_embedding_provider()
        self._init_collections()

    def _init_collections(self):
        """Pre-initialize the six required collections with our embedding function."""
        self.collections = {}
        collection_names = [
            "supplier_profiles",
            "risk_events",
            "regional_risk_profiles",
            "financial_evidence",
            "contingency_playbooks",
            "supplier_performance"
        ]
        
        for name in collection_names:
            namespaced_name = f"{settings.COLLECTION_NAME}_{name}"
            try:
                self.collections[name] = self.client.get_or_create_collection(
                    name=namespaced_name,
                    embedding_function=self.embedding_provider
                )
                logger.info(f"Initialized ChromaDB collection: {namespaced_name}")
            except Exception as e:
                logger.warning(f"Recreating collection {namespaced_name} due to initialization conflict/dimension mismatch: {e}")
                try:
                    self.client.delete_collection(name=namespaced_name)
                except Exception:
                    pass
                self.collections[name] = self.client.get_or_create_collection(
                    name=namespaced_name,
                    embedding_function=self.embedding_provider
                )
                logger.info(f"Re-initialized ChromaDB collection: {namespaced_name}")


    def get_collection(self, name: str):
        if name not in self.collections:
            raise ValueError(f"Collection {name} not found.")
        return self.collections[name]

    def reset_user_collections(self):
        """Clears dynamic user data from ChromaDB collections."""
        user_cols = ["supplier_profiles", "risk_events", "supplier_performance"]
        for col_name in user_cols:
            if col_name in self.collections:
                try:
                    col = self.collections[col_name]
                    existing_ids = col.get().get("ids", [])
                    if existing_ids:
                        col.delete(ids=existing_ids)
                        logger.info(f"Cleared {len(existing_ids)} entries from ChromaDB collection {col_name}")
                except Exception as e:
                    logger.warning(f"Failed to clear Chroma collection {col_name}: {e}")

# Global singleton client
chroma_manager = None

def get_chroma_manager():
    global chroma_manager
    if chroma_manager is None:
        chroma_manager = ChromaDBManager()
    return chroma_manager
