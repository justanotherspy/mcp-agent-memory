#!/usr/bin/env python3
"""
Shared Memory MCP Server
========================

An MCP server that provides a shared memory scratch space for multiple AI agents
to communicate. Each agent can add memory entries (max 200 words) and read all
entries in chronological order. Perfect for enabling multi-agent conversations
through message passing.

Usage:
    python shared_memory_mcp.py
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime, timezone
import json
import os
from pathlib import Path

# Constants
CHARACTER_LIMIT = 25000  # Maximum response size in characters
MAX_WORDS_PER_ENTRY = 200  # Maximum words per memory entry
MEMORY_FILE = Path.home() / ".shared_memory_mcp" / "memory.json"

# Initialize FastMCP server
mcp = FastMCP("shared_memory_mcp")


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class MemoryEntry(BaseModel):
    """Model representing a single memory entry."""
    timestamp: str
    agent_name: str
    content: str
    word_count: int


# Utility Functions

def ensure_memory_file() -> None:
    """Ensure the memory file and directory exist."""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        with open(MEMORY_FILE, 'w') as f:
            json.dump([], f)


def load_memories() -> List[Dict[str, Any]]:
    """Load all memory entries from the JSON file."""
    ensure_memory_file()
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_memories(memories: List[Dict[str, Any]]) -> None:
    """Save memory entries to the JSON file."""
    ensure_memory_file()
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memories, f, indent=2)


def count_words(text: str) -> int:
    """Count the number of words in a text string."""
    return len(text.split())


def format_memories_as_markdown(memories: List[Dict[str, Any]]) -> str:
    """Format memory entries as markdown."""
    if not memories:
        return "No memory entries found."
    
    lines = ["# Shared Memory\n"]
    lines.append(f"Total entries: {len(memories)}\n")
    
    for i, entry in enumerate(memories, 1):
        timestamp = entry['timestamp']
        agent = entry['agent_name']
        content = entry['content']
        words = entry['word_count']
        
        lines.append(f"## Entry {i}: {agent}")
        lines.append(f"**Time**: {timestamp}")
        lines.append(f"**Words**: {words}/{MAX_WORDS_PER_ENTRY}")
        lines.append(f"\n{content}\n")
        lines.append("---\n")
    
    return "\n".join(lines)


def format_memories_as_json(memories: List[Dict[str, Any]]) -> str:
    """Format memory entries as JSON."""
    return json.dumps({
        "total_entries": len(memories),
        "entries": memories
    }, indent=2)


# Tool Definitions

class AddMemoryInput(BaseModel):
    """Input model for adding a memory entry."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    agent_name: str = Field(
        ...,
        description="Name of the agent adding this memory (e.g., 'claude-code-alpha', 'assistant-1', 'researcher-bot')",
        min_length=1,
        max_length=100
    )
    
    content: str = Field(
        ...,
        description="The memory content to store. Maximum 200 words.",
        min_length=1
    )
    
    @field_validator('content')
    @classmethod
    def validate_word_count(cls, v: str) -> str:
        """Validate that content doesn't exceed maximum word count."""
        word_count = count_words(v)
        if word_count > MAX_WORDS_PER_ENTRY:
            raise ValueError(
                f"Content exceeds maximum of {MAX_WORDS_PER_ENTRY} words. "
                f"Current word count: {word_count}. Please shorten your message."
            )
        return v


