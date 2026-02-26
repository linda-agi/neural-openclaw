"""
SessionCompressor: Summarize conversation history → episodic memories.
Instead of keeping full history (expensive in tokens), compress periodically into NeuralMemory.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..neural_layer.neural_layer import NeuralMemoryLayer

logger = logging.getLogger(__name__)

# Number of messages to keep after compress (recent window)
RECENT_WINDOW = 5

# Compress when number of messages exceeds this threshold
COMPRESS_THRESHOLD = 20


class SessionCompressor:
    """
    Automatically compress session history when too long.
    
    Flow:
    1. Monitor messages in session
    2. When exceeding COMPRESS_THRESHOLD → summarize via LLM
    3. Save summary into NeuralMemory
    4. Keep only RECENT_WINDOW most recent messages
    """

    def __init__(self, neural_memory: "NeuralMemoryLayer", llm_call_fn):
        """
        Args:
            neural_memory: Instance of NeuralMemoryLayer
            llm_call_fn: Async function to call LLM for summarization
                Signature: async (prompt: str) -> str
        """
        self.memory = neural_memory
        self.llm_call = llm_call_fn

    async def maybe_compress(
        self,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        If messages are too long, compress and return reduced list.
        If not needed, return original messages unchanged.

        Args:
            messages: List of messages in format {"role": ..., "content": ...}

        Returns:
            List of messages after compression (or original if not needed).
        """
        if len(messages) < COMPRESS_THRESHOLD:
            return messages

        logger.info(
            f"Compressing session: {len(messages)} messages → {RECENT_WINDOW} recent"
        )

        # Part to compress (exclude last RECENT_WINDOW)
        to_compress = messages[:-RECENT_WINDOW]
        recent = messages[-RECENT_WINDOW:]

        # Summarize using LLM
        summary = await self._summarize(to_compress)

        # Save summary into NeuralMemory
        await self.memory.store_context(
            content=f"[SESSION_SUMMARY] {summary}",
            expires_hours=48,
        )

        logger.info(
            f"Compressed {len(to_compress)} messages into episodic memory. "
            f"Kept {len(recent)} recent messages."
        )

        # Return only recent messages (save ~80% tokens)
        return recent

    async def _summarize(self, messages: list[dict[str, Any]]) -> str:
        """Use LLM to summarize conversation into episodic memory."""
        # Format messages into text
        conversation_text = " ".join(
            f"{m['role'].upper()}: {str(m.get('content', ''))[:300]}"
            for m in messages
        )

        prompt = f"""Summarize the key decisions, findings, and progress from this conversation segment. Focus on: what was decided, what was learned, what was completed, what's still pending. Be concise — max 3-4 sentences.

Conversation: {conversation_text}

Summary:"""

        return await self.llm_call(prompt)
