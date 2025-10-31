# Shared Memory MCP Server

A Model Context Protocol (MCP) server that enables multiple AI agents to share a memory scratch space. Perfect for enabling conversations between Claude Code instances or any other MCP-compatible agents.

## Features

- **Shared Memory Space**: Multiple agents can read and write to a common memory
- **Agent Identification**: Each entry records which agent created it
- **Word Limits**: Each entry is limited to 200 words (configurable)
- **Chronological Order**: Memories are returned in the order they were created
- **Multiple Formats**: Support for both JSON and Markdown output
- **Persistent Storage**: Uses a simple JSON file for reliable persistence
- **Filtering**: Filter memories by agent name or limit results

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package installer)

### Setup

1. Install the MCP Python SDK:
```bash
pip install mcp
```

2. Make the server executable:
```bash
chmod +x shared_memory_mcp.py
```

3. Test the server runs correctly:
```bash
python shared_memory_mcp.py --help
```

## Usage with Claude Code

### Single Machine Setup

To connect two Claude Code instances on the same machine:

1. Create or edit your Claude Code MCP configuration file:
   - **macOS/Linux**: `~/.config/claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the shared memory server to both Claude Code instances' config:

```json
{
  "mcpServers": {
    "shared-memory": {
      "command": "python",
      "args": ["/path/to/shared_memory_mcp.py"]
    }
  }
}
```

3. Restart Claude Code instances to load the new MCP server

### Example Conversation Flow

**Claude Code Instance 1 (Alpha):**
```
Human: Add a memory that you're starting to analyze the sales data

Claude: I'll record that in our shared memory.
[calls add_memory tool with agent_name="claude-alpha"]
```

**Claude Code Instance 2 (Beta):**
```
Human: Check the shared memory to see what Alpha is working on

Claude: Let me read the shared memory.
[calls read_memory tool]

I see that claude-alpha has started analyzing the sales data. I can help with 
visualizations once the analysis is complete.

[calls add_memory to respond to Alpha]
```

**Claude Code Instance 1 (Alpha) - Later:**
```
Human: Check if Beta has any updates

Claude: [calls read_memory tool]

Beta has responded! They're ready to help with visualizations once I complete 
the analysis.
```

## Tool Reference

### add_memory

Add a new memory entry to the shared space.

**Parameters:**
- `agent_name` (string, required): Your agent identifier (1-100 chars)
- `content` (string, required): Memory content (max 200 words)

**Example:**
```json
{
  "agent_name": "claude-alpha",
  "content": "I've completed the initial data analysis. Found 3 key trends in Q4 sales..."
}
```

**Returns:**
```json
{
  "success": true,
  "entry_number": 5,
  "timestamp": "2025-10-30T10:30:00Z",
  "agent_name": "claude-alpha",
  "word_count": 12,
  "message": "Memory entry #5 added successfully by claude-alpha"
}
```

### read_memory

Read all memory entries in chronological order.

**Parameters:**
- `response_format` (enum, optional): "markdown" (default) or "json"
- `limit` (integer, optional): Max number of recent entries to return
- `agent_filter` (string, optional): Only show entries from specific agent

**Example:**
```json
{
  "response_format": "markdown",
  "limit": 10
}
```

**Markdown Output:**
```markdown
# Shared Memory

Total entries: 3

## Entry 1: claude-alpha
**Time**: 2025-10-30T10:30:00Z
**Words**: 15/200

Starting analysis of Q4 sales data. Will focus on regional trends first.

---

## Entry 2: claude-beta
**Time**: 2025-10-30T10:32:00Z
**Words**: 12/200

Ready to help with visualizations once analysis is complete.

---
```

**JSON Output:**
```json
{
  "total_entries": 2,
  "entries": [
    {
      "timestamp": "2025-10-30T10:30:00Z",
      "agent_name": "claude-alpha",
      "content": "Starting analysis...",
      "word_count": 15
    }
  ]
}
```

### clear_memory

Clear all memory entries (destructive operation).

**Parameters:**
- `confirm` (boolean, required): Must be `true` to proceed

**Example:**
```json
{
  "confirm": true
}
```

**Returns:**
```json
{
  "success": true,
  "entries_cleared": 5,
  "message": "Successfully cleared 5 memory entries. Memory is now empty."
}
```

## Storage Location

Memory is stored in:
- **macOS/Linux**: `~/.shared_memory_mcp/memory.json`
- **Windows**: `%USERPROFILE%\.shared_memory_mcp\memory.json`

You can manually inspect or edit this file if needed.

## Advanced Configuration

### Custom Storage Location

Set the `MEMORY_FILE` constant in the script:

```python
MEMORY_FILE = Path("/custom/path/to/memory.json")
```

### Adjust Word Limit

Change the `MAX_WORDS_PER_ENTRY` constant:

```python
MAX_WORDS_PER_ENTRY = 500  # Allow longer entries
```

### Character Limit for Responses

Modify `CHARACTER_LIMIT` to control response truncation:

```python
CHARACTER_LIMIT = 50000  # Allow larger responses
```

## Use Cases

### Multi-Agent Collaboration
- Two agents working on different parts of a project
- One agent doing research, another doing analysis
- Coordinating tasks across multiple AI instances

### Async Communication
- Leave messages for later retrieval
- Build conversation history over time
- Track progress across sessions

### Debugging & Development
- Monitor what different agent instances are thinking
- Trace decision-making processes
- Share context between development sessions

## Troubleshooting

### Server Won't Start
- Verify Python version: `python --version` (need 3.10+)
- Check MCP SDK installed: `pip show mcp`
- Look for syntax errors: `python -m py_compile shared_memory_mcp.py`

### Claude Code Not Finding Tools
- Confirm config file path is correct for your OS
- Restart Claude Code after config changes
- Check logs in Claude Code for MCP connection errors

### Memory Not Persisting
- Verify write permissions for storage directory
- Check disk space availability
- Look for JSON errors in the memory file

### Word Count Exceeded
- Content is limited to 200 words per entry
- Break longer thoughts into multiple entries
- Or increase `MAX_WORDS_PER_ENTRY` in the script

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Claude Code    │         │  Shared Memory   │         │  Claude Code    │
│  Instance 1     │────────▶│   MCP Server     │◀────────│  Instance 2     │
│  (Alpha)        │         │                  │         │  (Beta)         │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  memory.json    │
                            │  (Persistent    │
                            │   Storage)      │
                            └─────────────────┘
```

## Contributing

Feel free to extend this server with additional features:
- **Tags/Categories**: Add categorization to memories
- **Search**: Implement full-text search across memories
- **Expiration**: Auto-delete old memories after a time period
- **Statistics**: Track agent activity and memory usage
- **Encryption**: Add encryption for sensitive memories

## License

This is example code - feel free to modify and use as needed for your projects.

## Support

For MCP protocol documentation, visit: https://modelcontextprotocol.io
For Claude Code documentation, visit: https://docs.claude.com/en/docs/claude-code
