"""Task 10 — Sinh câu trả lời có trích dẫn.

Luồng xử lý:
    1. Lấy top-k chunk.
    2. Sắp xếp lại để giảm hiện tượng bỏ sót thông tin ở giữa context.
    3. Định dạng context kèm tiêu đề và nguồn.
    4. Gọi nhà cung cấp được chọn trong .env.
    5. Trả về câu trả lời, nguồn và đường retrieval.

Nếu context không đủ hoặc nhà cung cấp lỗi, trả lời từ chối an toàn; không bịa thông tin.
"""

import os

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

SAFE_REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."

SYSTEM_PROMPT = """Trả lời bằng tiếng Việt chỉ từ context được cung cấp.
Mỗi khẳng định thực tế phải có citation dạng [Document N].
Nếu context không đủ evidence, hãy trả lời đúng câu: Tôi không thể xác minh thông tin này từ nguồn hiện có."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa các chunk quan trọng về đầu và cuối context."""
    if len(chunks) <= 2:
        return list(chunks)

    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có nhãn tiêu đề và nguồn để đối chiếu citation."""
    parts = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk["metadata"]
        parts.append(
            f"[Document {index} | Title: {metadata['title']} | "
            f"Source: {metadata['source']}]\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    if LLM_PROVIDER == "openai":
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model=LLM_MODEL or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
            timeout=30.0,
        )
        return response.choices[0].message.content or ""

    if LLM_PROVIDER == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options=types.HttpOptions(timeout=30_000),
        )
        response = client.models.generate_content(
            model=LLM_MODEL or "gemini-2.0-flash",
            contents=f"{system_prompt}\n\n{user_message}",
            config=types.GenerateContentConfig(
                temperature=TEMPERATURE,
                top_p=TOP_P,
            ),
        )
        return response.text or ""

    if LLM_PROVIDER == "anthropic":
        import anthropic

        client = anthropic.Anthropic(timeout=30.0)
        response = client.messages.create(
            model=LLM_MODEL or "claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Sinh GenerationResult từ context đã truy xuất."""
    try:
        chunks = retrieve(query, top_k=top_k)
    except Exception:
        chunks = []

    if not chunks:
        return {
            "answer": SAFE_REFUSAL,
            "sources": [],
            "retrieval_source": "none",
        }

    context = format_context(reorder_for_llm(chunks))
    user_message = f"Context:\n{context}\n\nCâu hỏi: {query}"

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception:
        return {
            "answer": SAFE_REFUSAL,
            "sources": [],
            "retrieval_source": "none",
        }

    if not answer.strip() or answer.strip() == SAFE_REFUSAL:
        return {
            "answer": SAFE_REFUSAL,
            "sources": [],
            "retrieval_source": "none",
        }

    method = chunks[0]["retrieval_method"]
    retrieval_source = method if method in {"hybrid", "pageindex"} else "hybrid"
    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_source,
    }


if __name__ == "__main__":
    print(generate_with_citation("test query"))
