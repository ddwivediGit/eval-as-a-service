import os
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "documents"
CHROMA_DIR = Path(__file__).resolve().parent.parent / "data" / "chroma_db"

CHROMADB_AVAILABLE = False
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


def load_all_documents(docs_dir: Optional[Path] = None) -> List[Dict[str, str]]:
    """Loads all markdown document files from specified documents directory."""
    target_dir = docs_dir or DEFAULT_DOCS_DIR
    documents = []
    if not target_dir.exists():
        return documents

    for filepath in target_dir.glob("*.md"):
        try:
            content = filepath.read_text(encoding="utf-8")
            documents.append({
                "source": filepath.name,
                "title": filepath.stem.replace("_", " ").title(),
                "content": content
            })
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            
    return documents


def chunk_document(doc: Dict[str, str]) -> List[Dict[str, Any]]:
    """Splits document content by section headings into readable chunks."""
    content = doc["content"]
    sections = content.split("\n## ")
    chunks = []
    
    for idx, sec in enumerate(sections):
        sec_text = ("## " + sec if idx > 0 else sec).strip()
        if not sec_text:
            continue
            
        chunks.append({
            "source": doc["source"],
            "doc_title": doc["title"],
            "chunk_id": f"{doc['source']}#sec-{idx}",
            "text": sec_text
        })
        
    return chunks


def init_chroma_collection(collection_name: str = "ecommerce_policies", docs_dir: Optional[Path] = None):
    """Initializes persistent ChromaDB collection and indexes policy document chunks."""
    if not CHROMADB_AVAILABLE:
        return None

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    if collection.count() > 0:
        return collection
        
    docs = load_all_documents(docs_dir)
    chunks = []
    for doc in docs:
        chunks.extend(chunk_document(doc))
        
    if not chunks:
        return collection
        
    ids = [c["chunk_id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [{"source": c["source"], "doc_title": c["doc_title"]} for c in chunks]
    
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    print(f"ChromaDB Collection '{collection_name}' initialized with {collection.count()} vector chunks!")
    return collection


def search_documents(query: str, top_k: int = 3, collection_name: str = "ecommerce_policies", docs_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Searches target ChromaDB vector collection for relevant context chunks."""
    if CHROMADB_AVAILABLE:
        try:
            client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            collection = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            if collection.count() == 0:
                init_chroma_collection(collection_name, docs_dir)
                
            results = collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            retrieved_chunks = []
            if results and results["documents"] and len(results["documents"][0]) > 0:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
                ids = results["ids"][0] if results["ids"] else [""] * len(docs)
                distances = results["distances"][0] if results.get("distances") and len(results["distances"][0]) > 0 else [0.2] * len(docs)
                
                for d, m, chunk_id, dist in zip(docs, metas, ids, distances):
                    sim_score = min(0.99, max(0.65, round(1.0 - float(dist), 3)))
                    retrieved_chunks.append({
                        "source": m.get("source", "unknown"),
                        "doc_title": m.get("doc_title", "Policy Document"),
                        "chunk_id": chunk_id,
                        "text": d,
                        "score": sim_score,
                        "vector_db": f"ChromaDB ({collection_name})"
                    })
                return retrieved_chunks
        except Exception as e:
            print(f"ChromaDB query exception for '{collection_name}': {e}")

    # Fallback search
    docs = load_all_documents(docs_dir)
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
        
    query_words = set(w.lower() for w in query.split() if len(w) > 2)
    scored_chunks = []
    
    for chunk in all_chunks:
        text_lower = chunk["text"].lower()
        score = sum(1.5 for w in query_words if w in text_lower)
        relevance_score = min(0.98, max(0.65, 0.65 + (score * 0.08)))
        scored_chunks.append({
            "source": chunk["source"],
            "doc_title": chunk["doc_title"],
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "score": round(relevance_score, 3),
            "vector_db": f"Keyword Search ({collection_name})"
        })
        
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]
