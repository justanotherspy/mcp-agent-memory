# Quick Start Guide - Shared Memory MCP Server

Get your multi-agent conversation system up and running in 5 minutes!

## 1. Install Dependencies

```bash
pip install mcp
```

## 2. Test the Server

```bash
# Verify Python syntax
python -m py_compile shared_memory_mcp.py

# Run the demo
python demo_shared_memory.py
```

Expected output: A simulated conversation between two agents with JSON/Markdown output.

## 3. Configure Claude Code

### Find your config file location:
- **macOS/Linux**: `~/.config/claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Add the server configuration:

```json
{
  "mcpServers": {
    "shared-memory": {
      "command": "python",
      "args": ["/full/path/to/shared_memory_mcp.py"]
    }
  }
}
```

**Important**: Use the absolute path to `shared_memory_mcp.py`!

To get the absolute path:
```bash
# macOS/Linux
pwd  # then append /shared_memory_mcp.py

# Or use this helper:
echo "$(pwd)/shared_memory_mcp.py"
```

## 4. Restart Claude Code

Both Claude Code instances need to restart to load the MCP server.

## 5. Test It Out!

### In Claude Code Instance 1:
```
Human: Use the add_memory tool to record that you're starting work on project analysis

Claude: [calls add_memory with agent_name="instance-1"]
Done! I've recorded that I'm starting the project analysis.
```

### In Claude Code Instance 2:
```
Human: Use read_memory to see what the other instance is working on

Claude: [calls read_memory]
I can see instance-1 has started working on project analysis!
```

### Continue the conversation:
```
Instance 2 Human: Add a memory that you'll handle the data visualization

Claude: [calls add_memory with agent_name="instance-2"]

Instance 1 Human: Check for any updates

Claude: [calls read_memory]
Instance-2 has offered to handle the visualization work!
```

## 6. View Memory Storage

You can inspect the raw memory data at:
```bash
# macOS/Linux
cat ~/.shared_memory_mcp/memory.json

# Windows
type %USERPROFILE%\.shared_memory_mcp\memory.json
```

## Common Issues

### "Module 'mcp' not found"
```bash
pip install mcp
```

### "Command not found: python"
Try `python3` instead:
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

### "Tools not showing up in Claude Code"
1. Verify config file location is correct
2. Check absolute path is correct
3. Restart Claude Code completely
4. Check Claude Code logs for errors

## Advanced Usage

### Filter by agent:
```
Human: Show me only messages from instance-1
Claude: [calls read_memory with agent_filter="instance-1"]
```

### Limit results:
```
Human: Show me the last 5 messages
Claude: [calls read_memory with limit=5]
```

### Clear memory:
```
Human: Clear all shared memory
Claude: [calls clear_memory with confirm=true]
```

## Next Steps

- Read SHARED_MEMORY_README.md for detailed documentation
- Customize agent names for your workflow
- Experiment with different conversation patterns
- Consider extending the server with custom features

Happy multi-agent collaborating! 🤖🤖
