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
            "k": 8,
            "filter": {
                "document_id": document_id
            }
        }
    )


def format_docs(docs):
    # Label every chunk with its page so the model can quote and cite pages.
    # Chunks are put in page order so lists that span chunks read in sequence.
    docs = sorted(docs, key=lambda d: d.metadata.get("page_number", 0))
    return "\n\n".join(
        f"[Page {d.metadata.get('page_number', '?')}]\n{d.page_content}"
        for d in docs
    )


PROMPT = ChatPromptTemplate.from_template("""
You are a helpful study assistant.

Answer the question using only the context below. Each part of the context is
labelled with its page number.

Rules:
- Explain clearly in complete sentences (a short paragraph or a few points,
  never a single word).
- If the question asks for a list (for example "all", "steps", "types"), give
  every item that appears anywhere in the context, each with a short description.
- If the question asks for the exact lines, quote the relevant sentences word
  for word from the context, in quotation marks, and say which page each is on.
- Never invent items or facts that are not in the context.
- If the answer cannot be found in the context, say exactly:
"I don't know based on the provided document."

Context:
{context}

Question:
{question}

Answer:
""")

REWRITE_PROMPT = ChatPromptTemplate.from_template("""
Rewrite the follow-up question so it makes sense on its own, using the earlier
conversation only to fill in what it refers to. If it is already clear on its
own, return it unchanged. Output only the question.

Earlier conversation:
{history}

Follow-up question: {question}

Standalone question:""")

LLM = ChatNVIDIA(
    model="meta/llama-3.2-11b-vision-instruct",
    temperature=0,
    max_tokens=1024
)

CHAIN = PROMPT | LLM | StrOutputParser()
REWRITE_CHAIN = REWRITE_PROMPT | LLM | StrOutputParser()


def _turn_to_text(turn):
    """Accept {"q","a"}, {"question","answer"} or (q, a) turns."""
    if isinstance(turn, dict):
        q = turn.get("q") or turn.get("question") or ""
        a = turn.get("a") or turn.get("answer") or ""
    else:
        q, a = turn[0], turn[1]
    return f"Q: {q}\nA: {str(a)[:300]}"


def standalone_question(question, history):
    """Turn follow-ups like 'give me the exact lines' into a full question.

    Only runs when there is earlier chat and the question is short, to avoid
    an extra LLM call on every message.
    """
    if not history or len(question.split()) > 12:
        return question
    try:
        text = "\n".join(_turn_to_text(t) for t in history[-3:])
        rewritten = REWRITE_CHAIN.invoke(
            {"history": text, "question": question}
        ).strip().strip('"')
        if rewritten and len(rewritten) < 300:
            return rewritten
    except Exception as e:
        print("rewrite error:", repr(e))
    return question


def ask_with_resources(question, document_id, history=None):
    search_question = standalone_question(question, history)

    retriever = create_retriever(document_id)
    docs = retriever.invoke(search_question)
    pages = sorted(set(doc.metadata["page_number"] for doc in docs))
    context = format_docs(docs)

    answer = CHAIN.invoke({"context": context, "question": search_question})

    return answer, pages, context