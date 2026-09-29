import base64
from pathlib import Path
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.messages import HumanMessage


vision_llm = ChatNVIDIA(
    model="meta/llama-3.2-11b-vision-instruct",
    temperature=0,
    max_tokens=1024,
)


def _mime_for(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    return "image/jpeg"


def answer_vision(question: str, image_path: Path, history: str = "") -> str:
    image_path = Path(image_path)
    b64_image = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    mime = _mime_for(image_path)

    text_part = (
        f"You are a helpful study assistant. Answer using the attached image.\n\n"
        f"Previous conversation:\n{history}\n\n"
        f"Question: {question}"
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": text_part},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64_image}"},
            },
        ]
    )

    response = vision_llm.invoke([message])
    return response.content