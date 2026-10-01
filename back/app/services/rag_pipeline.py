# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.runnables import RunnablePassthrough

# from langchain_nvidia_ai_endpoints import ChatNVIDIA

# from .vector_strore import get_vector_store


# def create_retriever(document_id):
#     vector_store = get_vector_store()

#     return vector_store.as_retriever(
#         search_type="similarity",
#         search_kwargs={
#             "k": 4,
#             "filter": {
#                 "document_id": document_id
#             }
#         }
#     )


# def create_rag_chain(document_id):
#     retriever = create_retriever(document_id)

#     prompt = ChatPromptTemplate.from_template("""
# You are a helpful AI assistant.

# Answer the question using only the provided context.

# If the answer cannot be found in the context, say:
# "I don't know based on the provided document."

# Context:
# {context}

# Question:
# {question}

# Answer:
# """)

#     llm = ChatNVIDIA(
#     model="meta/llama-3.1-8b-instruct",
#     temperature=0,
#     max_tokens=1024,
# )

#     parser = StrOutputParser()

#     chain = (
#         {
#             "context": retriever,
#             "question": RunnablePassthrough()
#         }
#         | prompt
#         | llm
#         | parser
#     )

#     return chain

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from .vector_strore import get_vector_store


def is_relevant_to_pdf(question, document_id, threshold=0.3):
    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_score(
        question, k=1, filter={"document_id": document_id}
    )
    if not results:
        return False
    _, score = results[0]
    return score >= threshold


def create_retriever(document_id):
    vector_store = get_vector_store()

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 6,
            "filter": {
                "document_id": document_id
            }
        }
    )


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


PROMPT = ChatPromptTemplate.from_template("""
You are a helpful study assistant.

Answer the question using only the context below. Explain clearly in complete
sentences (a short paragraph or a few points, never a single word).

If the answer cannot be found in the context, say exactly:
"I don't know based on the provided document."

Context:
{context}

Question:
{question}

Answer:
""")

LLM = ChatNVIDIA(
    model="meta/llama-3.2-11b-vision-instruct",
    temperature=0,
    max_tokens=1024
)

CHAIN = PROMPT | LLM | StrOutputParser()


def ask_with_resources(question, document_id):

    retriever = create_retriever(document_id)
    docs = retriever.invoke(question)
    pages = sorted(set(doc.metadata["page_number"] for doc in docs))
    context = format_docs(docs)

    answer = CHAIN.invoke({"context": context, "question": question})

    return answer, pages, context