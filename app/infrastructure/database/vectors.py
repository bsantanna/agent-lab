from typing import List

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_postgres import PGVector


class DocumentRepository:
    def __init__(self, db_url: str):
        self.search_type = "similarity"
        self.db_url = f"{db_url}"

    def add(
        self,
        embeddings_model: Embeddings,
        collection_name: str,
        documents: List[Document],
    ):
        vector_store = self.get_vector_store(embeddings_model, collection_name)
        vector_store.add_documents(documents)

    def search(
        self,
        embeddings_model: Embeddings,
        collection_name: str,
        query: str,
        size: int = 5,
    ):
        vector_store = self.get_vector_store(embeddings_model, collection_name)
        return vector_store.search(query, self.search_type, k=size)

    def get_vector_store(
        self,
        embeddings_model: Embeddings,
        collection_name: str,
    ) -> VectorStore:
        return PGVector(
            embeddings=embeddings_model,
            collection_name=collection_name,
            connection=self.db_url,
            use_jsonb=True,
        )
