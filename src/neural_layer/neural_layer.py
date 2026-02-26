"""
NeuralMemory wrapper for OpenClaw.
Provides unified interface: store, recall, cache tool results.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any

try:
    from neural_memory import Brain
    from neural_memory.engine.encoder import MemoryEncoder
    from neural_memory.engine.retrieval import ReflexPipeline
    from neural_memory.storage.sqlite_store import SQLiteStorage
    NEURAL_MEMORY_AVAILABLE = True
except ImportError:
    NEURAL_MEMORY_AVAILABLE = False
    Brain = None
    MemoryEncoder = None
    ReflexPipeline = None
    SQLiteStorage = None

logger = logging.getLogger(__name__)


class NeuralMemoryLayer:
    """
    NeuralMemory layer integrated into OpenClaw.
    Responsible for:
    - Storing and recalling episodic memories (decisions, context, patterns)
    - Caching tool call results to avoid redundant calls
    - Compressing session history into episodic memories
    """

    def __init__(self, project_name: str, db_path: str | None = None):
        self.project_name = project_name
        self.db_path = db_path or f".openclaw/{project_name}_memory.db"
        self._storage: SQLiteStorage | None = None
        self._brain: Brain | None = None
        self._encoder: MemoryEncoder | None = None
        self._pipeline: ReflexPipeline | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize async — call once when agent starts."""
        if self._initialized:
            return

        if not NEURAL_MEMORY_AVAILABLE:
            logger.warning("NeuralMemory not installed. Running in mock mode.")
            self._initialized = True
            return

        self._storage = SQLiteStorage(self.db_path)
        
        # Load brain if exists, create new if not
        try:
            self._brain = await self._storage.load_brain_by_name(self.project_name)
            logger.info(f"Loaded existing brain: {self.project_name}")
        except Exception:
            self._brain = Brain.create(self.project_name)
            await self._storage.save_brain(self._brain)
            logger.info(f"Created new brain: {self.project_name}")

        self._storage.set_brain(self._brain.id)
        self._encoder = MemoryEncoder(self._storage, self._brain.config)
        self._pipeline = ReflexPipeline(self._storage, self._brain.config)
        self._initialized = True

    # ─── Store Methods ──────────────────────────────────────────

    async def store_decision(self, content: str, context: str = "") -> None:
        """
        Store an architectural/technical decision.
        Use for: technology selection, design patterns, config choices.
        Does not expire — decisions are important long-term.
        """
        await self._ensure_initialized()
        if not NEURAL_MEMORY_AVAILABLE:
            logger.info(f"[MOCK] Would store decision: {content[:80]}")
            return
        full_content = f"[DECISION] {content}"
        if context:
            full_content += f" | Context: {context}"
        await self._encoder.encode(full_content, memory_type="decision")
        logger.debug(f"Stored decision: {content[:80]}")

    async def store_context(self, content: str, expires_hours: int = 24) -> None:
        """
        Store temporary context of current session.
        Use for: current task, workflow state.
        Auto-expires after expires_hours.
        """
        await self._ensure_initialized()
        if not NEURAL_MEMORY_AVAILABLE:
            logger.info(f"[MOCK] Would store context: {content[:80]}")
            return
        await self._encoder.encode(
            content,
            memory_type="context",
            expires=expires_hours,
        )

    async def store_insight(self, content: str) -> None:
        """
        Store pattern/lesson learned from errors or successes.
        Use for: bug patterns, optimization insights, gotchas.
        """
        await self._ensure_initialized()
        if not NEURAL_MEMORY_AVAILABLE:
            logger.info(f"[MOCK] Would store insight: {content[:80]}")
            return
        await self._encoder.encode(
            f"[INSIGHT] {content}",
            memory_type="insight",
        )

    async def store_fact(self, content: str, expires_hours: int | None = None) -> None:
        """Store short-term or long-term fact."""
        await self._ensure_initialized()
        if not NEURAL_MEMORY_AVAILABLE:
            logger.info(f"[MOCK] Would store fact: {content[:80]}")
            return
        await self._encoder.encode(
            content,
            memory_type="fact",
            expires=expires_hours,
        )

    # ─── Tool Result Cache ───────────────────────────────────────

    async def cache_tool_result(
        self,
        tool_name: str,
        args: dict[str, Any] | str,
        result: str,
        ttl_hours: int = 1,
        max_result_chars: int = 500,
    ) -> None:
        """
        Cache result of a tool call.

        Args:
            tool_name: Tool name (e.g., "read_file", "search_web")
            args: Arguments passed to tool
            result: Result returned (will be trimmed if too long)
            ttl_hours: Time-to-live for cache
            max_result_chars: Max length of result to store
        """
        await self._ensure_initialized()
        if not NEURAL_MEMORY_AVAILABLE:
            logger.info(f"[MOCK] Would cache tool result: {tool_name}")
            return
        args_str = json.dumps(args) if isinstance(args, dict) else str(args)
        
        result_trimmed = result[:max_result_chars]
        if len(result) > max_result_chars:
            result_trimmed += "... [trimmed]"

        content = f"[TOOL_CACHE] {tool_name}({args_str}) → {result_trimmed}"
        cache_key = self._make_cache_key(tool_name, args_str)
        
        await self._encoder.encode(
            content,
            memory_type="fact",
            expires=ttl_hours,
            metadata={"cache_key": cache_key, "tool": tool_name},
        )

    async def get_cached_tool_result(
        self,
        tool_name: str,
        args: dict[str, Any] | str,
        min_confidence: float = 0.80,
    ) -> str | None:
        """
        Check cache before calling real tool.

        Returns:
            Cached result string if available and confidence is high enough.
            None if real tool call is needed.
        """
        await self._ensure_initialized()
        if not NEURAL_MEMORY_AVAILABLE:
            logger.info(f"[MOCK] Would check cache for: {tool_name}")
            return None
        args_str = json.dumps(args) if isinstance(args, dict) else str(args)
        query = f"{tool_name} {args_str}"
        
        result = await self._pipeline.query(query)
        
        if result and result.confidence >= min_confidence:
            # Only return if result is actually tool cache (not wrong recall)
            if "[TOOL_CACHE]" in result.context and tool_name in result.context:
                logger.debug(f"Cache hit for {tool_name}: confidence={result.confidence:.2f}")
                return result.context
        
        return None

    # ─── Recall Methods ─────────────────────────────────────────

    async def recall(
        self,
        query: str,
        min_confidence: float = 0.5,
        depth: int = 2,
    ) -> str | None:
        """
        Recall information related to query.

        Args:
            query: Question or keyword to remember
            min_confidence: Minimum confidence threshold (0-1)
            depth: Number of hops for graph traversal (1=close, 3=deep)

        Returns:
            Context string if found, None otherwise.
        """
        await self._ensure_initialized()
        if not NEURAL_MEMORY_AVAILABLE:
            logger.info(f"[MOCK] Would recall: {query}")
            return None
        result = await self._pipeline.query(query, depth=depth)
        
        if result and result.confidence >= min_confidence:
            return result.context
        
        return None

    async def get_task_context(
        self,
        task_description: str,
        max_tokens_approx: int = 500,
    ) -> str:
        """
        Get optimal token context for a specific task.
        Instead of injecting full project context, only get most relevant memories.

        Args:
            task_description: Description of current task
            max_tokens_approx: Estimated token limit (~4 chars/token)

        Returns:
            Context string filtered and trimmed.
        """
        await self._ensure_initialized()
        if not NEURAL_MEMORY_AVAILABLE:
            logger.info(f"[MOCK] Would get task context: {task_description[:50]}")
            return ""
        result = await self._pipeline.query(task_description, depth=2)
        
        if not result or not result.context:
            return ""

        # Trim by token budget
        max_chars = max_tokens_approx * 4
        context = result.context[:max_chars]
        
        return f"[Memory Context] {context} [/Memory Context]"

    # ─── Helpers ────────────────────────────────────────────────

    async def _ensure_initialized(self) -> None:
        if not self._initialized:
            await self.initialize()

    def _make_cache_key(self, tool_name: str, args_str: str) -> str:
        raw = f"{tool_name}:{args_str}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]
