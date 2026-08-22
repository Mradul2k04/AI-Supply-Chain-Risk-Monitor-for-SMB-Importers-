import logging
from typing import List, Dict, Any, Optional
from src.rag.chroma_client import get_chroma_manager

logger = logging.getLogger(__name__)

def retrieve_risk_evidence(
    query: str,
    collection_name: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """
    Retrieve documents from a specific ChromaDB collection matching the query and metadata filters.
    """
    logger.info(f"Retrieving from '{collection_name}' with query='{query}', filters={filters}")
    manager = get_chroma_manager()
    collection = manager.get_collection(collection_name)
    
    # Build where clause
    where_clause = {}
    if filters:
        # Filter out None values
        cleaned_filters = {k: v for k, v in filters.items() if v is not None}
        if len(cleaned_filters) > 1:
            # ChromaDB uses $and for multiple conditions
            where_clause = {"$and": [{k: v} for k, v in cleaned_filters.items()]}
        elif len(cleaned_filters) == 1:
            where_clause = cleaned_filters
            
    try:
        # Query collection
        query_args = {"query_texts": [query], "n_results": limit}
        if where_clause:
            query_args["where"] = where_clause
            
        results = collection.query(**query_args)
        
        formatted_results = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0] if "distances" in results else [1.0] * len(documents)
        
        for idx in range(len(documents)):
            formatted_results.append({
                "id": ids[idx],
                "content": documents[idx],
                "metadata": metadatas[idx],
                "relevance_score": 1.0 - distances[idx] if idx < len(distances) else 0.5
            })
            
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error querying collection {collection_name}: {e}", exc_info=True)
        return []
