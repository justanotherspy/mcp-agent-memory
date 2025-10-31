# API Reference - Version 2.0

Complete reference for all MCP tools in the Shared Memory server v2.0.

---

## Table of Contents

1. [add_memory](#add_memory)
2. [read_memory](#read_memory)
3. [update_memory](#update_memory)
4. [delete_memory](#delete_memory)
5. [get_memory](#get_memory)
6. [search_memory](#search_memory)
7. [get_memory_stats](#get_memory_stats)
8. [clear_memory](#clear_memory)
9. [health_check](#health_check)

---

## add_memory

Add a new memory entry to the shared memory space.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `agent_name` | string | ✅ | - | Name of the agent (1-100 chars) |
| `content` | string | ✅ | - | Memory content (max 200 words) |
| `tags` | array[string] | ❌ | [] | Tags for categorization (max 10) |
| `priority` | enum | ❌ | "medium" | Priority: "low", "medium", "high" |
| `metadata` | object | ❌ | {} | Custom metadata (any JSON object) |

### Returns

```json
{
  "success": true,
  "entry_id": "550e8400-e29b-41d4-a716-446655440000",
  "entry_number": 42,
  "timestamp": "2025-10-30T12:34:56.789Z",
  "agent_name": "claude-alpha",
  "word_count": 15,
  "tags": ["analysis", "complete"],
  "priority": "high",
  "message": "Memory entry #42 added successfully by claude-alpha"
}
```

### Example

```javascript
await add_memory({
  agent_name: "claude-alpha",
  content: "Analysis complete. Found 3 key insights in user behavior data.",
  tags: ["analysis", "insights", "user-behavior"],
  priority: "high",
  metadata: {
    project: "user-research-2025",
    confidence: 0.95,
    data_points: 10000
  }
});
```

### Annotations
- **readOnlyHint:** false
- **destructiveHint:** false
- **idempotentHint:** false

---

## read_memory

Read memory entries with advanced filtering and sorting.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `response_format` | enum | ❌ | "markdown" | "markdown" or "json" |
| `limit` | integer | ❌ | null | Max entries to return (1-1000) |
| `agent_filter` | string | ❌ | null | Filter by agent name |
| `tags` | array[string] | ❌ | null | Filter by tags (AND logic) |
| `priority` | enum | ❌ | null | Filter by priority level |
| `sort_order` | enum | ❌ | "chronological" | "chronological", "reverse", "priority" |

### Returns (JSON format)

```json
{
  "total_entries": 42,
  "entries": [
    {
      "entry_id": "uuid",
      "timestamp": "2025-10-30T12:00:00Z",
      "agent_name": "claude-alpha",
      "content": "Message content here",
      "word_count": 15,
      "tags": ["tag1", "tag2"],
      "priority": "high",
      "metadata": {},
      "updated_at": null
    }
  ]
}
```

### Returns (Markdown format)

```markdown
# Shared Memory

Total entries: 42

## Entry 1: claude-alpha
**ID**: `550e8400-e29b-41d4-a716-446655440000`
**Time**: 2025-10-30T12:00:00Z
**Words**: 15/200
**Priority**: high
**Tags**: analysis, complete

Message content here

---
```

### Examples

```javascript
// Get all high-priority entries
await read_memory({
  priority: "high",
  sort_order: "reverse",  // Newest first
  response_format: "markdown"
});

// Get last 10 entries from specific agent
await read_memory({
  agent_filter: "claude-alpha",
  limit: 10,
  sort_order: "reverse"
});

// Get entries with specific tags
await read_memory({
  tags: ["analysis", "complete"],
  response_format: "json"
});
```

### Annotations
- **readOnlyHint:** true
- **destructiveHint:** false
- **idempotentHint:** true

---

## update_memory

Update an existing memory entry. Only specified fields are updated.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entry_id` | string | ✅ | - | UUID of entry to update |
| `content` | string | ❌ | unchanged | New content (max 200 words) |
| `tags` | array[string] | ❌ | unchanged | New tags (replaces existing) |
| `priority` | enum | ❌ | unchanged | New priority level |
| `metadata` | object | ❌ | unchanged | New metadata (replaces existing) |

### Returns

```json
{
  "success": true,
  "entry_id": "550e8400-e29b-41d4-a716-446655440000",
  "updated_fields": ["tags", "priority"],
  "updated_at": "2025-10-30T13:00:00Z",
  "message": "Entry 550e8400-e29b-41d4-a716-446655440000 updated successfully"
}
```

### Example

```javascript
// Update tags and priority after review
await update_memory({
  entry_id: "550e8400-e29b-41d4-a716-446655440000",
  tags: ["analysis", "reviewed", "archived"],
  priority: "low"
});

// Update just the content
await update_memory({
  entry_id: "550e8400-e29b-41d4-a716-446655440000",
  content: "Updated analysis: Found 5 insights instead of 3."
});
```

### Annotations
- **readOnlyHint:** false
- **destructiveHint:** false
- **idempotentHint:** true (same update multiple times = same result)

---

## delete_memory

Delete a specific memory entry by ID.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entry_id` | string | ✅ | UUID of entry to delete |

### Returns

```json
{
  "success": true,
  "entry_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_name": "claude-alpha",
  "deleted_at": "2025-10-30T14:00:00Z",
  "remaining_entries": 41,
  "message": "Entry 550e8400-e29b-41d4-a716-446655440000 deleted successfully"
}
```

### Example

```javascript
await delete_memory({
  entry_id: "550e8400-e29b-41d4-a716-446655440000"
});
```

### Annotations
- **readOnlyHint:** false
- **destructiveHint:** true (cannot be undone)
- **idempotentHint:** true (deleting twice = same result)

---

## get_memory

Retrieve a single memory entry by its ID.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `entry_id` | string | ✅ | - | UUID of entry to retrieve |
| `response_format` | enum | ❌ | "json" | "markdown" or "json" |

### Returns (JSON format)

```json
{
  "success": true,
  "entry": {
    "entry_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-10-30T12:00:00Z",
    "agent_name": "claude-alpha",
    "content": "Message content",
    "word_count": 15,
    "tags": ["tag1"],
    "priority": "high",
    "metadata": {},
    "updated_at": null
  }
}
```

### Example

```javascript
// Get specific entry in JSON format
const entry = await get_memory({
  entry_id: "550e8400-e29b-41d4-a716-446655440000",
  response_format: "json"
});

// Get in markdown format
await get_memory({
  entry_id: "550e8400-e29b-41d4-a716-446655440000",
  response_format: "markdown"
});
```

### Annotations
- **readOnlyHint:** true
- **destructiveHint:** false
- **idempotentHint:** true

---

## search_memory

Search memory entries for a query string. Searches across content, agent names, and tags.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ | - | Search query (1-200 chars) |
| `case_sensitive` | boolean | ❌ | false | Case-sensitive search |
| `response_format` | enum | ❌ | "markdown" | "markdown" or "json" |
| `limit` | integer | ❌ | null | Max results to return (1-1000) |

### Returns (JSON format)

```json
{
  "success": true,
  "query": "analysis",
  "total_results": 5,
  "entries": [
    { /* entry objects */ }
  ]
}
```

### Examples

```javascript
// Case-insensitive search
await search_memory({
  query: "user behavior",
  case_sensitive: false,
  limit: 10
});

// Case-sensitive search in markdown
await search_memory({
  query: "CRITICAL",
  case_sensitive: true,
  response_format: "markdown"
});

// Search for tag
await search_memory({
  query: "analysis"  // Matches content, agent names, and tags
});
```

### Annotations
- **readOnlyHint:** true
- **destructiveHint:** false
- **idempotentHint:** true

---

## get_memory_stats

Get comprehensive statistics about the shared memory.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `response_format` | enum | ❌ | "json" | "markdown" or "json" |

### Returns

```json
{
  "success": true,
  "total_entries": 42,
  "total_words": 1250,
  "average_words_per_entry": 29.8,
  "agent_activity": {
    "claude-alpha": 25,
    "claude-beta": 17
  },
  "top_agents": [
    ["claude-alpha", 25],
    ["claude-beta", 17]
  ],
  "tag_usage": {
    "analysis": 15,
    "complete": 12,
    "review": 8
  },
  "top_tags": [
    ["analysis", 15],
    ["complete", 12],
    ["review", 8]
  ],
  "priority_distribution": {
    "low": 10,
    "medium": 20,
    "high": 12
  },
  "date_range": {
    "earliest": "2025-10-01T00:00:00Z",
    "latest": "2025-10-30T14:00:00Z"
  },
  "storage_size_bytes": 52480,
  "storage_size_kb": 51.25,
  "max_entries": 1000,
  "entries_until_rotation": 958
}
```

### Example

```javascript
// Get stats in JSON
const stats = await get_memory_stats({ response_format: "json" });

// Get stats in markdown (formatted report)
await get_memory_stats({ response_format: "markdown" });
```

### Annotations
- **readOnlyHint:** true
- **destructiveHint:** false
- **idempotentHint:** true

---

## clear_memory

Clear all memory entries. Creates automatic backup before clearing.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `confirm` | boolean | ✅ | Must be true to proceed |

### Returns

```json
{
  "success": true,
  "entries_cleared": 42,
  "cleared_at": "2025-10-30T15:00:00Z",
  "message": "Successfully cleared 42 memory entries. Backup created."
}
```

### Example

```javascript
// Clear all memory (requires explicit confirmation)
await clear_memory({ confirm: true });

// Will fail if confirm is false
await clear_memory({ confirm: false });
// Returns: {"success": false, "error": "Confirmation required..."}
```

### Annotations
- **readOnlyHint:** false
- **destructiveHint:** true (cannot be undone, backup created)
- **idempotentHint:** true

---

## health_check

Check the health status of the memory system.

### Parameters

Empty object `{}` required.

### Returns

```json
{
  "success": true,
  "timestamp": "2025-10-30T15:30:00Z",
  "checks": {
    "storage_file": {
      "status": "ok",
      "path": "/Users/name/.shared_memory_mcp/memory.json",
      "exists": true,
      "size_bytes": 52480
    },
    "file_locking": {
      "status": "ok",
      "message": "File locking operational"
    },
    "json_parsing": {
      "status": "ok",
      "entry_count": 42
    },
    "backup_system": {
      "status": "ok",
      "backup_dir": "/Users/name/.shared_memory_mcp/backups",
      "backup_count": 10
    }
  },
  "message": "All systems operational"
}
```

### Example

```javascript
// Check system health
const health = await health_check({});

if (health.success) {
  console.log("System is healthy");
} else {
  console.error("System health check failed:", health.message);
}
```

### Annotations
- **readOnlyHint:** true
- **destructiveHint:** false
- **idempotentHint:** true

---

## Common Patterns

### Pattern 1: Add and Track
```javascript
// Add entry
const result = await add_memory({
  agent_name: "analyzer",
  content: "Starting analysis...",
  tags: ["analysis", "in-progress"],
  priority: "high"
});

// Save entry_id for later updates
const entryId = result.entry_id;

// Update when done
await update_memory({
  entry_id: entryId,
  tags: ["analysis", "complete"],
  priority: "low",
  content: "Analysis complete. Found 5 insights."
});
```

### Pattern 2: Search and Modify
```javascript
// Search for entries needing review
const results = await search_memory({
  query: "needs review",
  response_format: "json"
});

// Update each entry
for (const entry of results.entries) {
  await update_memory({
    entry_id: entry.entry_id,
    tags: [...entry.tags, "reviewed"],
    priority: "low"
  });
}
```

### Pattern 3: Agent Handoff
```javascript
// Agent A completes work
await add_memory({
  agent_name: "agent-a",
  content: "Data collection complete. Ready for analysis.",
  tags: ["data", "ready-for-analysis"],
  priority: "high",
  metadata: { task: "data-collection", next: "agent-b" }
});

// Agent B picks up work
const pending = await read_memory({
  tags: ["ready-for-analysis"],
  sort_order: "priority"
});
```

### Pattern 4: Periodic Cleanup
```javascript
// Get statistics
const stats = await get_memory_stats({ response_format: "json" });

// If nearing rotation, clean up old low-priority entries
if (stats.entries_until_rotation < 100) {
  const oldEntries = await read_memory({
    priority: "low",
    response_format: "json",
    limit: 50
  });

  // Archive or delete old entries
  for (const entry of oldEntries.entries) {
    await delete_memory({ entry_id: entry.entry_id });
  }
}
```

---

## Error Handling

All tools return JSON with consistent error format:

```json
{
  "success": false,
  "error": "Detailed error message here"
}
```

Common errors:
- **Validation errors**: Field validation failed (word count, length, etc.)
- **Not found**: Entry ID doesn't exist
- **Invalid format**: Invalid entry_id format
- **Lock timeout**: Unable to acquire file lock within timeout
- **Storage corruption**: JSON file corrupted (attempts recovery)

Always check `success` field before processing results.

---

## Best Practices

1. **Always check success field**
   ```javascript
   const result = await add_memory({...});
   if (!result.success) {
     console.error("Failed:", result.error);
   }
   ```

2. **Use meaningful tags**
   - Keep tags short (1-2 words)
   - Use lowercase
   - Be consistent (e.g., "in-progress" not "in_progress" or "inProgress")

3. **Set appropriate priority**
   - High: Urgent, needs immediate attention
   - Medium: Normal operations (default)
   - Low: Archive, completed, low importance

4. **Include useful metadata**
   ```javascript
   metadata: {
     timestamp: Date.now(),
     source: "data-pipeline-v2",
     confidence: 0.95
   }
   ```

5. **Update when task state changes**
   - Add entry when starting task
   - Update tags/priority as work progresses
   - Update content with results when complete

6. **Clean up periodically**
   - Delete obsolete entries
   - Archive completed work
   - Monitor storage stats

7. **Use health_check proactively**
   - Run periodically (e.g., daily)
   - Check before critical operations
   - Alert on failures

---

## Limits and Constraints

| Resource | Limit | Configurable |
|----------|-------|--------------|
| Word count per entry | 200 words | `MAX_WORDS_PER_ENTRY` |
| Tags per entry | 10 tags | Validator |
| Agent name length | 100 chars | Validator |
| Response character limit | 25,000 chars | `CHARACTER_LIMIT` |
| Max entries before rotation | 1,000 entries | `MAX_ENTRIES` |
| File lock timeout | 10 seconds | `file_lock(timeout=...)` |
| Backup retention | 10 backups | `cleanup_old_backups(keep=...)` |
| Log file size | 10 MB | Logger config |
| Log file backups | 5 files | Logger config |

All limits marked "Configurable" can be changed by modifying constants in `shared_memory_mcp.py`.

---

## Storage Locations

| Item | Location |
|------|----------|
| Memory storage | `~/.shared_memory_mcp/memory.json` |
| Log file | `~/.shared_memory_mcp/mcp_memory.log` |
| Backups | `~/.shared_memory_mcp/backups/` |
| Temporary files | `~/.shared_memory_mcp/.memory.json.tmp` |

---

**Version:** 2.0.0
**Last Updated:** 2025-10-30
