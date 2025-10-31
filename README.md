# MCP Agent Memory - v2.0

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](./tests)

**Production-ready MCP server providing shared memory for multi-agent collaboration.**

---

## Overview

MCP Agent Memory is an enhanced Model Context Protocol (MCP) server that enables multiple AI agents (like Claude Code instances) to communicate asynchronously through a shared memory space. Think of it as a sophisticated shared notepad where AI agents can leave messages, search for information, and coordinate their work.

### Key Features

- 🔒 **Concurrency Safe** - File locking for shared environments
- 📝 **Full CRUD** - Create, Read, Update, Delete operations
- 🔍 **Advanced Search** - Full-text search across all fields
- 🏷️ **Organization** - Tags, priority levels, metadata
- 📊 **Analytics** - Comprehensive memory statistics
- 💾 **Reliable** - Automatic backups and corruption recovery
- 📋 **Structured Logging** - Complete operation visibility
- 🛡️ **Health Monitoring** - Built-in health check system

---

## Quick Start

### Installation

1. **Clone or download** this repository
2. **Install dependencies:**
   ```bash
   pip install mcp pydantic
   ```
3. **Run the server:**
   ```bash
   python3 shared_memory_mcp.py
   ```

### Basic Usage

```python
# Add a memory entry
await add_memory(
    agent_name="claude-alpha",
    content="Analysis complete. Found 3 key insights.",
    tags=["analysis", "complete"],
    priority="high"
)

# Search for entries
results = await search_memory(query="analysis")

# Get statistics
stats = await get_memory_stats()
```

### Configuration

Add to your Claude Code config (`~/.claudeCode/config.json`):

```json
{
  "mcpServers": {
    "shared-memory": {
      "command": "python3",
      "args": ["/path/to/shared_memory_mcp.py"]
    }
  }
}
```

---

## What's New in v2.0

### New Tools (6 total)
- ✅ `update_memory` - Modify existing entries
- ✅ `delete_memory` - Remove specific entries
- ✅ `get_memory` - Retrieve single entry by ID
- ✅ `search_memory` - Full-text search
- ✅ `get_memory_stats` - Memory analytics
- ✅ `health_check` - System health monitoring

### Enhanced Tools
- ⚡ `add_memory` - Now supports tags, priority, metadata
- ⚡ `read_memory` - Advanced filtering and sorting
- ⚡ `clear_memory` - Auto-backup before clearing

### Core Improvements
- 🔒 Thread-safe file locking
- 💾 Automatic backups (keeps 10)
- 📝 Structured logging
- 🔄 Auto-rotation at 1000 entries
- 🛡️ Corruption recovery
- 🆔 Unique entry IDs (UUID)

**Zero breaking changes!** All v1 code works without modification.

---

## Architecture

```
MCP Agent Memory v2.0
├── shared_memory_mcp.py      # Main server (9 MCP tools)
├── utils/
│   ├── file_lock.py           # Concurrency safety
│   └── logger.py              # Structured logging
├── tests/
│   ├── test_memory_operations.py
│   └── test_concurrency.py
└── docs/
    ├── API_REFERENCE_V2.md    # Complete API docs
    ├── CHANGELOG_V2.md        # Version history
    ├── UPGRADE_GUIDE.md       # v1→v2 migration
    └── IMPLEMENTATION_SUMMARY.md
```

### Storage

```
~/.shared_memory_mcp/
├── memory.json              # Main storage
├── mcp_memory.log          # Rotating logs
└── backups/                # Auto-backups (10 kept)
    └── memory_backup_*.json
```

---

## Documentation

### Getting Started
- 📖 [SHARED_MEMORY_README.md](./SHARED_MEMORY_README.md) - Full user guide
- 🚀 [Quick Start Guide](./archive/QUICKSTART.md) - 5-minute setup

### Reference
- 📚 [API Reference](./docs/API_REFERENCE_V2.md) - Complete API documentation
- 📋 [Changelog](./docs/CHANGELOG_V2.md) - Version 2.0 changes
- ⬆️ [Upgrade Guide](./docs/UPGRADE_GUIDE.md) - Migrate from v1 to v2

