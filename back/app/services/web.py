import os
import datetime
from tavily import TavilyClient

from .llm import answer_general

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return _client


def _search(query: str) -> str:
    res = _get_client().search(query=query, max_results=5)
    return "\n\n".join(
        f"{r['title']}\n{r['content']}\nSource: {r['url']}" for r in res["results"]
    )


def answer_web(question: str) -> str:
    today = datetime.date.today().strftime("%A, %d %B %Y")

    query = answer_general(
        f"Rewrite as a short web search query, add {datetime.date.today().year} "
        f"if it's about something current. Output only the query.\n\n{question}"
    ).strip()

    try:
        results = _search(query)
    except Exception as e:
        print("tavily error:", e)
        results = ""

    if not results:
        return answer_general(
            f"Today is {today}. Answer briefly from your own knowledge, "
            f"and say it may be outdated.\n\n{question}"
        )

    return answer_general(
        f"Today is {today}. Answer using the search results below. Be concise. "
        "Summarize partial info too, and correct wrong premises. "
        "Only say nothing was found if the results are irrelevant.\n\n"
        f"Results:\n{results}\n\nQuestion: {question}"
    )