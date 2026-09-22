# """
# TEST 1: Embeddings
# Checks that your NVIDIA API key works and the embedding model
# returns a vector. Run this FIRST — everything downstream depends on it.

# Run: python test_1_embeddings.py
# """
# from dotenv import load_dotenv
# load_dotenv()

# from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

# print("Creating embeddings client...")
# embeddings = NVIDIAEmbeddings(model="nvidia/nemotron-3-embed-1b")

# print("Embedding a test string...")
# vector = embeddings.embed_query("what is adolescence")

# print(f"SUCCESS. Vector length: {len(vector)}")
# print(f"First 5 values: {vector[:5]}")

# """
# TEST 2: LLM
# Checks that your NVIDIA API key works for the chat model and that
# the model name is valid. Independent of PDFs/Pinecone/retrieval.

# Run: python test_2_llm.py
# """
# from dotenv import load_dotenv
# load_dotenv()

# from langchain_nvidia_ai_endpoints import ChatNVIDIA

# print("Creating LLM client...")
# llm = ChatNVIDIA(
#     model="nvidia/nemotron-3.5-lightning-30b-a3b",
#     temperature=0,
#     max_completion_tokens=200
# )

# print("Sending a test message...")
# response = llm.invoke("Say hello in one sentence.")

# print("SUCCESS. Response:")
# print(response.content)

# """
# TEST 3: PDF extraction + chunking (hardcoded path version)

# Just edit PDF_PATH below to point at your PDF, then run:
#     python test_3_pdf_chunking.py
# """
# import sys
# from pathlib import Path

# sys.path.insert(0, str(Path(__file__).parent.parent))  # adjust if needed

# from app.services.pdf_processor import extract_text_from_pdf
# from app.services.chunker import chunk_documents

# # ---- EDIT THIS LINE ----
# PDF_PATH = r"D:\All Projects\self\research_paper.pdf"
# # -------------------------

# print(f"Extracting text from {PDF_PATH}...")
# documents = extract_text_from_pdf(PDF_PATH)
# print(f"SUCCESS. Extracted {len(documents)} page(s).")

# if documents:
#     print(f"\nPage 1 preview (first 300 chars):")
#     print(documents[0].page_content[:300])
#     print(f"\nPage 1 metadata: {documents[0].metadata}")
# else:
#     print("WARNING: No documents extracted. PDF may be empty, image-only, or unreadable by PyPDF.")

# print("\nChunking...")
# chunks = chunk_documents(documents)
# print(f"SUCCESS. Created {len(chunks)} chunk(s).")

# if chunks:
#     print(f"\nChunk 1 preview (first 300 chars):")
#     print(chunks[0].page_content[:300])
#     print(f"\nChunk 1 metadata: {chunks[0].metadata}")

# """
# TEST 4: Pinecone (write + read)
# Checks that Pinecone connection/index works, that vectors can be
# upserted, and that similarity search returns results. Uses fake
# text so it doesn't depend on your PDF.

# Run: python test_4_pinecone.py
# """
# from dotenv import load_dotenv
# load_dotenv()

# import os
# from langchain_core.documents import Document
# from app.services.vector_strore import create_vectors, get_vector_store

# TEST_DOC_ID = "test-doc-123"

# print(f"PINECONE_INDEX_NAME = {os.getenv('PINECONE_INDEX_NAME')}")

# print("\nCreating fake documents...")
# docs = [
#     Document(
#         page_content="Adolescence is the transitional period between childhood and adulthood.",
#         metadata={"document_id": TEST_DOC_ID, "page_number": 1, "source": "fake"}
#     ),
#     Document(
#         page_content="A chromosome is a thread-like structure of nucleic acids and protein.",
#         metadata={"document_id": TEST_DOC_ID, "page_number": 2, "source": "fake"}
#     ),
# ]

# print("Upserting into Pinecone...")
# create_vectors(docs)
# print("SUCCESS: upsert completed.")

# print("\nRunning similarity search for 'what is adolescence'...")
# vector_store = get_vector_store()
# retriever = vector_store.as_retriever(
#     search_type="similarity",
#     search_kwargs={"k": 2, "filter": {"document_id": TEST_DOC_ID}}
# )
# results = retriever.invoke("what is adolescence")

# print(f"SUCCESS. Got {len(results)} result(s).")
# for i, r in enumerate(results):
#     print(f"\nResult {i+1}: {r.page_content}")
#     print(f"Metadata: {r.metadata}")

# """
# TEST 5: Full RAG chain
# Runs the exact same create_rag_chain() used by /ask, against the
# fake document_id inserted by test_4_pinecone.py. Run test_4 first.

