import logging
from typing import List

logger = logging.getLogger(__name__)

def split_text_by_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks with specified character size and overlap.
    """
    if not text:
        return []
    
    # If the text is smaller than chunk size, return it as a single chunk
    if len(text) <= chunk_size:
        return [text]
        
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # Advance by chunk_size minus overlap
        start += (chunk_size - chunk_overlap)
        
    logger.debug(f"Split text of length {len(text)} into {len(chunks)} chunks.")
    return chunks
