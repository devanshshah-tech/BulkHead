from .schema import Citation

SYSTEM_INSTRUCTION = (
    "You are a grounded assistant. Answer the question using ONLY the numbered context"
    " chunks below. Cite chunks inline as [n]. If the context does not contain the"
    " answer, say so explicitly. Never invent facts."
)


def build_prompt(question: str, citations: list[Citation]) -> str:
    parts = [SYSTEM_INSTRUCTION, "", "Context:"]
    for i, c in enumerate(citations, start=1):
        parts.append(f"[{i}] (source: {c.source}) {c.content}")
    parts.extend(["", f"Question: {question}", "Answer:"])
    return "\n".join(parts)
