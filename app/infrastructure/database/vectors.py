from langchain_core.embeddings import Embeddings
from langchain_postgres import PGVector


class DocumentRepository:
    def __init__(self, db_url: str):
        self.search_type = "similarity"
        self.db_url = f"{db_url}_vectors"

    def search(self, embeddings_model: Embeddings, collection_name: str, query: str):
        vector_store = PGVector(
            embeddings=embeddings_model,
            collection_name=collection_name,
            connection=self.db_url,
            use_jsonb=True,
        )

        return vector_store.search(query, self.search_type)
