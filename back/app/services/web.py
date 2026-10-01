import os
import datetime
from tavily import TavilyClient
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool

from .llm import answer_general

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    return _client


@tool("web_search")
def web_search(query: str) -> str:
    """Search the web for current information. Input: a short search query."""
    try:
        res = _get_client().search(query=query, max_results=5)
    except Exception as e:
        print("tavily error:", repr(e))
        return "SEARCH FAILED"
    return "\n\n".join(
        f"{r['title']}\n{r['content']}\nSource: {r['url']}" for r in res["results"]
    )


def answer_web(question: str) -> str:
    today = datetime.date.today().strftime("%A, %d %B %Y")

    agent = Agent(
        role="Web research assistant",
        goal="Answer questions using fresh web search results",
        backstory="You search the web, read the results, and give short, accurate answers with sources.",
        tools=[web_search],
        llm=LLM(model="nvidia_nim/meta/llama-3.2-11b-vision-instruct"),
        allow_delegation=False,
        verbose=False,
    )
    task = Task(
        description=(
            f"Today is {today}. Use the web_search tool to find current information, "
            f"then answer this question concisely. Correct wrong premises. "
            f"Question: {question}"
        ),
        expected_output="A concise answer based on the search results, with source links.",
        agent=agent,
    )
    try:
        return str(Crew(agents=[agent], tasks=[task], verbose=False).kickoff())
    except Exception as e:
        print("crew web error:", repr(e))
        return answer_general(
            f"Today is {today}. Answer briefly from your own knowledge, "
            f"and say it may be outdated.\n\n{question}"
        )