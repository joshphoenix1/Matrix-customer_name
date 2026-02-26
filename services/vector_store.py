"""
ChromaDB vector store wrapper — persistent client, embed, query, delete.
"""

import os
try:
    import chromadb
except ImportError:
    chromadb = None
from config import CHROMA_DIR, EMBEDDING_MODEL

_client = None
_collection = None


def _get_client():
    """Lazy-init persistent ChromaDB client."""
    global _client
    if _client is None:
        if chromadb is None:
            raise ImportError("chromadb is not installed. Run: pip install chromadb")
        os.makedirs(CHROMA_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _client


def get_collection():
    """Get or create the persona_communications collection."""
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name="persona_communications",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_documents(ids, documents, metadatas=None):
    """Batch insert documents with 100-item chunking."""
    collection = get_collection()
    for i in range(0, len(ids), 100):
        batch_ids = ids[i:i + 100]
        batch_docs = documents[i:i + 100]
        batch_meta = metadatas[i:i + 100] if metadatas else None
        kwargs = {"ids": batch_ids, "documents": batch_docs}
        if batch_meta:
            kwargs["metadatas"] = batch_meta
        collection.add(**kwargs)


def query(query_text, n_results=5, where=None):
    """Semantic search against the collection."""
    collection = get_collection()
    if collection.count() == 0:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    kwargs = {"query_texts": [query_text], "n_results": min(n_results, collection.count())}
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


def delete_collection():
    """Delete the entire collection for full rebuild."""
    global _collection
    try:
        client = _get_client()
        client.delete_collection("persona_communications")
    except Exception:
        pass
    _collection = None


def get_count():
    """Return the number of documents in the collection."""
    try:
        return get_collection().count()
    except Exception:
        return 0
