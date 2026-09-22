from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatNVIDIA(
    model="meta/llama-3.2-11b-vision-instruct",
    temperature=0,
    max_tokens=1024
)

prompt = ChatPromptTemplate.from_template("""
You are a helpful study assistant. Answer clearly and directly.
If there is previous conversation below, use it for context.
Never comment on whether the conversation is new.

Previous conversation:
{history}

New Question: {question}
""")
parser = StrOutputParser()
chain = prompt | llm | parser


def answer_general(question: str, history:str ="") -> str:
    return chain.invoke({"question": question, "history":history})

def rewrite_followup(question: str, history: str) -> str:
    prompt = ChatPromptTemplate.from_template("""
Rewrite the user's latest message as one standalone question, using the
conversation below to resolve words like "it", "this" or "more", and fixing
obvious typos. Reply with ONLY the rewritten question, nothing else.

Conversation:
{history}

Latest message: {question}
""")
    rewrite_chain = prompt | llm | parser
    return rewrite_chain.invoke({"question": question, "history": history}).strip().strip('"')