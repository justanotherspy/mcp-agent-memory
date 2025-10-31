#!/usr/bin/env python3
"""
Shared Memory MCP Server - Version 2.0
======================================

An enhanced MCP server providing shared memory with:
- Concurrent access safety (file locking)
- Structured logging and monitoring
- CRUD operations with unique entry IDs
- Advanced search and filtering
- Tags, priority levels, and metadata
- Memory statistics and bulk operations
- Automatic backup and rotation

Perfect for enabling sophisticated multi-agent collaboration.

Usage:
    python shared_memory_mcp.py
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import uuid
import re
import time

# Import utilities
from utils.file_lock import file_lock, atomic_write, FileLockTimeout, FileLockError
from utils.logger import get_logger

# Constants
CHARACTER_LIMIT = 25000  # Maximum response size in characters
MAX_WORDS_PER_ENTRY = 200  # Maximum words per memory entry
MAX_ENTRIES = 1000  # Maximum entries before rotation
MEMORY_FILE = Path.home() / ".shared_memory_mcp" / "memory.json"
BACKUP_DIR = Path.home() / ".shared_memory_mcp" / "backups"
STORAGE_VERSION = "2.0"

# Initialize FastMCP server
mcp = FastMCP("shared_memory_mcp")

# Initialize logger
logger = get_logger()


# Enums

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class Priority(str, Enum):
    """Priority levels for memory entries."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SortOrder(str, Enum):
    """Sort order for memory entries."""
    CHRONOLOGICAL = "chronological"  # Oldest first
    REVERSE = "reverse"  # Newest first
    PRIORITY = "priority"  # High to low


# Data Models

class MemoryEntry(BaseModel):
    """Model representing a single memory entry."""
    entry_id: str
    timestamp: str
    agent_name: str
    content: str
    word_count: int
    tags: List[str] = Field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    metadata: Dict[str, Any] = Field(default_factory=dict)
    updated_at: Optional[str] = None


class StorageFormat(BaseModel):
    """Model for the memory storage file format."""
    version: str
    entries: List[Dict[str, Any]]
    created_at: str
    updated_at: str


# Storage Management Functions

