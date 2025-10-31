"""
Unit tests for memory operations (add, read, update, delete, search, stats)
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path modification
from shared_memory_mcp import (
    count_words,
    generate_entry_id,
    validate_entry_id,
    find_entry_by_id,
    filter_memories,
    sort_memories,
    search_memories,
    format_memories_as_markdown,
    format_memories_as_json,
    Priority,
    SortOrder
)


class TestWordCount:
    """Test word counting functionality."""

    def test_count_words_simple(self):
        assert count_words("hello world") == 2

    def test_count_words_empty(self):
        assert count_words("") == 1  # Empty split creates ['']

    def test_count_words_single(self):
        assert count_words("hello") == 1

    def test_count_words_multiple_spaces(self):
        assert count_words("hello    world") == 2

    def test_count_words_newlines(self):
        assert count_words("hello\nworld\ntest") == 3


class TestEntryID:
    """Test entry ID generation and validation."""

    def test_generate_entry_id(self):
        entry_id = generate_entry_id()
        assert isinstance(entry_id, str)
        assert len(entry_id) == 36  # UUID format: 8-4-4-4-12

    def test_generate_entry_id_unique(self):
        id1 = generate_entry_id()
        id2 = generate_entry_id()
        assert id1 != id2

    def test_validate_entry_id_valid(self):
        entry_id = generate_entry_id()
        assert validate_entry_id(entry_id) is True

    def test_validate_entry_id_invalid(self):
        assert validate_entry_id("not-a-uuid") is False
        assert validate_entry_id("") is False
        assert validate_entry_id("123") is False


class TestFindEntry:
    """Test finding entries by ID."""

    def test_find_entry_by_id_found(self):
        entry_id = "test-id-123"
        memories = [
            {"entry_id": "id-1", "content": "first"},
            {"entry_id": entry_id, "content": "second"},
            {"entry_id": "id-3", "content": "third"}
        ]
        entry = find_entry_by_id(memories, entry_id)
        assert entry is not None
        assert entry["content"] == "second"

    def test_find_entry_by_id_not_found(self):
        memories = [
            {"entry_id": "id-1", "content": "first"},
            {"entry_id": "id-2", "content": "second"}
        ]
        entry = find_entry_by_id(memories, "nonexistent")
        assert entry is None

    def test_find_entry_by_id_empty_list(self):
        entry = find_entry_by_id([], "any-id")
        assert entry is None


class TestFilterMemories:
    """Test memory filtering functionality."""

    @pytest.fixture
    def sample_memories(self):
        return [
            {
                "entry_id": "1",
                "agent_name": "alpha",
                "content": "test content",
                "tags": ["tag1", "tag2"],
                "priority": "high",
                "timestamp": "2025-01-01T00:00:00Z"
            },
            {
                "entry_id": "2",
                "agent_name": "beta",
                "content": "another test",
                "tags": ["tag2", "tag3"],
                "priority": "low",
                "timestamp": "2025-01-02T00:00:00Z"
            },
            {
                "entry_id": "3",
                "agent_name": "alpha",
                "content": "more content",
                "tags": ["tag1"],
                "priority": "medium",
                "timestamp": "2025-01-03T00:00:00Z"
            }
        ]

    def test_filter_by_agent(self, sample_memories):
        filtered = filter_memories(sample_memories, agent_filter="alpha")
        assert len(filtered) == 2
        assert all(m["agent_name"] == "alpha" for m in filtered)

    def test_filter_by_tags_single(self, sample_memories):
        filtered = filter_memories(sample_memories, tags=["tag1"])
        assert len(filtered) == 2
        assert all("tag1" in m["tags"] for m in filtered)

    def test_filter_by_tags_multiple(self, sample_memories):
        filtered = filter_memories(sample_memories, tags=["tag1", "tag2"])
        assert len(filtered) == 1
        assert filtered[0]["entry_id"] == "1"

    def test_filter_by_priority(self, sample_memories):
        filtered = filter_memories(sample_memories, priority=Priority.HIGH)
        assert len(filtered) == 1
        assert filtered[0]["priority"] == "high"

    def test_filter_by_date_range(self, sample_memories):
        filtered = filter_memories(
            sample_memories,
            date_from="2025-01-02T00:00:00Z"
        )
        assert len(filtered) == 2

        filtered = filter_memories(
            sample_memories,
            date_to="2025-01-02T00:00:00Z"
        )
        assert len(filtered) == 2

    def test_filter_multiple_criteria(self, sample_memories):
        filtered = filter_memories(
            sample_memories,
            agent_filter="alpha",
            tags=["tag1"]
        )
        assert len(filtered) == 2

    def test_filter_no_matches(self, sample_memories):
        filtered = filter_memories(sample_memories, agent_filter="nonexistent")
        assert len(filtered) == 0


class TestSortMemories:
    """Test memory sorting functionality."""

    @pytest.fixture
    def sample_memories(self):
        return [
            {"entry_id": "1", "priority": "low", "timestamp": "2025-01-01"},
            {"entry_id": "2", "priority": "high", "timestamp": "2025-01-02"},
            {"entry_id": "3", "priority": "medium", "timestamp": "2025-01-03"}
        ]

    def test_sort_chronological(self, sample_memories):
        sorted_mem = sort_memories(sample_memories, SortOrder.CHRONOLOGICAL)
        assert [m["entry_id"] for m in sorted_mem] == ["1", "2", "3"]

    def test_sort_reverse(self, sample_memories):
        sorted_mem = sort_memories(sample_memories, SortOrder.REVERSE)
        assert [m["entry_id"] for m in sorted_mem] == ["3", "2", "1"]

    def test_sort_priority(self, sample_memories):
        sorted_mem = sort_memories(sample_memories, SortOrder.PRIORITY)
        # High (2), Medium (3), Low (1)
        assert [m["entry_id"] for m in sorted_mem] == ["2", "3", "1"]


class TestSearchMemories:
    """Test memory search functionality."""

    @pytest.fixture
    def sample_memories(self):
        return [
            {
                "entry_id": "1",
                "agent_name": "AlphaBot",
                "content": "This is a TEST message",
                "tags": ["important", "analysis"]
            },
            {
                "entry_id": "2",
                "agent_name": "BetaBot",
                "content": "Another message here",
                "tags": ["routine"]
            },
            {
                "entry_id": "3",
                "agent_name": "AlphaBot",
                "content": "Follow-up message",
                "tags": ["testing", "analysis"]
            }
        ]

    def test_search_in_content_case_insensitive(self, sample_memories):
        results = search_memories(sample_memories, "test", case_sensitive=False)
        assert len(results) == 2
        assert results[0]["entry_id"] in ["1", "3"]

    def test_search_in_content_case_sensitive(self, sample_memories):
        results = search_memories(sample_memories, "TEST", case_sensitive=True)
        assert len(results) == 1
        assert results[0]["entry_id"] == "1"

    def test_search_in_agent_name(self, sample_memories):
        results = search_memories(sample_memories, "alpha", case_sensitive=False)
        assert len(results) == 2
        assert all(m["agent_name"] == "AlphaBot" for m in results)

    def test_search_in_tags(self, sample_memories):
        results = search_memories(sample_memories, "analysis", case_sensitive=False)
        assert len(results) == 2

    def test_search_no_results(self, sample_memories):
        results = search_memories(sample_memories, "nonexistent")
        assert len(results) == 0

    def test_search_empty_query(self, sample_memories):
        results = search_memories(sample_memories, "")
        assert len(results) == 3


class TestFormatting:
    """Test memory formatting functions."""

    @pytest.fixture
    def sample_memories(self):
        return [
            {
                "entry_id": "test-id-1",
                "timestamp": "2025-01-01T00:00:00Z",
                "agent_name": "TestAgent",
                "content": "Test content here",
                "word_count": 3,
                "tags": ["test", "sample"],
                "priority": "high",
                "updated_at": None
            }
        ]

    def test_format_as_markdown(self, sample_memories):
        result = format_memories_as_markdown(sample_memories)
        assert "# Shared Memory" in result
        assert "Total entries: 1" in result
        assert "TestAgent" in result
        assert "test, sample" in result
        assert "high" in result

    def test_format_as_markdown_empty(self):
        result = format_memories_as_markdown([])
        assert result == "No memory entries found."

    def test_format_as_json(self, sample_memories):
        result = format_memories_as_json(sample_memories)
        data = json.loads(result)
        assert data["total_entries"] == 1
        assert len(data["entries"]) == 1
        assert data["entries"][0]["entry_id"] == "test-id-1"

    def test_format_as_json_empty(self):
        result = format_memories_as_json([])
        data = json.loads(result)
        assert data["total_entries"] == 0
        assert data["entries"] == []


class TestPriorityEnum:
    """Test Priority enum."""

    def test_priority_values(self):
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"


class TestSortOrderEnum:
    """Test SortOrder enum."""

    def test_sort_order_values(self):
        assert SortOrder.CHRONOLOGICAL.value == "chronological"
        assert SortOrder.REVERSE.value == "reverse"
        assert SortOrder.PRIORITY.value == "priority"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
