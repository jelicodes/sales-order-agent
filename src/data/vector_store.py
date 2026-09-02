import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config.settings import settings

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None
_embedding_fn: GoogleGenerativeAIEmbeddings | None = None


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )
    return _embedding_fn


def get_vector_store() -> chromadb.Collection:
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=settings.CHROMADB_PATH)
        _collection = _client.get_or_create_collection(
            name="products",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def index_products(products: list[dict]) -> None:
    collection = get_vector_store()
    embeddings = get_embeddings()

    documents = [f"{p['name']} {p['description']} {p['category']}" for p in products]
    embedding_vectors = embeddings.embed_documents(documents)

    collection.upsert(
        ids=[f"product_{p['id']}" for p in products],
        embeddings=embedding_vectors,
        documents=documents,
        metadatas=[
            {"product_id": p["id"], "category": p["category"], "base_price": p["base_price"]}
            for p in products
        ],
    )


def search_products_semantic(query: str, n_results: int = 5) -> list[dict]:
    collection = get_vector_store()
    embeddings = get_embeddings()

    query_embedding = embeddings.embed_query(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)

    if not results["metadatas"][0]:
        return []
    return [
        {
            "product_id": m["product_id"],
            "category": m["category"],
            "base_price": m["base_price"],
            "score": 1 - d,
        }
        for m, d in zip(results["metadatas"][0], results["distances"][0])
    ]
