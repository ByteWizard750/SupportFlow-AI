"""
RAG Service Layer for SupportFlow AI.

Handles knowledge base document loading, semantic chunking, local embedding generation
via Sentence Transformers (all-MiniLM-L6-v2), FAISS vector indexing, and nearest-neighbor search.
Includes in-memory query embedding caching for instant retrieval and sub-millisecond latency.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Base Directory Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_KB_DIR = ROOT_DIR / "knowledge_base"
DEFAULT_VECTOR_STORE_DIR = ROOT_DIR / "vector_store"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# In-memory cached model and index instances
_EMBEDDING_MODEL: Optional[SentenceTransformer] = None
_FAISS_INDEX: Optional[faiss.Index] = None
_CHUNKS_METADATA: Optional[List[Dict[str, Any]]] = None


def get_embedding_model() -> SentenceTransformer:
    """
    Lazy-loads and caches the SentenceTransformer embedding model.
    Downloads to local HuggingFace cache on first invocation.
    """
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        _EMBEDDING_MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _EMBEDDING_MODEL


def load_knowledge_base_documents(kb_dir: Optional[Path] = None) -> List[Dict[str, str]]:
    """
    Loads all support documentation files (.txt, .md) from the knowledge base directory.
    """
    dir_path = kb_dir or DEFAULT_KB_DIR
    if not dir_path.exists():
        return []

    documents = []
    for file_path in sorted(dir_path.glob("*.*")):
        if file_path.suffix.lower() in [".txt", ".md"]:
            try:
                content = file_path.read_text(encoding="utf-8").strip()
                if not content:
                    continue

                # Extract title from first markdown header if present, or filename
                lines = content.split("\n")
                first_line = lines[0].strip()
                if first_line.startswith("# "):
                    doc_title = first_line[2:].strip()
                else:
                    doc_title = file_path.stem.replace("_", " ").title()

                documents.append({
                    "doc_id": file_path.name,
                    "doc_title": doc_title,
                    "content": content
                })
            except Exception as e:
                print(f"[WARN] Failed to read knowledge base document {file_path}: {e}")

    return documents


def chunk_document(doc_id: str, doc_title: str, content: str) -> List[Dict[str, Any]]:
    """
    Splits a knowledge base document into semantically coherent section chunks.
    Preserves document title and section headings in chunk metadata.
    """
    chunks = []
    lines = content.split("\n")
    current_section = "General Overview"
    current_lines = []

    def flush_section_chunk(section_name: str, lines_list: List[str]):
        text = "\n".join(lines_list).strip()
        if not text:
            return

        # If section is very long, split into paragraphs
        paragraphs = text.split("\n\n")
        accumulated = []
        accumulated_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if accumulated_len + len(para) > 500 and accumulated:
                chunk_body = "\n\n".join(accumulated)
                full_text = f"Document: {doc_title}\nSection: {section_name}\n{chunk_body}"
                chunks.append({
                    "doc_id": doc_id,
                    "doc_title": doc_title,
                    "section": section_name,
                    "chunk_id": len(chunks),
                    "text": chunk_body,
                    "embedding_text": full_text
                })
                accumulated = [para]
                accumulated_len = len(para)
            else:
                accumulated.append(para)
                accumulated_len += len(para)

        if accumulated:
            chunk_body = "\n\n".join(accumulated)
            full_text = f"Document: {doc_title}\nSection: {section_name}\n{chunk_body}"
            chunks.append({
                "doc_id": doc_id,
                "doc_title": doc_title,
                "section": section_name,
                "chunk_id": len(chunks),
                "text": chunk_body,
                "embedding_text": full_text
            })

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            # Flush previous section
            flush_section_chunk(current_section, current_lines)
            current_section = stripped[3:].strip()
            current_lines = []
        elif stripped.startswith("# ") and not current_lines:
            # Top level title
            continue
        else:
            current_lines.append(line)

    flush_section_chunk(current_section, current_lines)
    return chunks


def build_vector_index(
    kb_dir: Optional[Path] = None,
    vector_store_dir: Optional[Path] = None,
    force_rebuild: bool = False
) -> Tuple[faiss.Index, List[Dict[str, Any]]]:
    """
    Constructs or loads the local FAISS vector index and metadata mapping.
    """
    global _FAISS_INDEX, _CHUNKS_METADATA

    v_dir = vector_store_dir or DEFAULT_VECTOR_STORE_DIR
    v_dir.mkdir(parents=True, exist_ok=True)
    index_file = v_dir / "faiss_index.bin"
    meta_file = v_dir / "chunks_metadata.json"

    # If index already exists and rebuild is not requested, load from disk
    if not force_rebuild and index_file.exists() and meta_file.exists():
        try:
            index = faiss.read_index(str(index_file))
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            _FAISS_INDEX = index
            _CHUNKS_METADATA = metadata
            return index, metadata
        except Exception as e:
            print(f"[WARN] Failed to load cached index, rebuilding: {e}")

    # Ingest documents and create chunks
    docs = load_knowledge_base_documents(kb_dir=kb_dir)
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc["doc_id"], doc["doc_title"], doc["content"]))

    if not all_chunks:
        # Fallback empty index
        dimension = 384
        index = faiss.IndexFlatIP(dimension)
        return index, []

    # Generate Embeddings
    model = get_embedding_model()
    texts_to_embed = [c["embedding_text"] for c in all_chunks]
    embeddings = model.encode(texts_to_embed, normalize_embeddings=True, show_progress_bar=False)

    embeddings_np = np.array(embeddings).astype("float32")
    dimension = embeddings_np.shape[1]

    # Use IndexFlatIP (Inner Product) on L2-normalized vectors = Cosine Similarity
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings_np)

    # Save index and metadata
    faiss.write_index(index, str(index_file))
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    _FAISS_INDEX = index
    _CHUNKS_METADATA = all_chunks
    return index, all_chunks


# In-memory query results cache for instantaneous lookups
_QUERY_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 3,
    min_similarity: float = 0.20,
    kb_dir: Optional[Path] = None,
    vector_store_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Encodes the query and searches the FAISS index for the top-k most relevant knowledge chunks.
    Results are cached in memory for sub-millisecond retrieval on repeated renders.

    Returns:
        List of matching chunk dicts containing text, doc_title, section, and similarity score.
    """
    global _FAISS_INDEX, _CHUNKS_METADATA, _QUERY_CACHE

    clean_query = query.strip()
    if not clean_query:
        return []

    cache_key = f"{clean_query}::{top_k}::{min_similarity}"
    if cache_key in _QUERY_CACHE:
        return _QUERY_CACHE[cache_key]

    if _FAISS_INDEX is None or _CHUNKS_METADATA is None:
        _FAISS_INDEX, _CHUNKS_METADATA = build_vector_index(
            kb_dir=kb_dir,
            vector_store_dir=vector_store_dir
        )

    if _FAISS_INDEX.ntotal == 0 or not _CHUNKS_METADATA:
        return []

    model = get_embedding_model()
    query_emb = model.encode([clean_query], normalize_embeddings=True)
    query_np = np.array(query_emb).astype("float32")

    k = min(top_k, _FAISS_INDEX.ntotal)
    scores, indices = _FAISS_INDEX.search(query_np, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0 and idx < len(_CHUNKS_METADATA):
            sim_score = float(score)
            if sim_score >= min_similarity:
                chunk_copy = dict(_CHUNKS_METADATA[idx])
                chunk_copy["similarity_score"] = round(sim_score, 4)
                results.append(chunk_copy)

    _QUERY_CACHE[cache_key] = results
    return results
