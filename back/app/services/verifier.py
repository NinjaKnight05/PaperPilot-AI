import os
from crewai import Agent, Task, Crew, LLM

llm = LLM(
    model="nvidia_nim/meta/llama-3.2-11b-vision-instruct",
    api_key=os.getenv("NVIDIA_NIM_API_KEY"),
    temperature=0
)

verifier_agent = Agent(
    role="Fact Checker",
    goal="Check if an answer is actually supported by the given evidence",
    backstory="You are strict about only approving answers that are truly backed by the evidence.",
    llm=llm,
    verbose=False
)

def verify_answer(context: str, answer: str) -> bool:
    task = Task(
        description=f"""
Evidence:
{context}

Answer:
{answer}

Is the answer fully supported by the evidence? Respond with ONLY one word: yes or no.
""",
        expected_output="yes or no",
        agent=verifier_agent
    )
    crew = Crew(agents=[verifier_agent], tasks=[task], tracing=False)
    result = str(crew.kickoff()).strip().lower()
    return result.startswith("yes")