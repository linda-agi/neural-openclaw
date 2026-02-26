"""
ContextAssembler: Aggregate context from multiple sources, optimize token budget.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContextBlock:
    source: str  # "neural", "traditional", "system"
    content: str
    priority: int  # 1=highest
    token_estimate: int  # estimated number of tokens


class ContextAssembler:
    """
    Gather context from multiple sources and cut by token budget.
    Priority: System > Neural (high confidence) > Traditional > Neural (low confidence)
    """

    def __init__(self, max_context_tokens: int = 1500):
        self.max_context_tokens = max_context_tokens

    def assemble(self, blocks: list[ContextBlock]) -> str:
        """
        Sort blocks by priority, cut when reaching token budget.

        Returns:
            Context string optimized, ready to inject into prompt.
        """
        # Sort by priority (1 = highest)
        sorted_blocks = sorted(blocks, key=lambda b: b.priority)
        
        result_parts = []
        total_tokens = 0

        for block in sorted_blocks:
            if total_tokens + block.token_estimate > self.max_context_tokens:
                remaining = self.max_context_tokens - total_tokens
                if remaining > 50:  # Only add if enough space left
                    chars = remaining * 4
                    result_parts.append(
                        f"[{block.source.upper()}] {block.content[:chars]}... [truncated]"
                    )
                break

            result_parts.append(f"[{block.source.upper()}] {block.content}")
            total_tokens += block.token_estimate

        return " ".join(result_parts)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate number of tokens (~4 chars = 1 token for English/code)."""
        return max(1, len(text) // 4)
