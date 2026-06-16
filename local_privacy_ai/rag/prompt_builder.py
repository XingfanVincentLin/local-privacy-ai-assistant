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
        "available data is insufficient. Keep the answer concise and mention uncertainty only "
        "when the context is actually missing or ambiguous. Include the timestamp when the "
        "context gives one for the requested value or state.\n\n"
        "If the question asks for the latest, current, newest, or most recent value, compare "
        "the timestamps in the retrieved sources and use the newest relevant timestamp. Do not "
        "answer from an older event when a newer relevant event is present.\n\n"
        "For comparison questions, compare only the requested values and give a clear conclusion. "
        "Do not add caveats that contradict the numeric comparison shown in the context.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer:"
    )
