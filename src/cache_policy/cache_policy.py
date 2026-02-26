"""
Define TTL and freshness policy for each type of tool/memory.
"""
from __future__ import annotations

# TTL (hours) for each type of tool result
TOOL_CACHE_TTL: dict[str, int] = {
    # File system — changes frequently, short TTL
    "read_file": 1,
    "list_directory": 1,
    "get_file_content": 1,
    
    # Git — relatively stable within session
    "git_status": 0,  # DO NOT cache (changes continuously)
    "git_log": 2,
    "git_diff": 0,  # DO NOT cache
    
    # Web / API — moderate cache
    "search_web": 4,
    "fetch_url": 2,
    "call_api": 1,
    
    # Database queries — depends on use case
    "query_db": 0,  # DO NOT cache by default (sensitive data)
    
    # Package/dependency info — stable
    "check_package": 24,
    "get_dependencies": 12,
    
    # Test results — short cache
    "run_tests": 0,  # DO NOT cache (need fresh)
    "check_lint": 1,
}

# Types of tools that should NOT be cached regardless of setting
NO_CACHE_TOOLS = {
    "git_status",
    "git_diff",
    "run_tests",
    "query_db",
    "write_file",
    "execute_command",
}

# Confidence threshold to use cache (by tool type)
CACHE_CONFIDENCE: dict[str, float] = {
    "read_file": 0.90,  # Need very sure because content can change
    "search_web": 0.75,
    "fetch_url": 0.80,
    "get_dependencies": 0.85,
    "default": 0.80,
}


def should_cache_tool(tool_name: str) -> bool:
    """Check if this tool should be cached."""
    return tool_name not in NO_CACHE_TOOLS and tool_name in TOOL_CACHE_TTL


def get_cache_ttl(tool_name: str) -> int:
    """Get TTL (hours) for tool. 0 = do not cache."""
    return TOOL_CACHE_TTL.get(tool_name, 0)


def get_confidence_threshold(tool_name: str) -> float:
    """Get confidence threshold to accept cache."""
    return CACHE_CONFIDENCE.get(tool_name, CACHE_CONFIDENCE["default"])
