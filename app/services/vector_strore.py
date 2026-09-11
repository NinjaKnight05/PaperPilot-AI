from langchain_pinecone import PineconeVectorStore
from .embeddings import create_embeddings
import os


def create_vectors(chunks):
    embeddings = create_embeddings()

    vector_store = PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        index_name=os.getenv("PINECONE_INDEX_NAME")
    )

    return vector_store


def get_vector_store():
    embeddings = create_embeddings()

    vector_store = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        embedding=embeddings
    )

    return vector_store