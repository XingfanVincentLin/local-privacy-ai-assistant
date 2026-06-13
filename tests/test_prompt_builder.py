from __future__ import annotations

from local_privacy_ai.rag.prompt_builder import build_prompt


def test_build_prompt_instructs_model_to_use_context_only() -> None:
    prompt = build_prompt(
        "Was motion detected?",
        [{"text": "At 22:15, Living Room Motion was active or detected motion."}],
    )

    assert "Answer only from the provided context" in prompt
    assert "Living Room Motion" in prompt
    assert "Was motion detected?" in prompt

