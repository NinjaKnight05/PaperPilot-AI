import os
import re
from crewai import Agent, Task, Crew, LLM

llm = LLM(
    model="nvidia_nim/meta/llama-3.2-11b-vision-instruct",
    api_key=os.getenv("NVIDIA_NIM_API_KEY"),
    temperature=0
)

classifier_agent = Agent(
    role="Query Classifier",
    goal="Classify a user question into pdf, web, or general",
    backstory="You are an expert at understanding what kind of information source a question needs.",
    llm=llm,
    verbose=False
)

_WEB_RE = re.compile(
    r"\bwho\s+(is|are|was|were)\b"
    r"|\bwho's\b"
    r"|\btell me about\b"
    r"|\b(news|latest|current|currently|today|tonight|yesterday|tomorrow|"
    r"recent|recently|update|updates|headlines?|trending|breaking)\b"
    r"|\bthis (week|month|year)\b"
    r"|\b20(2[4-9]|3\d)\b"
    r"|\b(price|stock|weather|score|winner|election|ceo|president|prime minister|minister)\b",
    re.IGNORECASE,
)


def needs_web(question: str) -> bool:
    return bool(_WEB_RE.search(question))


def classify_query(question: str, has_document: bool) -> str:
    if needs_web(question):
        return "web"

    pdf_line = "- pdf: the question is likely answerable by the uploaded document (definitions, explanations, topics a document would cover)\n" if has_document else ""
    intro = "A document has been uploaded. " if has_document else ""
    tiebreaker = "\nWhen in doubt between pdf and general, prefer pdf — the document was uploaded to be used." if has_document else ""
    valid_categories = ("pdf", "web", "general") if has_document else ("web", "general")
    default_fallback = "pdf" if has_document else "general"

    classify_task = Task(
        description=f"""
{intro}Classify the following question into exactly ONE category:
{pdf_line}- web: needs current or up-to-date facts — includes explicit "latest/today/now" questions, questions about things that change over time (current position holders like president/PM/CEO, current prices, current rankings, live scores, recent events) even without those exact words, AND questions about a specific real person, organisation, company, product or place (e.g. "who is X", "tell me about X")
- general: timeless facts, definitions, explanations, opinions, or creative tasks — things that don't change over time
{tiebreaker}
Respond with ONLY one word matching a category above.

Question: {{question}}
""",
        expected_output="One word",
        agent=classifier_agent
    )

    crew = Crew(
        agents=[classifier_agent],
        tasks=[classify_task],
        tracing=False
    )

    result = crew.kickoff(inputs={"question": question})
    result = str(result).strip().lower()

    if result not in valid_categories:
        result = default_fallback

    return result