@mcp.tool(
    name="add_memory",
    annotations={
        "title": "Add Memory Entry",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def add_memory(params: AddMemoryInput) -> str:
    """Add a new memory entry to the shared memory space.
    
    This tool allows an agent to record a thought, observation, or message that can
    be read by other agents. Each entry is timestamped and includes the agent's name.
    
    Args:
        params (AddMemoryInput): Input containing:
            - agent_name (str): Name identifying the agent (1-100 characters)
            - content (str): Memory content (max 200 words)
    
    Returns:
        str: Confirmation message with entry details in JSON format containing:
            - success (bool): Whether the operation succeeded
            - entry_number (int): The sequence number of this entry
            - timestamp (str): ISO 8601 timestamp when entry was created
            - agent_name (str): Name of the agent
            - word_count (int): Number of words in the entry
            - message (str): Human-readable confirmation message
    
    Example:
        >>> add_memory(agent_name="claude-alpha", content="I've analyzed the data...")
    """
    # Load existing memories
    memories = load_memories()
    
    # Create new entry
    timestamp = datetime.now(timezone.utc).isoformat()
    word_count = count_words(params.content)
    
    entry = {
        "timestamp": timestamp,
        "agent_name": params.agent_name,
        "content": params.content,
        "word_count": word_count
    }
    
    # Append and save
    memories.append(entry)
    save_memories(memories)
    
    # Return confirmation
    result = {
        "success": True,
        "entry_number": len(memories),
        "timestamp": timestamp,
        "agent_name": params.agent_name,
        "word_count": word_count,
        "message": f"Memory entry #{len(memories)} added successfully by {params.agent_name}"
    }
    
    return json.dumps(result, indent=2)


class ReadMemoryInput(BaseModel):
    """Input model for reading memory entries."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )
    
    limit: Optional[int] = Field(
        default=None,
        description="Optional limit on number of entries to return (returns most recent). If not specified, returns all entries.",
        ge=1,
        le=1000
    )
    
    agent_filter: Optional[str] = Field(
        default=None,
        description="Optional filter to only show entries from a specific agent name",
        max_length=100
    )


@mcp.tool(
    name="read_memory",
    annotations={
        "title": "Read Memory Entries",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def read_memory(params: ReadMemoryInput) -> str:
    """Read all memory entries from the shared memory space in chronological order.
    
    This tool retrieves all memory entries that have been recorded by various agents,
    presented in the order they were created (oldest first). Useful for catching up
    on the conversation or reviewing past thoughts.
    
    Args:
        params (ReadMemoryInput): Input containing:
            - response_format (ResponseFormat): 'markdown' (default) or 'json'
            - limit (Optional[int]): Maximum number of entries to return (most recent)
            - agent_filter (Optional[str]): Only show entries from this agent
    
    Returns:
        str: All memory entries formatted according to response_format
        
        Markdown format includes:
        - Total entry count
        - For each entry: entry number, agent name, timestamp, word count, content
        
        JSON format includes:
        - total_entries (int): Total number of entries
        - entries (List[Dict]): Array of entry objects with timestamp, agent_name, 
          content, and word_count fields
    
    Example:
        >>> read_memory(response_format="markdown")
        >>> read_memory(response_format="json", limit=10)
        >>> read_memory(agent_filter="claude-alpha")
    """
    # Load memories
    memories = load_memories()
    
    # Apply agent filter if specified
    if params.agent_filter:
        memories = [m for m in memories if m['agent_name'] == params.agent_filter]
    
    # Apply limit if specified (get most recent)
    if params.limit and len(memories) > params.limit:
        memories = memories[-params.limit:]
    
    # Format response
    if params.response_format == ResponseFormat.MARKDOWN:
        result = format_memories_as_markdown(memories)
    else:
        result = format_memories_as_json(memories)
    
    # Check character limit
    if len(result) > CHARACTER_LIMIT:
        truncated_count = len(memories) // 2
        memories = memories[-truncated_count:]
        
        if params.response_format == ResponseFormat.MARKDOWN:
            result = format_memories_as_markdown(memories)
        else:
            result = format_memories_as_json(memories)
        
        truncation_notice = (
            f"\n\n⚠️ **Response Truncated**: Showing most recent {truncated_count} of "
            f"{len(load_memories())} entries. Use 'limit' parameter to control results."
        )
        result = result + truncation_notice
    
    return result


class ClearMemoryInput(BaseModel):
    """Input model for clearing memory."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    confirm: bool = Field(
        ...,
        description="Must be set to true to confirm you want to clear all memory entries"
    )


@mcp.tool(
    name="clear_memory",
    annotations={
        "title": "Clear All Memory",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def clear_memory(params: ClearMemoryInput) -> str:
    """Clear all memory entries from the shared memory space.
    
    This is a destructive operation that removes all recorded memory entries.
    Use this to start fresh or clean up after a conversation session.
    
    Args:
        params (ClearMemoryInput): Input containing:
            - confirm (bool): Must be true to proceed with clearing
    
    Returns:
        str: Confirmation message in JSON format containing:
            - success (bool): Whether the operation succeeded
            - entries_cleared (int): Number of entries that were removed
            - message (str): Human-readable confirmation message
    
    Example:
        >>> clear_memory(confirm=True)
    """
    if not params.confirm:
        return json.dumps({
            "success": False,
            "error": "Confirmation required. Set 'confirm' parameter to true to clear memory."
        }, indent=2)
    
    # Load current memories to count them
    memories = load_memories()
    count = len(memories)
    
    # Clear memory
    save_memories([])
    
    result = {
        "success": True,
        "entries_cleared": count,
        "message": f"Successfully cleared {count} memory entries. Memory is now empty."
    }
    
    return json.dumps(result, indent=2)


# Main entry point
if __name__ == "__main__":
    mcp.run()
