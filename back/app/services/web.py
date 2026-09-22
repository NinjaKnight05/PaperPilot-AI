# import os
# from crewai import Agent, Task, Crew, LLM
# from crewai.tools import tool
# from langchain_community.tools import DuckDuckGoSearchRun

# search = DuckDuckGoSearchRun()


# @tool("Web Search")
# def search_tool(query: str) -> str:
#     """Searches the web and returns results for the query."""
#     try:
#         return search.run(query)
#     except Exception as e:
#         return f"Search failed: {e}"

# llm = LLM(
#     model="nvidia_nim/meta/llama-3.2-11b-vision-instruct",
#     api_key=os.getenv("NVIDIA_NIM_API_KEY"),
#     temperature=0
# )

# web_agent = Agent(
#     role="Web Researcher",
#     goal="Answer questions using current information from the web",
#     backstory="You search the web and answer using only what you find.",
#     tools=[search_tool],
#     llm=llm,
#     verbose=False,
#     max_iter=5,
#     max_execution_time=40
# )


# def answer_web(question: str) -> str:
#     task = Task(
#         description=f"Search the web and answer this question: {question}",
#         expected_output="A clear answer based on the search results",
#         agent=web_agent
#     )
#     crew = Crew(agents=[web_agent], tasks=[task], tracing=False)
#     return str(crew.kickoff())
import datetime
from langchain_community.tools import DuckDuckGoSearchRun

from .llm import answer_general

search = DuckDuckGoSearchRun()


def answer_web(question: str) -> str:
    # 1) one web search (never raises)
    try:
        results = search.run(question)
    except Exception:
        results = ""

    if not results.strip():
        return "I couldn't get web results right now. Please try again in a moment."

    # 2) one LLM call that answers only from those results
    prompt = (
        f"Today's date is {datetime.date.today().isoformat()}.\n"
        "Answer the question using ONLY the web search results below. "
        "Be direct and concise. If the results don't contain the answer, say so.\n\n"
        f"Search results:\n{results}\n\n"
        f"Question: {question}"
    )
    return answer_general(prompt)