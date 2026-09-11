from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
def create_embeddings():
    embeddings =NVIDIAEmbeddings(
        model="nvidia/nemotron-3-embed-1b"
    )
    return embeddings