### Developer
- 🔧 [Implementation Summary](./docs/IMPLEMENTATION_SUMMARY.md) - Technical details
- 🧪 [Testing Guide](#testing) - How to run tests
- 🏗️ [Architecture Details](#architecture) - System design

---

## API Overview

### Memory Operations

| Tool | Description | Type |
|------|-------------|------|
| `add_memory` | Create new entry with tags/priority | Write |
| `read_memory` | Read with advanced filtering | Read |
| `update_memory` | Modify existing entry | Write |
| `delete_memory` | Remove specific entry | Write |
| `get_memory` | Retrieve single entry by ID | Read |
| `search_memory` | Full-text search | Read |
| `get_memory_stats` | Memory analytics | Read |
| `clear_memory` | Clear all entries | Write |
| `health_check` | System health status | Read |

See [API Reference](./docs/API_REFERENCE_V2.md) for detailed documentation.

---

## Testing

### Run Basic Tests
```bash
python3 run_basic_tests.py
```

### Run Full Test Suite (requires pytest)
```bash
pip install pytest pytest-cov
pytest tests/ -v --cov
```

### Test Coverage
- ✅ 70+ test cases
- ✅ Unit tests (operations, filtering, search)
- ✅ Concurrency tests (locking, atomic writes)
- ✅ Integration tests

---

## Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
python3 run_basic_tests.py

# Type checking
mypy shared_memory_mcp.py

# Linting
ruff check .
```

### Code Quality Tools
- ✅ pytest - Testing framework
- ✅ mypy - Type checking
- ✅ ruff - Linting and formatting
- ✅ pre-commit - Git hooks

---

## Performance

### Typical Operations
- Add entry: 5-15ms (includes backup)
- Read entries: 2-10ms
- Search (100 entries): 1-5ms
- Update/Delete: 5-15ms (includes backup)

### Limits
- Max words per entry: 200
- Max tags per entry: 10
- Max entries before rotation: 1000
- File lock timeout: 10 seconds
- Backup retention: 10 backups

---

## Use Cases

### Multi-Agent Collaboration
```python
# Agent A: Data collector
await add_memory(
    agent_name="data-collector",
    content="Collected 10,000 data points",
    tags=["data", "ready-for-analysis"],
    priority="high"
)

# Agent B: Analyzer picks up work
pending = await read_memory(tags=["ready-for-analysis"])
```

### Task Tracking
```python
# Start task
result = await add_memory(
    agent_name="worker",
    content="Starting analysis...",
    tags=["analysis", "in-progress"],
    priority="high"
)

# Update on completion
await update_memory(
    entry_id=result.entry_id,
    tags=["analysis", "complete"],
    priority="low"
)
```

### Knowledge Base
```python
# Search for information
results = await search_memory(
    query="user behavior insights",
    limit=10
)

# Get statistics
stats = await get_memory_stats()
print(f"Total knowledge: {stats.total_entries} entries")
```

---

## FAQ

**Q: Is v2 compatible with v1 code?**
A: Yes! 100% backward compatible. All v1 code works without changes.

**Q: How does migration work?**
A: Automatic. v2 detects v1 format and migrates on first write.

**Q: Can multiple agents write simultaneously?**
A: Yes! File locking ensures safe concurrent access.

**Q: What happens if storage gets corrupted?**
A: Automatic recovery from the most recent valid backup.

**Q: How much disk space does it use?**
A: ~500-1000 bytes per entry. 1000 entries ≈ 500KB-1MB.

**Q: Can I use it for production?**
A: Yes! v2 is production-ready with reliability features.

See [UPGRADE_GUIDE.md](./docs/UPGRADE_GUIDE.md) for more details.

---

## Troubleshooting

### Common Issues

**File lock timeout**
```bash
# Check for other running instances
ps aux | grep shared_memory_mcp

# Increase timeout in code if needed
```

**JSON parse error**
```bash
# Restore from backup
cp ~/.shared_memory_mcp/backups/memory_backup_*.json \
   ~/.shared_memory_mcp/memory.json
```

**Check system health**
```python
health = await health_check({})
print(health.message)  # "All systems operational"
```

### Logs
```bash
# View logs
tail -f ~/.shared_memory_mcp/mcp_memory.log

# Check for errors
grep ERROR ~/.shared_memory_mcp/mcp_memory.log
```

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

### Code Style
- Use type hints
- Follow existing patterns
- Add docstrings
- Run pre-commit hooks

---

## License

MIT License - See LICENSE file for details

---

## Changelog

### v2.0.0 (2025-10-30)
- ✅ Added concurrency safety (file locking)
- ✅ Added structured logging
- ✅ Added 6 new MCP tools
- ✅ Enhanced data model (tags, priority, metadata)
- ✅ Added automatic backups and recovery
- ✅ Added comprehensive test suite (70+ tests)
- ✅ Added complete documentation
- ✅ Zero breaking changes

See [CHANGELOG_V2.md](./docs/CHANGELOG_V2.md) for detailed history.

---

## Acknowledgments

Built on the Model Context Protocol (MCP) by Anthropic.

Enhanced with production-ready features while maintaining the simplicity and elegance of the original design.

---

## Links

- **Documentation:** [./docs/](./docs/)
- **Tests:** [./tests/](./tests/)
- **API Reference:** [API_REFERENCE_V2.md](./docs/API_REFERENCE_V2.md)
- **MCP Protocol:** https://modelcontextprotocol.io/

---

**Made with ❤️ for multi-agent collaboration**

*Version 2.0.0 - Production Ready* 🚀
