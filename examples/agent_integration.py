"""
Example integration of NeuralOpenClaw into OpenClaw agent.
This shows the main pattern to implement.
"""
import asyncio
from src import (
    NeuralMemoryLayer,
    SmartMemoryRouter,
    ContextAssembler,
    ContextBlock,
    SessionCompressor,
    should_cache_tool,
    get_cache_ttl,
    get_confidence_threshold,
)


class OpenClawAgent:
    def __init__(self, project_name: str):
        # Memory components
        self.neural_memory = NeuralMemoryLayer(project_name)
        self.router = SmartMemoryRouter()
        self.assembler = ContextAssembler(max_context_tokens=1500)
        self.compressor = SessionCompressor(
            neural_memory=self.neural_memory,
            llm_call_fn=self._llm_call,  # Point to your LLM call
        )
        self.messages = []

    async def initialize(self):
        await self.neural_memory.initialize()

    # ─── BEFORE TOOL CALL: check cache ──────────────────────────

    async def smart_tool_call(self, tool_name: str, args: dict) -> str:
        """
        Smart wrapper for tool calls.
        1. Check NeuralMemory cache first
        2. If miss → call real tool
        3. Cache result for later use
        """
        # Step 1: Check if should cache
        if should_cache_tool(tool_name):
            threshold = get_confidence_threshold(tool_name)
            cached = await self.neural_memory.get_cached_tool_result(
                tool_name, args, min_confidence=threshold
            )
            if cached:
                # Cache HIT — save 1 tool call
                return cached

        # Step 2: Cache MISS → call real tool
        result = await self._actual_tool_call(tool_name, args)

        # Step 3: Save to cache
        ttl = get_cache_ttl(tool_name)
        if ttl > 0:
            await self.neural_memory.cache_tool_result(
                tool_name, args, result, ttl_hours=ttl
            )

        return result

    # ─── BEFORE LLM CALL: build optimal context ─────────────────

    async def build_context_for_task(self, task: str) -> str:
        """
        Build optimal token context for task.
        Instead of dumping full history, only inject:
        - Relevant episodic memories from NeuralMemory
        - Recent session messages (compressed)
        """
        blocks = []

        # Priority 1: Neural memory context for this task
        neural_ctx = await self.neural_memory.get_task_context(
            task, max_tokens_approx=800
        )
        if neural_ctx:
            blocks.append(
                ContextBlock(
                    source="neural",
                    content=neural_ctx,
                    priority=1,
                    token_estimate=self.assembler.estimate_tokens(neural_ctx),
                )
            )

        # Priority 2: Traditional memory (if available)
        # traditional_ctx = await self.traditional_memory.search(task)
        # blocks.append(ContextBlock(source="traditional", content=traditional_ctx, priority=2, ...))

        return self.assembler.assemble(blocks)

    # ─── AFTER SESSION: compress if too long ────────────────────

    async def add_message(self, role: str, content: str):
        """Add message and auto-compress if needed."""
        self.messages.append({"role": role, "content": content})
        
        # Auto-compress when messages exceed threshold
        self.messages = await self.compressor.maybe_compress(self.messages)

    # ─── STORE IMPORTANT EVENTS ─────────────────────────────────

    async def on_decision_made(self, decision: str, reason: str = ""):
        """Call whenever agent/user makes important decision."""
        await self.neural_memory.store_decision(decision, context=reason)

    async def on_error_resolved(self, error: str, solution: str):
        """Call when bug is fixed — save as insight."""
        await self.neural_memory.store_insight(
            f"Error: {error} → Solution: {solution}"
        )

    async def on_task_completed(self, task: str, outcome: str):
        """Call when task is completed — save to episodic memory."""
        await self.neural_memory.store_context(
            f"Completed: {task} | Outcome: {outcome}",
            expires_hours=72,
        )

    # ─── PRIVATE ────────────────────────────────────────────────

    async def _actual_tool_call(self, tool_name: str, args: dict) -> str:
        """Call real OpenClaw tool — implement according to existing codebase."""
        raise NotImplementedError("Connect to existing OpenClaw tool system")

    async def _llm_call(self, prompt: str) -> str:
        """Call LLM — implement according to existing codebase."""
        raise NotImplementedError("Connect to existing OpenClaw LLM client")


# Example usage
async def main():
    agent = OpenClawAgent(project_name="my-project")
    await agent.initialize()

    # Store a decision
    await agent.on_decision_made(
        "Using SQLite for episodic memory",
        "Because it's lightweight and portable"
    )

    # Build context for a task
    context = await agent.build_context_for_task("Implement feature X")
    print(f"Context: {context}")

    # Smart tool call with caching
    result = await agent.smart_tool_call(
        "read_file",
        {"path": "config.json"}
    )
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
