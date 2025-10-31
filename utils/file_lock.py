"""
File Locking Utility
====================

Cross-platform file locking mechanism with retry logic to prevent race conditions
during concurrent access to the memory storage file.

Supports:
- Unix/Linux/Mac: fcntl-based locking
- Windows: msvcrt-based locking
- Automatic retry with exponential backoff
- Context manager for safe lock acquisition/release
"""

import time
import platform
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

# Platform-specific imports
_IS_WINDOWS = platform.system() == "Windows"

if _IS_WINDOWS:
    import msvcrt
else:
    import fcntl


class FileLockError(Exception):
    """Raised when file locking operations fail."""
    pass


class FileLockTimeout(FileLockError):
    """Raised when unable to acquire lock within timeout period."""
    pass


@contextmanager
def file_lock(
    file_path: Path,
    timeout: float = 10.0,
    retry_delay: float = 0.1,
    max_retry_delay: float = 2.0
):
    """
    Context manager for acquiring an exclusive lock on a file.

    Uses platform-specific locking mechanisms:
    - Unix/Linux/Mac: fcntl.flock()
    - Windows: msvcrt.locking()

    Implements exponential backoff retry logic to handle contention.

    Args:
        file_path (Path): Path to the file to lock
        timeout (float): Maximum time to wait for lock in seconds (default: 10.0)
        retry_delay (float): Initial delay between retries in seconds (default: 0.1)
        max_retry_delay (float): Maximum delay between retries in seconds (default: 2.0)

    Yields:
        file: Open file handle with exclusive lock acquired

    Raises:
        FileLockTimeout: If unable to acquire lock within timeout period
        FileLockError: If locking operation fails

    Example:
        >>> with file_lock(Path("data.json")) as f:
        ...     data = json.load(f)
        ...     # modify data
        ...     f.seek(0)
        ...     f.truncate()
        ...     json.dump(data, f)
    """
    file_handle = None
    start_time = time.time()
    current_retry_delay = retry_delay

    try:
        # Ensure file exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.touch()

        # Open file for reading and writing
        file_handle = open(file_path, 'r+')

        # Try to acquire lock with exponential backoff
        while True:
            try:
                if _IS_WINDOWS:
                    # Windows: Lock first byte of file
                    msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    # Unix: Use exclusive non-blocking lock
                    fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                # Lock acquired successfully
                break

            except (IOError, OSError) as e:
                # Lock is held by another process
                elapsed = time.time() - start_time

                if elapsed >= timeout:
                    raise FileLockTimeout(
                        f"Could not acquire lock on {file_path} within {timeout}s. "
                        f"Another process may be using the file."
                    ) from e

                # Wait with exponential backoff
                time.sleep(current_retry_delay)
                current_retry_delay = min(current_retry_delay * 2, max_retry_delay)

        # Yield the locked file handle
        yield file_handle

    except FileLockTimeout:
        raise
    except Exception as e:
        raise FileLockError(f"Failed to acquire lock on {file_path}: {e}") from e

    finally:
        # Release lock and close file
        if file_handle and not file_handle.closed:
            try:
                if _IS_WINDOWS:
                    # Windows: Unlock first byte
                    msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    # Unix: Release exclusive lock
                    fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
            except Exception:
                # Ignore errors during unlock (file may already be closed)
                pass
            finally:
                file_handle.close()


def atomic_write(file_path: Path, content: str) -> None:
    """
    Atomically write content to a file using temp file + rename pattern.

    This prevents partial writes and corruption if the process is interrupted.

    Process:
    1. Write to temporary file in same directory
    2. Flush and fsync to ensure data is written to disk
    3. Atomically rename temp file to target file

    Args:
        file_path (Path): Target file path
        content (str): Content to write

    Raises:
        OSError: If write or rename operations fail

    Example:
        >>> atomic_write(Path("data.json"), json.dumps(data, indent=2))
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory (ensures same filesystem for atomic rename)
    temp_path = file_path.parent / f".{file_path.name}.tmp"

    try:
        # Write to temp file
        with open(temp_path, 'w') as f:
            f.write(content)
            f.flush()
            # Ensure data is written to disk
            import os
            os.fsync(f.fileno())

        # Atomically rename temp file to target
        # On Unix: atomic operation
        # On Windows: not atomic, but close enough for our use case
        temp_path.replace(file_path)

    except Exception:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise


# Convenience function for locked read operations
@contextmanager
def locked_read(file_path: Path, timeout: float = 10.0):
    """
    Context manager for reading a file with shared lock.

    Args:
        file_path (Path): Path to file to read
        timeout (float): Maximum time to wait for lock

    Yields:
        str: File contents

    Example:
        >>> with locked_read(Path("data.json")) as content:
        ...     data = json.loads(content)
    """
    with file_lock(file_path, timeout=timeout) as f:
        content = f.read()
        yield content


# Convenience function for locked write operations
@contextmanager
def locked_write(file_path: Path, timeout: float = 10.0):
    """
    Context manager for writing to a file with exclusive lock.

    Args:
        file_path (Path): Path to file to write
        timeout (float): Maximum time to wait for lock

    Yields:
        callable: Function to call with content to write atomically

    Example:
        >>> with locked_write(Path("data.json")) as write:
        ...     write(json.dumps(data, indent=2))
    """
    def write_fn(content: str):
        atomic_write(file_path, content)

    with file_lock(file_path, timeout=timeout):
        yield write_fn
