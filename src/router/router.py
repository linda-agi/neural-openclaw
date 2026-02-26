"""
SmartMemoryRouter: Decide whether to query NeuralMemory or Traditional Memory.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class MemorySource(Enum):
    NEURAL = "neural"
    TRADITIONAL = "traditional"
    BOTH = "both"
    TOOL_CALL = "tool_call"  # Not in memory, need real tool call


@dataclass
class RoutingDecision:
    source: MemorySource
    reason: str
    confidence_threshold: float = 0.7


# Patterns to recognize query types
_DECISION_PATTERNS = re.compile(
    r"\b(why|reason|decided|chose|picked|selected|because)\b",
    re.IGNORECASE
)

_CAUSAL_PATTERNS = re.compile(
    r"\b(caused|led to|resulted|consequence|impact|affect)\b",
    re.IGNORECASE
)

_TOOL_PATTERNS = re.compile(
    r"\b(current|latest|now|today|file content|output of|result of)\b",
    re.IGNORECASE
)

_DOCUMENT_PATTERNS = re.compile(
    r"\b(documentation|readme|spec|api reference|how to use)\b",
    re.IGNORECASE
)


class SmartMemoryRouter:
    """
    Route query to correct memory backend to optimize tokens.
    """

    def route(self, query: str) -> RoutingDecision:
        """
        Analyze query and decide appropriate memory source.
        """
        # Causal / decision queries → NeuralMemory (strength: causal traversal)
        if _DECISION_PATTERNS.search(query) or _CAUSAL_PATTERNS.search(query):
            return RoutingDecision(
                source=MemorySource.NEURAL,
                reason="Causal/decision query → NeuralMemory graph traversal",
                confidence_threshold=0.65,
            )

        # Real-time / current state → need real tool call
        if _TOOL_PATTERNS.search(query):
            return RoutingDecision(
                source=MemorySource.TOOL_CALL,
                reason="Real-time query → check cache first, fallback to tool",
                confidence_threshold=0.85,  # Need higher confidence for fresh data
            )

        # Document / reference queries → Traditional RAG
        if _DOCUMENT_PATTERNS.search(query):
            return RoutingDecision(
                source=MemorySource.TRADITIONAL,
                reason="Document query → Traditional RAG",
            )

        # Default: try NeuralMemory first, fallback to Traditional
        return RoutingDecision(
            source=MemorySource.BOTH,
            reason="General query → try both sources",
            confidence_threshold=0.6,
        )
