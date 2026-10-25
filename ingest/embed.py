import os
import pickle
import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

_embedder = None

def get_embedder(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(model_name)
    return _embedder

def index_chunks(chunks: list[dict], chroma_dir: str, bm25_path: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    if not chunks:
        return

    os.makedirs(chroma_dir, exist_ok=True)
    os.makedirs(os.path.dirname(bm25_path), exist_ok=True)

    # 1. ChromaDB Dense Indexing
    client = chromadb.PersistentClient(path=chroma_dir)
    collection = client.get_or_create_collection(
        name="mutual_fund_facts",
        metadata={"hnsw:space": "cosine"}
    )

    embedder = get_embedder(model_name)
    texts = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

    # Upsert into ChromaDB
    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    # 2. BM25 Lexical Indexing
    tokenized_corpus = [doc.lower().split() for doc in texts]
    bm25 = BM25Okapi(tokenized_corpus)

    bm25_data = {
        "bm25": bm25,
        "chunks": chunks,
        "texts": texts
    }

    with open(bm25_path, "wb") as f:
        pickle.dump(bm25_data, f)


def index_pinecone_chunks(
    chunks: list[dict],
    api_key: str,
    index_name: str,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
):
    """Upserts chunk embeddings and metadata into Pinecone."""
    if not chunks or not api_key:
        return
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)

        embedder = get_embedder(model_name)
        texts = [c["text"] for c in chunks]
        embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

        vectors = []
        for i, c in enumerate(chunks):
            meta = dict(c["metadata"])
            meta["text"] = c["text"]
            vectors.append({
                "id": c["chunk_id"],
                "values": embeddings[i],
                "metadata": meta,
            })

        batch_size = 50
        for i in range(0, len(vectors), batch_size):
            index.upsert(vectors=vectors[i:i + batch_size])
    except Exception as e:
        print(f"Pinecone indexing error: {e}")

