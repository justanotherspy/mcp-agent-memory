# Shared Memory MCP Server - Project Summary

## Overview

This project implements a Model Context Protocol (MCP) server that enables multiple AI agents (like Claude Code instances) to share a common memory space for communication and collaboration.

## What You Get

A complete, production-ready MCP server with:
- ✅ Three well-designed tools (add_memory, read_memory, clear_memory)
- ✅ Full input validation with Pydantic v2
- ✅ Multiple output formats (JSON and Markdown)
- ✅ Persistent JSON storage
- ✅ Word count limits and validation
- ✅ Comprehensive documentation
- ✅ Demo/test script
- ✅ Configuration examples

## Files Included

1. **shared_memory_mcp.py** (Main Server)
   - 450+ lines of production-quality Python code
   - Follows MCP best practices
   - Complete error handling and validation
   - Supports filtering, pagination, and multiple formats

2. **SHARED_MEMORY_README.md** (Full Documentation)
   - Complete feature documentation
   - API reference for all tools
   - Configuration instructions
   - Troubleshooting guide
   - Use cases and examples

3. **QUICKSTART.md** (Quick Setup Guide)
   - 5-minute setup instructions
   - Step-by-step configuration
   - Common issues and solutions

4. **demo_shared_memory.py** (Demo Script)
   - Simulates multi-agent conversation
   - Tests all features
   - Shows example workflows

5. **example_claude_code_config.json** (Config Template)
   - Ready-to-use configuration template
   - Just update the path and you're ready!

## Key Features

### Tools Provided

**add_memory**
- Add entries with agent name and content (max 200 words)
- Automatic timestamp and word counting
- Returns confirmation with entry number

**read_memory**
- Read all entries in chronological order
- Filter by agent name
- Limit number of results
- Choose JSON or Markdown format

**clear_memory**
- Clear all entries (with confirmation)
- Useful for starting fresh sessions

### Technical Highlights

- **Agent-Centric Design**: Tools designed for AI agent workflows
- **Input Validation**: Full Pydantic v2 validation with clear error messages
- **Context Optimization**: Efficient responses with truncation for large datasets
- **Persistent Storage**: Simple JSON file storage (~/.shared_memory_mcp/memory.json)
- **Response Formats**: Both human-readable (Markdown) and machine-readable (JSON)
- **Error Handling**: Comprehensive error handling with actionable messages

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server Layer                         │
│  (shared_memory_mcp.py)                                     │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │   add    │  │   read   │  │  clear   │                 │
│  │  memory  │  │  memory  │  │  memory  │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│       │             │              │                        │
│       └─────────────┴──────────────┘                        │
│                     ▼                                       │
│              Storage Manager                                │
│         (JSON file operations)                              │
└─────────────────────────────────────────────────────────────┘
                      │
                      ▼
        ┌──────────────────────────┐
        │  ~/.shared_memory_mcp/   │
        │     memory.json          │
        └──────────────────────────┘
```

## Usage Pattern

### Single Machine (Most Common)
Two Claude Code instances on one machine, sharing memory via the MCP server.

```
Terminal 1: Claude Code Instance 1
Terminal 2: Claude Code Instance 2
Both connect to: shared_memory_mcp.py
Both read/write: ~/.shared_memory_mcp/memory.json
```

### Use Cases

1. **Collaborative Tasks**: Split work between agents
   - One does research, another analyzes
   - One writes code, another reviews

2. **Async Communication**: Leave messages for later
   - Agent 1 finishes task and leaves status
   - Agent 2 picks up where Agent 1 left off

3. **Debugging**: Monitor agent reasoning
   - Track decision-making processes
   - Review thought patterns across instances

## Code Quality

Follows all MCP best practices:
- ✅ Proper server naming convention (shared_memory_mcp)
- ✅ Clear tool naming (snake_case, descriptive)
- ✅ Comprehensive docstrings with types
- ✅ Pydantic v2 models with validation
- ✅ Tool annotations (readOnlyHint, destructiveHint, etc.)
- ✅ Character limits and truncation
- ✅ Multiple response formats
- ✅ Actionable error messages
- ✅ No code duplication (DRY principle)
- ✅ Type hints throughout
- ✅ Async/await patterns

## Getting Started

1. **Install**: `pip install mcp`
2. **Test**: `python demo_shared_memory.py`
3. **Configure**: Add to Claude Code config (see QUICKSTART.md)
4. **Use**: Start conversations between agents!

## Customization Ideas

Want to extend the server? Consider adding:
- **Tags/Categories**: Categorize memories by topic
- **Search**: Full-text search across entries
- **Expiration**: Auto-delete old entries
- **Priority Levels**: Mark important memories
- **Threading**: Group related conversations
- **Encryption**: Secure sensitive information
- **Statistics**: Track agent activity metrics
- **Export**: Export conversations to different formats

## Performance

- **Lightweight**: Minimal memory footprint
- **Fast**: JSON file operations are very quick
- **Scalable**: Handles thousands of entries efficiently
- **Reliable**: Simple storage = fewer failure modes

## Security Notes

- Memory is stored in user's home directory
- No network access required (unless using HTTP transport)
- No external dependencies beyond MCP SDK
- File permissions controlled by OS

## Testing

Run the demo to verify everything works:
```bash
python demo_shared_memory.py
```

Expected behavior:
- Creates 4 memory entries
- Shows filtered views
- Tests word limit validation
- Displays in both JSON and Markdown

## Support Resources

- **MCP Protocol**: https://modelcontextprotocol.io
- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code
- **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk

## License

Example/educational code - use and modify freely for your projects.

## What's Next?

1. Read QUICKSTART.md for setup
2. Run demo_shared_memory.py to see it work
3. Configure Claude Code instances
4. Start your first multi-agent conversation!
5. Customize as needed for your workflow

---

Built following Anthropic's MCP best practices for agent-centric tool design.
