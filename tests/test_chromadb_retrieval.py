import pytest
from src.rag.chroma_client import get_chroma_manager
from src.rag.retriever import retrieve_risk_evidence
from src.rag.ingestion import ingest_default_knowledge_base

def test_chromadb_retrieval_and_filtering():
    # Arrange: Initialize client and seed default data
    manager = get_chroma_manager()
    ingest_default_knowledge_base()
    
    # Act: Retrieve playbooks for weather disruptions
    results = retrieve_risk_evidence(
        query="monsoon flooding backup plan",
        collection_name="contingency_playbooks",
        filters={"risk_type": "weather"}
    )
    
    # Assert
    assert len(results) > 0
    assert "weather" in results[0]["metadata"]["risk_type"]
    assert "relevance_score" in results[0]
