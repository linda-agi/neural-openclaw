"""
Tests for NeuralOpenClaw CLI and core modules.
"""
import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    NeuralMemoryLayer,
    SmartMemoryRouter,
    ContextAssembler,
    ContextBlock,
    MemorySource,
    should_cache_tool,
    get_cache_ttl,
    get_confidence_threshold,
)


class TestSmartMemoryRouter:
    """Tests for SmartMemoryRouter."""

    def setup_method(self):
        self.router = SmartMemoryRouter()

    def test_route_decision_query(self):
        """Test routing of decision/causal queries."""
        result = self.router.route("Why did we choose SQLite?")
        assert result.source == MemorySource.NEURAL
        assert "Causal/decision" in result.reason

    def test_route_causal_query(self):
        """Test routing of causal queries."""
        result = self.router.route("What caused this bug?")
        assert result.source == MemorySource.NEURAL

    def test_route_tool_query(self):
        """Test routing of real-time queries."""
        result = self.router.route("What is the current file content?")
        assert result.source == MemorySource.TOOL_CALL
        assert result.confidence_threshold == 0.85

    def test_route_document_query(self):
        """Test routing of document queries."""
        result = self.router.route("Show me the API documentation")
        assert result.source == MemorySource.TRADITIONAL

    def test_route_general_query(self):
        """Test routing of general queries."""
        result = self.router.route("Tell me about the project")
        assert result.source == MemorySource.BOTH


class TestContextAssembler:
    """Tests for ContextAssembler."""

    def setup_method(self):
        self.assembler = ContextAssembler(max_context_tokens=100)

    def test_assemble_single_block(self):
        """Test assembling a single context block."""
        blocks = [
            ContextBlock(
                source="neural",
                content="Test content",
                priority=1,
                token_estimate=10
            )
        ]
        result = self.assembler.assemble(blocks)
        assert "[NEURAL]" in result
        assert "Test content" in result

    def test_assemble_multiple_blocks_priority(self):
        """Test that blocks are sorted by priority."""
        blocks = [
            ContextBlock(source="low", content="Low priority", priority=3, token_estimate=10),
            ContextBlock(source="high", content="High priority", priority=1, token_estimate=10),
            ContextBlock(source="mid", content="Mid priority", priority=2, token_estimate=10),
        ]
        result = self.assembler.assemble(blocks)
        # High priority should come first
        assert result.index("[HIGH]") < result.index("[MID]") < result.index("[LOW]")

    def test_assemble_truncation(self):
        """Test that content is truncated when exceeding token budget."""
        blocks = [
            ContextBlock(
                source="neural",
                content="A" * 1000,  # Very long content
                priority=1,
                token_estimate=250  # More than budget
            )
        ]
        result = self.assembler.assemble(blocks)
        assert "[truncated]" in result or len(result) < 500

    def test_estimate_tokens(self):
        """Test token estimation."""
        text = "This is a test sentence with 8 words"
        estimate = self.assembler.estimate_tokens(text)
        assert estimate > 0
        assert isinstance(estimate, int)


class TestCachePolicy:
    """Tests for cache policy functions."""

    def test_should_cache_tool_true(self):
        """Test tools that should be cached."""
        assert should_cache_tool("read_file") is True
        assert should_cache_tool("search_web") is True

    def test_should_cache_tool_false(self):
        """Test tools that should NOT be cached."""
        assert should_cache_tool("git_status") is False
        assert should_cache_tool("run_tests") is False
        assert should_cache_tool("write_file") is False

    def test_get_cache_ttl(self):
        """Test TTL retrieval."""
        assert get_cache_ttl("read_file") == 1
        assert get_cache_ttl("search_web") == 4
        assert get_cache_ttl("git_status") == 0  # No cache

    def test_get_confidence_threshold(self):
        """Test confidence threshold retrieval."""
        assert get_confidence_threshold("read_file") == 0.90
        assert get_confidence_threshold("search_web") == 0.75
        assert get_confidence_threshold("unknown_tool") == 0.80  # Default


class TestNeuralMemoryLayer:
    """Tests for NeuralMemoryLayer."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test memory layer initialization."""
        memory = NeuralMemoryLayer("test-project")
        await memory.initialize()
        assert memory._initialized is True

    @pytest.mark.asyncio
    async def test_store_decision_mock(self):
        """Test storing decision in mock mode."""
        memory = NeuralMemoryLayer("test-project")
        await memory.initialize()
        # Should not raise error in mock mode
        await memory.store_decision("Test decision", "Test context")

    @pytest.mark.asyncio
    async def test_recall_mock(self):
        """Test recall in mock mode."""
        memory = NeuralMemoryLayer("test-project")
        await memory.initialize()
        result = await memory.recall("Test query")
        assert result is None  # Mock mode returns None

    @pytest.mark.asyncio
    async def test_get_task_context_mock(self):
        """Test task context in mock mode."""
        memory = NeuralMemoryLayer("test-project")
        await memory.initialize()
        result = await memory.get_task_context("Test task")
        assert result == ""  # Mock mode returns empty string


class TestCLI:
    """Tests for CLI interface."""

    def test_cli_help(self):
        """Test CLI help command."""
        import subprocess
        result = subprocess.run(
            ["python3", "nocl.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "decision" in result.stdout
        assert "recall" in result.stdout
        assert "task" in result.stdout

    def test_cli_init(self):
        """Test CLI init command."""
        import subprocess
        result = subprocess.run(
            ["python3", "nocl.py", "init", "--project", "test-cli"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "Initialized" in result.stdout

    def test_cli_decision(self):
        """Test CLI decision command."""
        import subprocess
        result = subprocess.run(
            ["python3", "nocl.py", "--project", "test-cli", "decision", "Test", "--context", "CI"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode == 0
        assert "Decision stored" in result.stdout
