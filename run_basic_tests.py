#!/usr/bin/env python3
"""
Basic test runner - runs tests without pytest dependency
"""

import sys
from pathlib import Path

# Test imports
try:
    from shared_memory_mcp import (
        count_words,
        generate_entry_id,
        validate_entry_id,
        find_entry_by_id,
        filter_memories,
        sort_memories,
        search_memories,
        Priority,
        SortOrder
    )
    print("✓ Successfully imported shared_memory_mcp modules")
except Exception as e:
    print(f"✗ Failed to import shared_memory_mcp: {e}")
    sys.exit(1)

try:
    from utils.file_lock import file_lock, atomic_write
    from utils.logger import get_logger
    print("✓ Successfully imported utils modules")
except Exception as e:
    print(f"✗ Failed to import utils: {e}")
    sys.exit(1)

# Run basic tests
def test_count_words():
    assert count_words("hello world") == 2, "count_words failed"
    assert count_words("hello") == 1, "count_words single word failed"
    print("✓ count_words tests passed")

def test_entry_id():
    entry_id = generate_entry_id()
    assert isinstance(entry_id, str), "entry_id not string"
    assert len(entry_id) == 36, "entry_id wrong length"
    assert validate_entry_id(entry_id), "entry_id validation failed"
    assert not validate_entry_id("invalid"), "invalid entry_id passed validation"
    print("✓ entry_id tests passed")

def test_find_entry():
    memories = [
        {"entry_id": "1", "content": "first"},
        {"entry_id": "2", "content": "second"}
    ]
    entry = find_entry_by_id(memories, "2")
    assert entry is not None, "entry not found"
    assert entry["content"] == "second", "wrong entry found"
    assert find_entry_by_id(memories, "999") is None, "nonexistent entry found"
    print("✓ find_entry tests passed")

def test_filter_memories():
    memories = [
        {"agent_name": "alpha", "tags": ["tag1"], "priority": "high"},
        {"agent_name": "beta", "tags": ["tag2"], "priority": "low"},
        {"agent_name": "alpha", "tags": ["tag1", "tag2"], "priority": "medium"}
    ]

    filtered = filter_memories(memories, agent_filter="alpha")
    assert len(filtered) == 2, "agent filter failed"

    filtered = filter_memories(memories, tags=["tag1"])
    assert len(filtered) == 2, "tag filter failed"

    filtered = filter_memories(memories, priority=Priority.HIGH)
    assert len(filtered) == 1, "priority filter failed"

    print("✓ filter_memories tests passed")

def test_sort_memories():
    memories = [
        {"entry_id": "1", "priority": "low"},
        {"entry_id": "2", "priority": "high"},
        {"entry_id": "3", "priority": "medium"}
    ]

    sorted_mem = sort_memories(memories, SortOrder.PRIORITY)
    assert sorted_mem[0]["entry_id"] == "2", "priority sort failed"

    sorted_mem = sort_memories(memories, SortOrder.REVERSE)
    assert sorted_mem[0]["entry_id"] == "3", "reverse sort failed"

    print("✓ sort_memories tests passed")

def test_search_memories():
    memories = [
        {"entry_id": "1", "agent_name": "Alpha", "content": "TEST message", "tags": ["test"]},
        {"entry_id": "2", "agent_name": "Beta", "content": "other message", "tags": ["other"]}
    ]

    results = search_memories(memories, "test", case_sensitive=False)
    assert len(results) == 1, "case-insensitive search failed"

    results = search_memories(memories, "TEST", case_sensitive=True)
    assert len(results) == 1, "case-sensitive search failed"

    results = search_memories(memories, "alpha", case_sensitive=False)
    assert len(results) == 1, "agent name search failed"

    print("✓ search_memories tests passed")

def test_logger():
    logger = get_logger()
    logger.info("Test message")
    logger.debug("Debug message")
    print("✓ logger tests passed")

# Run all tests
def main():
    print("\nRunning basic tests...\n")

    tests = [
        test_count_words,
        test_entry_id,
        test_find_entry,
        test_filter_memories,
        test_sort_memories,
        test_search_memories,
        test_logger
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}\n")

    if failed == 0:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
