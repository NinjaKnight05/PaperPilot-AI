from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from .vector_strore import get_vector_store

def _search(question, document_id, k=8):
    vector_store = get_vector_store()
    return vector_store.similarity_search_with_score(
        question, k=k, filter={"document_id": document_id}
    )


def is_relevant_to_pdf(question, document_id, threshold=0.3):
    results = _search(question, document_id, k=1)
    if not results:
        return False
    _, score = results[0]
    return score >= threshold


def create_retriever(document_id):
    vector_store = get_vector_store()

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 8,
            "filter": {
                "document_id": document_id
            }
        }
    )


def format_docs(docs):
    docs = sorted(docs, key=lambda d: d.metadata.get("page_number", 0))
    return "\n\n".join(
        f"[Page {d.metadata.get('page_number', '?')}]\n{d.page_content}"
        for d in docs
    )


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
    results = _search(question, document_id, k=8)
    docs = [d for d, score in results if score >= 0.3]

    if not docs:
        return "I don't know based on the provided document.", [], ""

    pages = sorted(set(d.metadata["page_number"] for d in docs))
    context = format_docs(docs)

    answer = CHAIN.invoke({"context": context, "question": question})

    return answer, pages, context