# Run: python test_5_rag_chain.py
# """
# from dotenv import load_dotenv
# load_dotenv()

# from app.services.rag_pipeline import create_rag_chain

# TEST_DOC_ID = "test-doc-123"  # must match what test_4_pinecone.py inserted

# print("Creating RAG chain...")
# chain = create_rag_chain(TEST_DOC_ID)

# question = "what is adolescence"
# print(f"Asking: {question}")

# answer = chain.invoke(question)

# print("\nSUCCESS. Answer:")
# print(answer)


# """
# Lists every model your NVIDIA API key currently has access to.
# This is the authoritative source of truth — catalog webpages and
# docs go stale fast, this hits the live API.

# Run: python list_models.py
# """
# from dotenv import load_dotenv
# load_dotenv()

# import os
# import requests

# api_key = os.getenv("NVIDIA_API_KEY")

# response = requests.get(
#     "https://integrate.api.nvidia.com/v1/models",
#     headers={"Authorization": f"Bearer {api_key}"}
# )
# response.raise_for_status()

# models = response.json()["data"]

# print(f"Total models available: {len(models)}\n")

# # Heuristic filter: names that suggest reasoning/thinking models to AVOID
# avoid_keywords = ["reason", "think", "r1", "deepseek", "kimi", "cosmos", "nano", "ultra"]

# print("=" * 70)
# print("LIKELY GOOD CANDIDATES (plain instruct/chat, no obvious reasoning flag):")
# print("=" * 70)
# for m in models:
#     model_id = m["id"]
#     lower = model_id.lower()
#     if "instruct" in lower and not any(k in lower for k in avoid_keywords):
#         print(model_id)

# print("\n" + "=" * 70)
# print("ALL MODELS (full list, for reference):")
# print("=" * 70)
# for m in models:
#     print(m["id"])


# import sys
# from pathlib import Path

# sys.path.insert(0, str(Path(__file__).parent))

# from app.services.pdf_processor import extract_text_from_pdf
# from app.services.chunker import chunk_documents

# PDF_PATH = r"D:\All Projects\self\sample.pdf"  # <-- put your scanned sample.pdf path here

# print(f"Extracting text from {PDF_PATH}...")
# documents = extract_text_from_pdf(PDF_PATH)
# print(f"SUCCESS. Extracted {len(documents)} page(s).")

# if documents:
#     print(f"\nPage 1 preview (first 500 chars):")
#     print(documents[0].page_content[:500])
#     print(f"\nPage 1 metadata: {documents[0].metadata}")

# print("\nChunking...")
# chunks = chunk_documents(documents)
# print(f"SUCCESS. Created {len(chunks)} chunk(s).")


# from dotenv import load_dotenv
# load_dotenv()

# from langchain_nvidia_ai_endpoints import ChatNVIDIA

# candidates = [
#     "nvidia/nemotron-3.5-lightning-30b-a3b",  # confirmed worked earlier
#     "meta/llama-3.2-90b-vision-instruct",
#     "meta/llama-3.2-11b-vision-instruct",
#     "mistralai/mistral-large-2-instruct",
#     "nv-mistralai/mistral-nemo-12b-instruct",
#     "nvidia/nemotron-4-340b-instruct",
#     "databricks/dbrx-instruct",
#     "zyphra/zamba2-7b-instruct",
# ]

# for model_name in candidates:
#     try:
#         llm = ChatNVIDIA(model=model_name, temperature=0, max_tokens=10)
#         response = llm.invoke("Say OK")
#         print(f"[WORKS] {model_name} -> {response.content[:50]}")
#     except Exception as e:
#         print(f"[FAILS] {model_name} -> {str(e)[:100]}")


from dotenv import load_dotenv
load_dotenv()

from app.services.vector_strore import get_vector_store

DOCUMENT_ID = "39bdfd19-39b0-4e7d-ae08-6db88c41561c"  # from your last /upload response

vector_store = get_vector_store()

questions = [
    "what is adolescence",              # should be relevant, if in your PDF
    "what is the weather today",        # should NOT be relevant
    "write me a poem about the sea",  
    "what is the Internet of Robotic Things" # should NOT be relevant
]

for q in questions:
    results = vector_store.similarity_search_with_score(
        q, k=1, filter={"document_id": DOCUMENT_ID}
    )
    if results:
        doc, score = results[0]
        print(f"{q!r} -> score: {score:.4f} | top match: {doc.page_content[:80]}")
    else:
        print(f"{q!r} -> no results")