#!/usr/bin/env python3
"""
NeuralOpenClaw CLI - Command-line interface for NeuralMemory operations.
Similar to qmd CLI but optimized for episodic memory and token-efficient AI interactions.

Usage:
    nocl decision "content" --context "reason"
    nocl context "content" --expires 24
    nocl insight "content"
    nocl fact "content" --expires 12
    nocl cache tool_name args_json result --ttl 1
    nocl recall "query" --confidence 0.7 --depth 2
    nocl task "task description" --max-tokens 500
    nocl status
    nocl init --project my-project
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import (
    NeuralMemoryLayer,
    SmartMemoryRouter,
    ContextAssembler,
    MemorySource,
)


class NeuralOpenClawCLI:
    """CLI interface for NeuralOpenClaw operations."""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.memory = NeuralMemoryLayer(project_name)

    async def initialize(self):
        await self.memory.initialize()

    # ─── Store Commands ──────────────────────────────────────────

    async def store_decision(self, content: str, context: str = ""):
        """Store architectural/technical decision."""
        await self.memory.store_decision(content, context)
        print(f"✅ Decision stored: {content[:80]}")

    async def store_context(self, content: str, expires_hours: int = 24):
        """Store temporary session context."""
        await self.memory.store_context(content, expires_hours)
        print(f"✅ Context stored (expires in {expires_hours}h): {content[:80]}")

    async def store_insight(self, content: str):
        """Store pattern/lesson learned."""
        await self.memory.store_insight(content)
        print(f"✅ Insight stored: {content[:80]}")

    async def store_fact(self, content: str, expires_hours: int | None = None):
        """Store fact (short-term or long-term)."""
        await self.memory.store_fact(content, expires_hours)
        expiry = f" (expires in {expires_hours}h)" if expires_hours else " (permanent)"
        print(f"✅ Fact stored{expiry}: {content[:80]}")

    # ─── Cache Commands ──────────────────────────────────────────

    async def cache_tool_result(
        self,
        tool_name: str,
        args_json: str,
        result: str,
        ttl_hours: int = 1,
    ):
        """Cache tool result."""
        args = json.loads(args_json)
        await self.memory.cache_tool_result(
            tool_name, args, result, ttl_hours=ttl_hours
        )
        print(f"✅ Tool result cached: {tool_name} (TTL: {ttl_hours}h)")

    # ─── Recall Commands ─────────────────────────────────────────

    async def recall(self, query: str, min_confidence: float = 0.5, depth: int = 2):
        """Recall information related to query."""
        result = await self.memory.recall(query, min_confidence, depth)
        if result:
            print(f"🧠 Recall result (confidence >= {min_confidence}):")
            print("-" * 60)
            print(result)
            print("-" * 60)
        else:
            print(f"❌ No relevant memory found (confidence >= {min_confidence})")

    async def get_task_context(self, task_description: str, max_tokens: int = 500):
        """Get optimal token context for a task."""
        context = await self.memory.get_task_context(task_description, max_tokens)
        if context:
            print(f"📋 Task context for: {task_description[:50]}")
            print("-" * 60)
            print(context)
            print("-" * 60)
        else:
            print("❌ No relevant context found")

    # ─── Status Commands ─────────────────────────────────────────

    async def show_status(self):
        """Show memory status."""
        print(f"🧠 NeuralOpenClaw Status")
        print(f"Project: {self.project_name}")
        print(f"Database: {self.memory.db_path}")
        print(f"Initialized: {self.memory._initialized}")
        
        # Try to get brain info
        if self.memory._brain:
            print(f"Brain ID: {self.memory._brain.id}")
            print(f"Brain Name: {self.memory._brain.name}")
            if hasattr(self.memory._brain, 'config'):
                print(f"Config: {self.memory._brain.config}")


def main():
    parser = argparse.ArgumentParser(
        description="NeuralOpenClaw CLI - Episodic memory for OpenClaw",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nocl init --project my-project
  nocl decision "Using SQLite" --context "Lightweight and portable"
  nocl context "Working on feature X" --expires 12
  nocl insight "Bug fixed: race condition in async code"
  nocl recall "Why did we choose SQLite?"
  nocl task "Implement caching layer" --max-tokens 800
  nocl cache read_file '{"path": "config.json"}' '{"key": "value"}' --ttl 2
  nocl status
        """
    )

    parser.add_argument(
        "--project", "-p",
        default="openclaw",
        help="Project name (default: openclaw)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize memory for project")
    init_parser.add_argument("--project", required=True, help="Project name")

    # Decision command
    decision_parser = subparsers.add_parser("decision", help="Store a decision")
    decision_parser.add_argument("content", help="Decision content")
    decision_parser.add_argument("--context", "-c", default="", help="Context/reason")

    # Context command
    context_parser = subparsers.add_parser("context", help="Store session context")
    context_parser.add_argument("content", help="Context content")
    context_parser.add_argument("--expires", "-e", type=int, default=24, help="Expires in hours")

    # Insight command
    insight_parser = subparsers.add_parser("insight", help="Store insight/lesson")
    insight_parser.add_argument("content", help="Insight content")

    # Fact command
    fact_parser = subparsers.add_parser("fact", help="Store fact")
    fact_parser.add_argument("content", help="Fact content")
    fact_parser.add_argument("--expires", "-e", type=int, help="Expires in hours (optional)")

    # Cache command
    cache_parser = subparsers.add_parser("cache", help="Cache tool result")
    cache_parser.add_argument("tool", help="Tool name")
    cache_parser.add_argument("args", help="Arguments as JSON")
    cache_parser.add_argument("result", help="Tool result")
    cache_parser.add_argument("--ttl", "-t", type=int, default=1, help="TTL in hours")

    # Recall command
    recall_parser = subparsers.add_parser("recall", help="Recall information")
    recall_parser.add_argument("query", help="Query string")
    recall_parser.add_argument("--confidence", "-c", type=float, default=0.5, help="Min confidence")
    recall_parser.add_argument("--depth", "-d", type=int, default=2, help="Graph depth")

    # Task context command
    task_parser = subparsers.add_parser("task", help="Get task context")
    task_parser.add_argument("description", help="Task description")
    task_parser.add_argument("--max-tokens", "-t", type=int, default=500, help="Max tokens")

    # Status command
    subparsers.add_parser("status", help="Show memory status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Handle init command separately
    if args.command == "init":
        print(f"🚀 Initializing NeuralOpenClaw for project: {args.project}")
        # Just create the database file
        memory = NeuralMemoryLayer(args.project)
        asyncio.run(memory.initialize())
        print(f"✅ Initialized at: {memory.db_path}")
        sys.exit(0)

    # Create CLI instance
    cli = NeuralOpenClawCLI(args.project)
    
    # Run command
    async def run_command():
        await cli.initialize()
        
        if args.command == "decision":
            await cli.store_decision(args.content, args.context)
        elif args.command == "context":
            await cli.store_context(args.content, args.expires)
        elif args.command == "insight":
            await cli.store_insight(args.content)
        elif args.command == "fact":
            await cli.store_fact(args.content, args.expires)
        elif args.command == "cache":
            await cli.cache_tool_result(args.tool, args.args, args.result, args.ttl)
        elif args.command == "recall":
            await cli.recall(args.query, args.confidence, args.depth)
        elif args.command == "task":
            await cli.get_task_context(args.description, args.max_tokens)
        elif args.command == "status":
            await cli.show_status()

    asyncio.run(run_command())


if __name__ == "__main__":
    main()
