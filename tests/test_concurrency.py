"""
Concurrency tests for file locking mechanisms
"""

import pytest
import tempfile
import time
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.file_lock import (
    file_lock,
    atomic_write,
    FileLockError,
    FileLockTimeout
)


class TestFileLock:
    """Test file locking functionality."""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write('{"test": "data"}')
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    def test_file_lock_acquire_release(self, temp_file):
        """Test basic lock acquisition and release."""
        with file_lock(temp_file, timeout=5.0) as f:
            content = f.read()
            assert content == '{"test": "data"}'

    def test_file_lock_exclusive(self, temp_file):
        """Test that lock is exclusive - second lock should wait."""
        lock_acquired_times = []

        def acquire_lock(lock_id):
            start = time.time()
            with file_lock(temp_file, timeout=5.0) as f:
                lock_acquired_times.append((lock_id, time.time() - start))
                # Hold lock for a bit
                time.sleep(0.2)
                f.read()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(acquire_lock, 1),
                executor.submit(acquire_lock, 2)
            ]
            for future in as_completed(futures):
                future.result()

        # Second lock should have waited
        assert len(lock_acquired_times) == 2
        wait_times = [t[1] for t in sorted(lock_acquired_times)]
        # Second lock should have waited at least 0.1 seconds
        assert wait_times[1] > 0.1

    def test_file_lock_timeout(self, temp_file):
        """Test lock timeout when unable to acquire."""
        def hold_lock_forever():
            with file_lock(temp_file, timeout=10.0) as f:
                time.sleep(3)  # Hold lock for 3 seconds

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Start first thread to hold lock
            future1 = executor.submit(hold_lock_forever)
            time.sleep(0.1)  # Ensure first thread acquired lock

            # Try to acquire with short timeout
            with pytest.raises(FileLockTimeout):
                with file_lock(temp_file, timeout=0.5) as f:
                    pass

            future1.result()  # Wait for first thread to finish

    def test_file_lock_multiple_readers_sequential(self, temp_file):
        """Test multiple sequential reads work correctly."""
        for i in range(5):
            with file_lock(temp_file, timeout=5.0) as f:
                content = f.read()
                assert '{"test": "data"}' in content

    def test_file_lock_creates_file_if_not_exists(self):
        """Test that lock creates file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = Path(temp_dir) / "new_file.json"

            assert not temp_file.exists()

            with file_lock(temp_file, timeout=5.0) as f:
                assert temp_file.exists()

            # Cleanup
            temp_file.unlink()


class TestAtomicWrite:
    """Test atomic write functionality."""

    def test_atomic_write_creates_file(self):
        """Test atomic write creates new file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            content = '{"key": "value"}'

            atomic_write(file_path, content)

            assert file_path.exists()
            with open(file_path, 'r') as f:
                assert f.read() == content

    def test_atomic_write_overwrites_file(self):
        """Test atomic write overwrites existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write('{"old": "data"}')
            file_path = Path(f.name)

        try:
            new_content = '{"new": "data"}'
            atomic_write(file_path, new_content)

            with open(file_path, 'r') as f:
                assert f.read() == new_content
        finally:
            file_path.unlink()

    def test_atomic_write_concurrent(self):
        """Test atomic writes don't corrupt file under concurrent access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "concurrent_test.json"

            def write_data(thread_id):
                content = json.dumps({"thread_id": thread_id, "data": "x" * 100})
                atomic_write(file_path, content)
                return thread_id

            # Perform 10 concurrent writes
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(write_data, i) for i in range(10)]
                results = [f.result() for f in as_completed(futures)]

            # File should be valid JSON
            with open(file_path, 'r') as f:
                data = json.load(f)
                assert "thread_id" in data
                assert "data" in data
                assert data["thread_id"] in range(10)


class TestConcurrentMemoryOperations:
    """Test concurrent memory operations with file locking."""

    @pytest.fixture
    def temp_memory_file(self):
        """Create a temporary memory file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            initial_data = {
                "version": "2.0",
                "entries": [],
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }
            json.dump(initial_data, f)
            temp_path = Path(f.name)

        yield temp_path

        if temp_path.exists():
            temp_path.unlink()

    def test_concurrent_reads(self, temp_memory_file):
        """Test multiple concurrent reads work correctly."""
        def read_memory():
            with file_lock(temp_memory_file, timeout=5.0) as f:
                data = json.load(f)
                return len(data.get("entries", []))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_memory) for _ in range(20)]
            results = [f.result() for f in as_completed(futures)]

            # All reads should return 0 (empty entries)
            assert all(r == 0 for r in results)

    def test_concurrent_writes(self, temp_memory_file):
        """Test multiple concurrent writes maintain data integrity."""
        def add_entry(entry_id):
            with file_lock(temp_memory_file, timeout=10.0) as f:
                f.seek(0)
                data = json.load(f)

                # Add new entry
                data["entries"].append({
                    "entry_id": f"entry-{entry_id}",
                    "content": f"Content {entry_id}"
                })

                # Write back (using atomic write would be better in production)
                f.seek(0)
                f.truncate()
                json.dump(data, f)

            return entry_id

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(add_entry, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        # Verify all entries were added
        with open(temp_memory_file, 'r') as f:
            data = json.load(f)
            assert len(data["entries"]) == 10
            entry_ids = {e["entry_id"] for e in data["entries"]}
            assert len(entry_ids) == 10  # All unique

    def test_mixed_concurrent_operations(self, temp_memory_file):
        """Test mixed concurrent reads and writes."""
        def read_count():
            time.sleep(0.01)  # Small delay to increase contention
            with file_lock(temp_memory_file, timeout=5.0) as f:
                data = json.load(f)
                return len(data.get("entries", []))

        def write_entry(entry_id):
            time.sleep(0.01)
            with file_lock(temp_memory_file, timeout=5.0) as f:
                f.seek(0)
                data = json.load(f)
                data["entries"].append({"entry_id": f"entry-{entry_id}"})
                f.seek(0)
                f.truncate()
                json.dump(data, f)
            return entry_id

        with ThreadPoolExecutor(max_workers=10) as executor:
            # Mix of reads and writes
            futures = []
            for i in range(5):
                futures.append(executor.submit(write_entry, i))
                futures.append(executor.submit(read_count))

            results = [f.result() for f in as_completed(futures)]

        # File should be valid and have 5 entries
        with open(temp_memory_file, 'r') as f:
            data = json.load(f)
            assert len(data["entries"]) == 5


class TestRetryLogic:
    """Test exponential backoff retry logic."""

    def test_retry_backoff_timing(self, temp_memory_file=None):
        """Test that retry delays follow exponential backoff."""
        if temp_memory_file is None:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write('{"test": "data"}')
                temp_memory_file = Path(f.name)

        acquisition_times = []

        def acquire_with_delay():
            start = time.time()
            with file_lock(temp_memory_file, timeout=5.0) as f:
                elapsed = time.time() - start
                acquisition_times.append(elapsed)
                time.sleep(0.5)  # Hold lock

        try:
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(acquire_with_delay) for _ in range(3)]
                for f in as_completed(futures):
                    f.result()

            # Each subsequent lock should wait longer
            acquisition_times.sort()
            assert acquisition_times[0] < 0.1  # First gets it immediately
            assert acquisition_times[1] > 0.4  # Second waits for first
        finally:
            if temp_memory_file.exists():
                temp_memory_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
