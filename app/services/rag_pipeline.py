import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from langchain_nvidia_ai_endpoints import ChatNVIDIA

from .vector_strore import get_vector_store


def create_retriever():

    vector_store = get_vector_store()

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )


def create_rag_chain():

    retriever = create_retriever()

    prompt = ChatPromptTemplate.from_template("""
You are a helpful AI assistant.

Answer the question using only the provided context.

If the answer cannot be found in the context, say:
"I don't know based on the provided document."

Context:
{context}

Question:
{question}

Answer:
""")

    llm = ChatNVIDIA(
    model="nvidia/nemotron-3.5-lightning-30b-a3b",
    temperature=0,
    max_completion_tokens=16384
)
    parser = StrOutputParser()

    chain = (
        {
            "context": retriever,
            "question": RunnablePassthrough()
        } | prompt  | llm | parser
    )

    return chain