def ensure_storage_structure() -> None:
    """Ensure storage directory, file, and backup directory exist."""
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if not MEMORY_FILE.exists():
        initial_storage = {
            "version": STORAGE_VERSION,
            "entries": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        atomic_write(MEMORY_FILE, json.dumps(initial_storage, indent=2))
        logger.info("Initialized new memory storage", version=STORAGE_VERSION)


def load_memories() -> List[Dict[str, Any]]:
    """
    Load all memory entries from the JSON file with file locking.

    Returns:
        List[Dict[str, Any]]: List of memory entries

    Raises:
        FileLockTimeout: If unable to acquire lock within timeout
    """
    ensure_storage_structure()

    try:
        start_time = time.time()
        with file_lock(MEMORY_FILE, timeout=10.0) as f:
            lock_time = (time.time() - start_time) * 1000
            logger.log_lock_acquired(str(MEMORY_FILE), lock_time)

            content = f.read()

            if not content.strip():
                logger.warning("Empty memory file detected, initializing")
                return []

            try:
                data = json.loads(content)

                # Handle v1 format (list) vs v2 format (dict with version)
                if isinstance(data, list):
                    logger.info("Detected v1 format, auto-migrating to v2")
                    return data
                elif isinstance(data, dict):
                    return data.get("entries", [])
                else:
                    logger.error("Invalid storage format detected", type=type(data).__name__)
                    return []

            except json.JSONDecodeError as e:
                logger.log_storage_corruption(str(MEMORY_FILE), str(e))
                # Try to recover from backup
                backup_entries = recover_from_backup()
                if backup_entries is not None:
                    logger.log_storage_recovered(str(MEMORY_FILE), backup_used=True)
                    return backup_entries
                logger.error("Unable to recover from backup, returning empty", exc_info=True)
                return []

    except FileLockTimeout as e:
        logger.log_lock_timeout(str(MEMORY_FILE), 10.0)
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading memories", exc_info=True)
        return []


def save_memories(memories: List[Dict[str, Any]]) -> None:
    """
    Save memory entries to the JSON file with file locking and rotation.

    Args:
        memories (List[Dict[str, Any]]): List of memory entries to save
    """
    ensure_storage_structure()

    try:
        # Apply rotation if needed
        if len(memories) > MAX_ENTRIES:
            rotated_count = len(memories) - MAX_ENTRIES
            logger.warning(
                f"Rotating memory: removing {rotated_count} oldest entries",
                total_entries=len(memories),
                max_entries=MAX_ENTRIES
            )
            memories = memories[-MAX_ENTRIES:]

        # Create storage structure
        storage_data = {
            "version": STORAGE_VERSION,
            "entries": memories,
            "created_at": None,  # Will preserve from existing file
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        # Preserve created_at timestamp
        try:
            with file_lock(MEMORY_FILE, timeout=10.0) as f:
                content = f.read()
                if content.strip():
                    existing_data = json.loads(content)
                    if isinstance(existing_data, dict) and "created_at" in existing_data:
                        storage_data["created_at"] = existing_data["created_at"]
        except Exception:
            pass

        # Set created_at if not set
        if storage_data["created_at"] is None:
            storage_data["created_at"] = datetime.now(timezone.utc).isoformat()

        # Create backup before writing
        create_backup()

        # Write with atomic operation
        atomic_write(MEMORY_FILE, json.dumps(storage_data, indent=2))

        logger.debug("Memories saved successfully", entry_count=len(memories))

    except FileLockTimeout as e:
        logger.log_lock_timeout(str(MEMORY_FILE), 10.0)
        raise
    except Exception as e:
        logger.error(f"Failed to save memories", exc_info=True)
        raise


def create_backup() -> None:
    """Create a backup of the current memory file."""
    if not MEMORY_FILE.exists() or MEMORY_FILE.stat().st_size == 0:
        return

    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"memory_backup_{timestamp}.json"

        # Copy current file to backup
        with open(MEMORY_FILE, 'r') as src:
            content = src.read()

        with open(backup_file, 'w') as dst:
            dst.write(content)

        logger.debug("Backup created", backup_file=str(backup_file))

        # Clean up old backups (keep last 10)
        cleanup_old_backups(keep=10)

    except Exception as e:
        logger.warning(f"Failed to create backup", error=str(e))


def cleanup_old_backups(keep: int = 10) -> None:
    """Remove old backup files, keeping only the most recent ones."""
    try:
        backups = sorted(BACKUP_DIR.glob("memory_backup_*.json"))

        if len(backups) > keep:
            for backup_file in backups[:-keep]:
                backup_file.unlink()
                logger.debug("Removed old backup", file=str(backup_file))

    except Exception as e:
        logger.warning(f"Failed to cleanup old backups", error=str(e))


def recover_from_backup() -> Optional[List[Dict[str, Any]]]:
    """
    Attempt to recover memory entries from the most recent backup.

    Returns:
        Optional[List[Dict[str, Any]]]: Recovered entries or None if recovery fails
    """
    try:
        backups = sorted(BACKUP_DIR.glob("memory_backup_*.json"))

        if not backups:
            logger.warning("No backup files found for recovery")
            return None

        # Try most recent backup first
        for backup_file in reversed(backups):
            try:
                with open(backup_file, 'r') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    logger.info(f"Recovered from backup (v1)", backup=str(backup_file))
                    return data
                elif isinstance(data, dict) and "entries" in data:
                    logger.info(f"Recovered from backup (v2)", backup=str(backup_file))
                    return data["entries"]

            except Exception as e:
                logger.warning(f"Failed to recover from backup", backup=str(backup_file), error=str(e))
                continue

        logger.error("All backup recovery attempts failed")
        return None

    except Exception as e:
        logger.error(f"Error during backup recovery", exc_info=True)
        return None


# Utility Functions

def count_words(text: str) -> int:
    """Count the number of words in a text string."""
    return len(text.split())


def generate_entry_id() -> str:
    """Generate a unique entry ID."""
    return str(uuid.uuid4())


def validate_entry_id(entry_id: str) -> bool:
    """Validate that a string is a valid UUID."""
    try:
        uuid.UUID(entry_id)
        return True
    except ValueError:
        return False


def find_entry_by_id(memories: List[Dict[str, Any]], entry_id: str) -> Optional[Dict[str, Any]]:
    """Find a memory entry by its ID."""
    for entry in memories:
        if entry.get("entry_id") == entry_id:
            return entry
    return None


def filter_memories(
    memories: List[Dict[str, Any]],
    agent_filter: Optional[str] = None,
    tags: Optional[List[str]] = None,
    priority: Optional[Priority] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter memory entries based on various criteria.

    Args:
        memories: List of memory entries
        agent_filter: Filter by agent name
        tags: Filter by tags (must have all specified tags)
        priority: Filter by priority level
        date_from: Filter entries after this ISO timestamp
        date_to: Filter entries before this ISO timestamp

    Returns:
        Filtered list of memory entries
    """
    filtered = memories

    # Agent filter
    if agent_filter:
        filtered = [m for m in filtered if m.get("agent_name") == agent_filter]

    # Tags filter (entry must have all specified tags)
    if tags:
        filtered = [
            m for m in filtered
            if all(tag in m.get("tags", []) for tag in tags)
        ]

    # Priority filter
    if priority:
        filtered = [m for m in filtered if m.get("priority") == priority.value]

    # Date range filters
    if date_from:
        filtered = [m for m in filtered if m.get("timestamp", "") >= date_from]

    if date_to:
        filtered = [m for m in filtered if m.get("timestamp", "") <= date_to]

    return filtered


def sort_memories(
    memories: List[Dict[str, Any]],
    sort_order: SortOrder = SortOrder.CHRONOLOGICAL
) -> List[Dict[str, Any]]:
    """Sort memory entries according to specified order."""
    if sort_order == SortOrder.REVERSE:
        return list(reversed(memories))
    elif sort_order == SortOrder.PRIORITY:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(
            memories,
            key=lambda m: priority_order.get(m.get("priority", "medium"), 1)
        )
    else:  # CHRONOLOGICAL (default)
        return memories


def search_memories(
    memories: List[Dict[str, Any]],
    query: str,
    case_sensitive: bool = False
) -> List[Dict[str, Any]]:
    """
    Search memory entries for a query string.

    Searches in: content, agent_name, and tags

    Args:
        memories: List of memory entries
        query: Search query string
        case_sensitive: Whether search should be case-sensitive

    Returns:
        List of matching memory entries
    """
    if not query:
        return memories

    results = []
    search_pattern = query if case_sensitive else query.lower()

    for entry in memories:
        # Search in content
        content = entry.get("content", "")
        if not case_sensitive:
            content = content.lower()

        if search_pattern in content:
            results.append(entry)
            continue

        # Search in agent name
        agent_name = entry.get("agent_name", "")
        if not case_sensitive:
            agent_name = agent_name.lower()

        if search_pattern in agent_name:
            results.append(entry)
            continue

        # Search in tags
        tags = entry.get("tags", [])
        if not case_sensitive:
            tags = [t.lower() for t in tags]

        if any(search_pattern in tag for tag in tags):
            results.append(entry)
            continue

    return results


def format_memories_as_markdown(memories: List[Dict[str, Any]]) -> str:
    """Format memory entries as markdown."""
    if not memories:
        return "No memory entries found."

    lines = ["# Shared Memory\n"]
    lines.append(f"Total entries: {len(memories)}\n")

    for i, entry in enumerate(memories, 1):
        entry_id = entry.get('entry_id', 'unknown')
        timestamp = entry.get('timestamp', 'unknown')
        agent = entry.get('agent_name', 'unknown')
        content = entry.get('content', '')
        words = entry.get('word_count', 0)
        priority = entry.get('priority', 'medium')
        tags = entry.get('tags', [])
        updated_at = entry.get('updated_at')

        lines.append(f"## Entry {i}: {agent}")
        lines.append(f"**ID**: `{entry_id}`")
        lines.append(f"**Time**: {timestamp}")
        if updated_at:
            lines.append(f"**Updated**: {updated_at}")
        lines.append(f"**Words**: {words}/{MAX_WORDS_PER_ENTRY}")
        lines.append(f"**Priority**: {priority}")
        if tags:
            lines.append(f"**Tags**: {', '.join(tags)}")
        lines.append(f"\n{content}\n")
        lines.append("---\n")

    return "\n".join(lines)


def format_memories_as_json(memories: List[Dict[str, Any]]) -> str:
    """Format memory entries as JSON."""
    return json.dumps({
        "total_entries": len(memories),
        "entries": memories
    }, indent=2)


# Tool Input Models

class AddMemoryInput(BaseModel):
    """Input model for adding a memory entry."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    agent_name: str = Field(
        ...,
        description="Name of the agent adding this memory",
        min_length=1,
        max_length=100
    )

    content: str = Field(
        ...,
        description="The memory content to store. Maximum 200 words.",
        min_length=1
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Optional tags for categorizing this memory",
        max_length=10
    )

    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Priority level: low, medium, or high"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata for this entry"
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

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags list."""
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed per entry")
        # Strip whitespace and convert to lowercase
        return [tag.strip().lower() for tag in v if tag.strip()]


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
    """
    Add a new memory entry to the shared memory space.

    This tool allows an agent to record a thought, observation, or message with
    optional tags, priority level, and metadata for better organization.

    Args:
        params: Input containing agent_name, content, tags, priority, metadata

    Returns:
        JSON confirmation with entry details including unique entry_id

    Example:
        >>> add_memory(
        ...     agent_name="claude-alpha",
        ...     content="Analyzed user data and found 3 insights",
        ...     tags=["analysis", "insights"],
        ...     priority="high"
        ... )
    """
    try:
        # Load existing memories
        memories = load_memories()

        # Create new entry
        timestamp = datetime.now(timezone.utc).isoformat()
        entry_id = generate_entry_id()
        word_count = count_words(params.content)

        entry = {
            "entry_id": entry_id,
            "timestamp": timestamp,
            "agent_name": params.agent_name,
            "content": params.content,
            "word_count": word_count,
            "tags": params.tags,
            "priority": params.priority.value,
            "metadata": params.metadata,
            "updated_at": None
        }

        # Append and save
        memories.append(entry)
        save_memories(memories)

        # Log operation
        logger.log_add_memory(
            agent_name=params.agent_name,
            word_count=word_count,
            entry_number=len(memories),
            success=True
        )

        # Return confirmation
        result = {
            "success": True,
            "entry_id": entry_id,
            "entry_number": len(memories),
            "timestamp": timestamp,
            "agent_name": params.agent_name,
            "word_count": word_count,
            "tags": params.tags,
            "priority": params.priority.value,
            "message": f"Memory entry #{len(memories)} added successfully by {params.agent_name}"
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.log_add_memory(
            agent_name=params.agent_name,
            word_count=0,
            entry_number=0,
            success=False,
            error=str(e)
        )
        return json.dumps({
            "success": False,
            "error": f"Failed to add memory: {str(e)}"
        }, indent=2)


class ReadMemoryInput(BaseModel):
    """Input model for reading memory entries."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )

    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of entries to return (most recent)",
        ge=1,
        le=1000
    )

    agent_filter: Optional[str] = Field(
        default=None,
        description="Filter by agent name",
        max_length=100
    )

    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter by tags (entry must have all specified tags)"
    )

    priority: Optional[Priority] = Field(
        default=None,
        description="Filter by priority level"
    )

    sort_order: SortOrder = Field(
        default=SortOrder.CHRONOLOGICAL,
        description="Sort order: chronological, reverse, or priority"
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
    """
    Read memory entries with advanced filtering and sorting.

    Retrieve memory entries with optional filters for agent, tags, priority,
    and customizable sorting.

    Args:
        params: Input with format, filters, and sort options

    Returns:
        Formatted memory entries (markdown or JSON)

    Example:
        >>> read_memory(response_format="markdown", tags=["analysis"], priority="high")
    """
    try:
        # Load memories
        memories = load_memories()
        total_count = len(memories)

        # Apply filters
        memories = filter_memories(
            memories,
            agent_filter=params.agent_filter,
            tags=params.tags,
            priority=params.priority
        )

        # Apply sorting
        memories = sort_memories(memories, params.sort_order)

        # Apply limit if specified (get most recent after sorting)
        if params.limit and len(memories) > params.limit:
            if params.sort_order == SortOrder.CHRONOLOGICAL:
                memories = memories[-params.limit:]
            else:
                memories = memories[:params.limit]

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            result = format_memories_as_markdown(memories)
        else:
            result = format_memories_as_json(memories)

        truncated = False
        # Check character limit
        if len(result) > CHARACTER_LIMIT:
            truncated_count = len(memories) // 2
            memories = memories[-truncated_count:]

            if params.response_format == ResponseFormat.MARKDOWN:
                result = format_memories_as_markdown(memories)
            else:
                result = format_memories_as_json(memories)

            truncation_notice = (
                f"\n\n⚠️ **Response Truncated**: Showing {truncated_count} of "
                f"{total_count} entries. Use 'limit' parameter to control results."
            )
            result = result + truncation_notice
            truncated = True

        # Log operation
        logger.log_read_memory(
            format=params.response_format.value,
            entry_count=len(memories),
            agent_filter=params.agent_filter,
            limit=params.limit,
            truncated=truncated
        )

        return result

    except Exception as e:
        logger.error(f"Failed to read memory", exc_info=True)
        return json.dumps({
            "success": False,
            "error": f"Failed to read memory: {str(e)}"
        }, indent=2)


class UpdateMemoryInput(BaseModel):
    """Input model for updating a memory entry."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    entry_id: str = Field(
        ...,
        description="Unique ID of the entry to update"
    )

    content: Optional[str] = Field(
        default=None,
        description="New content (max 200 words). If not provided, content unchanged.",
        min_length=1
    )

    tags: Optional[List[str]] = Field(
        default=None,
        description="New tags list. If not provided, tags unchanged."
    )

    priority: Optional[Priority] = Field(
        default=None,
        description="New priority level. If not provided, priority unchanged."
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="New metadata. If not provided, metadata unchanged."
    )

    @field_validator('content')
    @classmethod
    def validate_word_count(cls, v: Optional[str]) -> Optional[str]:
        """Validate that content doesn't exceed maximum word count."""
        if v is None:
            return v
        word_count = count_words(v)
        if word_count > MAX_WORDS_PER_ENTRY:
            raise ValueError(
                f"Content exceeds maximum of {MAX_WORDS_PER_ENTRY} words. "
                f"Current word count: {word_count}."
            )
        return v


@mcp.tool(
    name="update_memory",
    annotations={
        "title": "Update Memory Entry",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def update_memory(params: UpdateMemoryInput) -> str:
    """
    Update an existing memory entry.

    Modify content, tags, priority, or metadata of a memory entry by its ID.
    Only specified fields are updated; others remain unchanged.

    Args:
        params: Input with entry_id and fields to update

    Returns:
        JSON confirmation with updated entry details

    Example:
        >>> update_memory(
        ...     entry_id="abc-123-def",
        ...     tags=["analysis", "complete"],
        ...     priority="low"
        ... )
    """
    try:
        # Validate entry ID format
        if not validate_entry_id(params.entry_id):
            return json.dumps({
                "success": False,
                "error": f"Invalid entry_id format: {params.entry_id}"
            }, indent=2)

        # Load memories
        memories = load_memories()

        # Find entry
        entry = find_entry_by_id(memories, params.entry_id)
        if entry is None:
            return json.dumps({
                "success": False,
                "error": f"Entry not found with ID: {params.entry_id}"
            }, indent=2)

        # Update fields
        updated_fields = []

        if params.content is not None:
            entry["content"] = params.content
            entry["word_count"] = count_words(params.content)
            updated_fields.append("content")

        if params.tags is not None:
            entry["tags"] = [tag.strip().lower() for tag in params.tags if tag.strip()]
            updated_fields.append("tags")

        if params.priority is not None:
            entry["priority"] = params.priority.value
            updated_fields.append("priority")

        if params.metadata is not None:
            entry["metadata"] = params.metadata
            updated_fields.append("metadata")

        # Update timestamp
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Save
        save_memories(memories)

        # Log operation
        logger.log_update_memory(
            entry_id=params.entry_id,
            agent_name=entry.get("agent_name", "unknown"),
            success=True
        )

        result = {
            "success": True,
            "entry_id": params.entry_id,
            "updated_fields": updated_fields,
            "updated_at": entry["updated_at"],
            "message": f"Entry {params.entry_id} updated successfully"
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.log_update_memory(
            entry_id=params.entry_id,
            agent_name="unknown",
            success=False,
            error=str(e)
        )
        return json.dumps({
            "success": False,
            "error": f"Failed to update memory: {str(e)}"
        }, indent=2)


class DeleteMemoryInput(BaseModel):
    """Input model for deleting a memory entry."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    entry_id: str = Field(
        ...,
        description="Unique ID of the entry to delete"
    )


@mcp.tool(
    name="delete_memory",
    annotations={
        "title": "Delete Memory Entry",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def delete_memory(params: DeleteMemoryInput) -> str:
    """
    Delete a specific memory entry by ID.

    Args:
        params: Input with entry_id to delete

    Returns:
        JSON confirmation of deletion

    Example:
        >>> delete_memory(entry_id="abc-123-def")
    """
    try:
        # Validate entry ID format
        if not validate_entry_id(params.entry_id):
            return json.dumps({
                "success": False,
                "error": f"Invalid entry_id format: {params.entry_id}"
            }, indent=2)

        # Load memories
        memories = load_memories()
        original_count = len(memories)

        # Find and remove entry
        entry = find_entry_by_id(memories, params.entry_id)
        if entry is None:
            return json.dumps({
                "success": False,
                "error": f"Entry not found with ID: {params.entry_id}"
            }, indent=2)

        # Remove entry
        memories = [m for m in memories if m.get("entry_id") != params.entry_id]

        # Save
        save_memories(memories)

        # Log operation
        logger.log_delete_memory(entry_id=params.entry_id, success=True)

        result = {
            "success": True,
            "entry_id": params.entry_id,
            "agent_name": entry.get("agent_name"),
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "remaining_entries": len(memories),
            "message": f"Entry {params.entry_id} deleted successfully"
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.log_delete_memory(entry_id=params.entry_id, success=False, error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Failed to delete memory: {str(e)}"
        }, indent=2)


class GetMemoryInput(BaseModel):
    """Input model for getting a single memory entry."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    entry_id: str = Field(
        ...,
        description="Unique ID of the entry to retrieve"
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'markdown' or 'json'"
    )


@mcp.tool(
    name="get_memory",
    annotations={
        "title": "Get Single Memory Entry",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_memory(params: GetMemoryInput) -> str:
    """
    Retrieve a single memory entry by its ID.

    Args:
        params: Input with entry_id and format

    Returns:
        Memory entry in specified format

    Example:
        >>> get_memory(entry_id="abc-123-def", response_format="json")
    """
    try:
        # Validate entry ID format
        if not validate_entry_id(params.entry_id):
            return json.dumps({
                "success": False,
                "error": f"Invalid entry_id format: {params.entry_id}"
            }, indent=2)

        # Load memories
        memories = load_memories()

        # Find entry
        entry = find_entry_by_id(memories, params.entry_id)
        if entry is None:
            return json.dumps({
                "success": False,
                "error": f"Entry not found with ID: {params.entry_id}"
            }, indent=2)

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            result = format_memories_as_markdown([entry])
        else:
            result = json.dumps({
                "success": True,
                "entry": entry
            }, indent=2)

        logger.debug("Retrieved single memory entry", entry_id=params.entry_id)

        return result

    except Exception as e:
        logger.error(f"Failed to get memory entry", entry_id=params.entry_id, exc_info=True)
        return json.dumps({
            "success": False,
            "error": f"Failed to get memory: {str(e)}"
        }, indent=2)


class SearchMemoryInput(BaseModel):
    """Input model for searching memory entries."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    query: str = Field(
        ...,
        description="Search query (searches content, agent names, and tags)",
        min_length=1,
        max_length=200
    )

    case_sensitive: bool = Field(
        default=False,
        description="Whether search should be case-sensitive"
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )

    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of results to return",
        ge=1,
        le=1000
    )


@mcp.tool(
    name="search_memory",
    annotations={
        "title": "Search Memory Entries",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def search_memory(params: SearchMemoryInput) -> str:
    """
    Search memory entries for a query string.

    Searches across content, agent names, and tags.

    Args:
        params: Input with query and search options

    Returns:
        Matching memory entries in specified format

    Example:
        >>> search_memory(query="analysis", case_sensitive=False, limit=10)
    """
    try:
        start_time = time.time()

        # Load memories
        memories = load_memories()

        # Search
        results = search_memories(memories, params.query, params.case_sensitive)

        # Apply limit
        if params.limit and len(results) > params.limit:
            results = results[:params.limit]

        # Format response
        if params.response_format == ResponseFormat.MARKDOWN:
            result = format_memories_as_markdown(results)
            if results:
                result = f"# Search Results for: \"{params.query}\"\n\n" + result
        else:
            result = json.dumps({
                "success": True,
                "query": params.query,
                "total_results": len(results),
                "entries": results
            }, indent=2)

        search_time = (time.time() - start_time) * 1000

        # Log operation
        logger.log_search_memory(
            query=params.query,
            results_count=len(results),
            search_time_ms=search_time
        )

        return result

    except Exception as e:
        logger.error(f"Failed to search memory", query=params.query, exc_info=True)
        return json.dumps({
            "success": False,
            "error": f"Failed to search memory: {str(e)}"
        }, indent=2)


class GetMemoryStatsInput(BaseModel):
    """Input model for getting memory statistics."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'markdown' or 'json'"
    )


@mcp.tool(
    name="get_memory_stats",
    annotations={
        "title": "Get Memory Statistics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_memory_stats(params: GetMemoryStatsInput) -> str:
    """
    Get statistics about the shared memory.

    Provides insights on:
    - Total entries and word count
    - Agent activity (entries per agent)
    - Tag usage
    - Priority distribution
    - Date range
    - Storage size

    Args:
        params: Input with response_format

    Returns:
        Memory statistics in specified format

    Example:
        >>> get_memory_stats(response_format="json")
    """
    try:
        # Load memories
        memories = load_memories()

        if not memories:
            return json.dumps({
                "success": True,
                "total_entries": 0,
                "message": "No memory entries found"
            }, indent=2)

        # Calculate statistics
        total_entries = len(memories)
        total_words = sum(m.get("word_count", 0) for m in memories)

        # Agent activity
        agent_counts = {}
        for m in memories:
            agent = m.get("agent_name", "unknown")
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        # Tag usage
        tag_counts = {}
        for m in memories:
            for tag in m.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Priority distribution
        priority_counts = {"low": 0, "medium": 0, "high": 0}
        for m in memories:
            priority = m.get("priority", "medium")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        # Date range
        timestamps = [m.get("timestamp") for m in memories if m.get("timestamp")]
        date_range = {
            "earliest": min(timestamps) if timestamps else None,
            "latest": max(timestamps) if timestamps else None
        }

        # Storage size
        storage_size = MEMORY_FILE.stat().st_size if MEMORY_FILE.exists() else 0

        stats = {
            "success": True,
            "total_entries": total_entries,
            "total_words": total_words,
            "average_words_per_entry": round(total_words / total_entries, 1) if total_entries > 0 else 0,
            "agent_activity": agent_counts,
            "top_agents": sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "tag_usage": tag_counts,
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "priority_distribution": priority_counts,
            "date_range": date_range,
            "storage_size_bytes": storage_size,
            "storage_size_kb": round(storage_size / 1024, 2),
            "max_entries": MAX_ENTRIES,
            "entries_until_rotation": MAX_ENTRIES - total_entries if total_entries < MAX_ENTRIES else 0
        }

        if params.response_format == ResponseFormat.MARKDOWN:
            # Format as markdown
            lines = ["# Memory Statistics\n"]
            lines.append(f"**Total Entries**: {stats['total_entries']}")
            lines.append(f"**Total Words**: {stats['total_words']:,}")
            lines.append(f"**Average Words/Entry**: {stats['average_words_per_entry']}")
            lines.append(f"**Storage Size**: {stats['storage_size_kb']} KB\n")

            lines.append("## Agent Activity")
            for agent, count in stats['top_agents']:
                lines.append(f"- {agent}: {count} entries")
            lines.append("")

            if stats['top_tags']:
                lines.append("## Top Tags")
                for tag, count in stats['top_tags']:
                    lines.append(f"- {tag}: {count} uses")
                lines.append("")

            lines.append("## Priority Distribution")
            for priority, count in stats['priority_distribution'].items():
                lines.append(f"- {priority.capitalize()}: {count} entries")
            lines.append("")

            lines.append("## Date Range")
            lines.append(f"- **Earliest**: {stats['date_range']['earliest']}")
            lines.append(f"- **Latest**: {stats['date_range']['latest']}")

            result = "\n".join(lines)
        else:
            result = json.dumps(stats, indent=2)

        logger.info("Retrieved memory statistics", total_entries=total_entries)

        return result

    except Exception as e:
        logger.error("Failed to get memory statistics", exc_info=True)
        return json.dumps({
            "success": False,
            "error": f"Failed to get statistics: {str(e)}"
        }, indent=2)


class ClearMemoryInput(BaseModel):
    """Input model for clearing memory."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    confirm: bool = Field(
        ...,
        description="Must be true to confirm clearing all memory entries"
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
    """
    Clear all memory entries from the shared memory space.

    This is a destructive operation that removes all entries.
    A backup is created automatically before clearing.

    Args:
        params: Input with confirm=True

    Returns:
        JSON confirmation of cleared entries

    Example:
        >>> clear_memory(confirm=True)
    """
    try:
        if not params.confirm:
            return json.dumps({
                "success": False,
                "error": "Confirmation required. Set 'confirm' parameter to true."
            }, indent=2)

        # Load current memories to count them
        memories = load_memories()
        count = len(memories)

        # Create backup before clearing
        create_backup()

        # Clear memory
        save_memories([])

        # Log operation
        logger.log_clear_memory(entries_cleared=count, success=True)

        result = {
            "success": True,
            "entries_cleared": count,
            "cleared_at": datetime.now(timezone.utc).isoformat(),
            "message": f"Successfully cleared {count} memory entries. Backup created."
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.log_clear_memory(entries_cleared=0, success=False)
        return json.dumps({
            "success": False,
            "error": f"Failed to clear memory: {str(e)}"
        }, indent=2)


class HealthCheckInput(BaseModel):
    """Input model for health check."""
    model_config = ConfigDict(extra='forbid')


@mcp.tool(
    name="health_check",
    annotations={
        "title": "Health Check",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def health_check(params: HealthCheckInput) -> str:
    """
    Check the health status of the memory system.

    Verifies:
    - Storage file accessibility
    - File locking capability
    - Backup directory status
    - JSON parsing validity

    Returns:
        JSON health status report

    Example:
        >>> health_check()
    """
    try:
        health_status = {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {}
        }

        # Check storage file exists and is readable
        try:
            ensure_storage_structure()
            health_status["checks"]["storage_file"] = {
                "status": "ok",
                "path": str(MEMORY_FILE),
                "exists": MEMORY_FILE.exists(),
                "size_bytes": MEMORY_FILE.stat().st_size if MEMORY_FILE.exists() else 0
            }
        except Exception as e:
            health_status["checks"]["storage_file"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["success"] = False

        # Check file locking
        try:
            with file_lock(MEMORY_FILE, timeout=5.0) as f:
                pass
            health_status["checks"]["file_locking"] = {
                "status": "ok",
                "message": "File locking operational"
            }
        except Exception as e:
            health_status["checks"]["file_locking"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["success"] = False

        # Check JSON validity
        try:
            memories = load_memories()
            health_status["checks"]["json_parsing"] = {
                "status": "ok",
                "entry_count": len(memories)
            }
        except Exception as e:
            health_status["checks"]["json_parsing"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["success"] = False

        # Check backup directory
        try:
            backups = list(BACKUP_DIR.glob("memory_backup_*.json"))
            health_status["checks"]["backup_system"] = {
                "status": "ok",
                "backup_dir": str(BACKUP_DIR),
                "backup_count": len(backups)
            }
        except Exception as e:
            health_status["checks"]["backup_system"] = {
                "status": "warning",
                "error": str(e)
            }

        # Overall status
        if health_status["success"]:
            health_status["message"] = "All systems operational"
        else:
            health_status["message"] = "Some checks failed - see details"

        logger.info("Health check completed", success=health_status["success"])

        return json.dumps(health_status, indent=2)

    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        return json.dumps({
            "success": False,
            "error": f"Health check failed: {str(e)}"
        }, indent=2)


# Main entry point
if __name__ == "__main__":
    logger.info("Starting MCP Agent Memory Server", version=STORAGE_VERSION)
    mcp.run()
