from rag.knowledge_base import PERSONA_KNOWLEDGE


def retrieve(query: str, long_term_summary: str = "") -> str:
    keywords = ("喜欢", "讨厌", "害怕", "心情", "情绪")

    if any(keyword in query for keyword in keywords) and long_term_summary.strip():
        return f"{PERSONA_KNOWLEDGE}\n\n用户长期记忆参考：\n{long_term_summary}"

    return PERSONA_KNOWLEDGE
