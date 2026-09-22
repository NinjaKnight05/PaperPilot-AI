from dotenv import load_dotenv
load_dotenv()

from app.services.router import classify_query

test_cases = [
    ("what is adolescence", True, "pdf"),
    ("what is the weather today", True, "web"),
    ("write me a poem about the sea", True, "general"),
    ("what is the weather today", False, "web"),
    ("explain photosynthesis", False, "general"),
]

for question, has_doc, expected in test_cases:
    result = classify_query(question, has_doc)
    status = "OK" if result == expected else "MISMATCH"
    print(f"[{status}] has_document={has_doc} | {question!r} -> got: {result}, expected: {expected}")