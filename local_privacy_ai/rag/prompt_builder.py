from __future__ import annotations


def build_prompt(query: str, sources: list[dict]) -> str:
    context = "\n\n".join(
        f"Source {index + 1}:\n{source['text']}" for index, source in enumerate(sources)
    )
    if not context:
        context = "No relevant context was retrieved."

    return (
        "You are a local privacy-preserving assistant for Home Assistant data.\n"
        "Answer only from the provided context. If the context is not enough, say that the "
        "available data is insufficient. Keep the answer concise and mention uncertainty.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer:"
    )

