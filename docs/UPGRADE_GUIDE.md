# Upgrade Guide: v1.0 → v2.0

Quick guide to upgrading from MCP Agent Memory v1.0 to v2.0.

---

## TL;DR

✅ **Zero Breaking Changes** - Your existing code works without modification!
✅ **Automatic Migration** - Storage format upgrades automatically
✅ **New Features Optional** - Use new features when ready

**Upgrade is safe and reversible.**

---

## What's New in v2.0

### New Capabilities
- 🔒 **Concurrency Safety** - Safe for shared environments
- 📊 **Full CRUD Operations** - Update, delete, get single entries
- 🔍 **Advanced Search** - Full-text search across all fields
- 🏷️ **Tags & Priority** - Better organization
- 📈 **Statistics** - Analytics and insights
- 🛡️ **Health Check** - System monitoring
- 📝 **Structured Logging** - Better observability
- 💾 **Auto Backups** - Never lose data

### Enhanced Existing Tools
- **add_memory** - Now supports tags, priority, metadata
- **read_memory** - Advanced filtering and sorting
- **clear_memory** - Creates automatic backup

---

## Upgrade Steps

### Step 1: Backup (Optional but Recommended)

```bash
# Backup your current memory file
cp ~/.shared_memory_mcp/memory.json ~/.shared_memory_mcp/memory_v1_backup.json
```

### Step 2: Replace Server File

```bash
# Option A: Update in place
cp shared_memory_mcp.py shared_memory_mcp_old.py
# Download new version to shared_memory_mcp.py

# Option B: Keep both versions
# Use shared_memory_mcp.py (v2) and shared_memory_mcp_v1_backup.py (v1)
```

### Step 3: Add Utilities (New in v2)

Create the `utils` directory:
```bash
mkdir -p utils
# Add these files:
# - utils/__init__.py
# - utils/file_lock.py
# - utils/logger.py
```

### Step 4: Restart MCP Server

```bash
# Stop old server
# Start new server
python3 shared_memory_mcp.py
```

### Step 5: Verify (Optional)

```python
# Test health check
result = await health_check({})
print(result)
# Should show all systems operational
```

---

## Automatic Migration

When v2.0 first runs with v1 data:

1. **Detects v1 format** (simple JSON array)
   ```json
   [
     {"timestamp": "...", "agent_name": "...", ...}
   ]
   ```

2. **Loads entries** successfully

3. **On first write** converts to v2 format:
   ```json
   {
     "version": "2.0",
     "entries": [...],
     "created_at": "...",
     "updated_at": "..."
   }
   ```

4. **Adds new fields** to entries:
   - `entry_id`: Generated UUID
   - `tags`: Empty array
   - `priority`: "medium" (default)
   - `metadata`: Empty object
   - `updated_at`: null

**Your data is preserved!** The migration is automatic and safe.

---

## Code Changes Required

### ❌ No Changes Required!

Your existing code works as-is:

```python
# v1 code - still works in v2!
await add_memory(
    agent_name="my-agent",
    content="My message here"
)

result = await read_memory(
    response_format="markdown",
    limit=10
)

await clear_memory(confirm=True)
```

### ✨ Optional: Use New Features

When ready, enhance your code:

```python
# Add with new v2 features
await add_memory(
    agent_name="my-agent",
    content="My message here",
    tags=["important", "analysis"],      # NEW
    priority="high",                     # NEW
    metadata={"project": "project-x"}    # NEW
)

# Advanced filtering
result = await read_memory(
    response_format="markdown",
    tags=["analysis"],                   # NEW
    priority="high",                     # NEW
    sort_order="priority",               # NEW
    limit=10
)

# Search functionality
results = await search_memory(          # NEW TOOL
    query="important message",
    case_sensitive=False
)

# Update entries
await update_memory(                    # NEW TOOL
    entry_id="...",
    tags=["reviewed"],
    priority="low"
)

# Get statistics
stats = await get_memory_stats()        # NEW TOOL
```

---

## Configuration Changes

### Log Files (New)

v2 creates a log file:
```
~/.shared_memory_mcp/mcp_memory.log
```

**Action:** Optionally monitor this file for troubleshooting.

### Backups (New)

v2 creates automatic backups:
```
~/.shared_memory_mcp/backups/
  ├── memory_backup_20251030_120000.json
  ├── memory_backup_20251030_110000.json
  └── ... (keeps last 10)
```

**Action:** No action required. Backups are automatic.

### Storage Location (Unchanged)

Memory file location unchanged:
```
~/.shared_memory_mcp/memory.json
```

---

## Backward Compatibility

### v2 → v1 (Downgrade)

If you need to downgrade:

1. **Export your data:**
   ```python
   result = await read_memory(response_format="json")
   # Save result.entries to file
   ```

2. **Restore v1 server:**
   ```bash
   cp shared_memory_mcp_v1_backup.py shared_memory_mcp.py
   ```

3. **Convert format:**
   ```python
   # Extract entries array from v2 format
   with open('~/.shared_memory_mcp/memory.json') as f:
       v2_data = json.load(f)
       v1_data = v2_data['entries']  # Extract entries

   # Remove v2-specific fields
   for entry in v1_data:
       entry.pop('entry_id', None)
       entry.pop('tags', None)
       entry.pop('priority', None)
       entry.pop('metadata', None)
       entry.pop('updated_at', None)

   # Save as v1 format
   with open('~/.shared_memory_mcp/memory.json', 'w') as f:
       json.dump(v1_data, f, indent=2)
   ```

4. **Restart v1 server**

**Note:** You'll lose v2 features (entry_id, tags, priority, metadata) but core data preserved.

---

## Testing Your Upgrade

### Basic Test

```python
# 1. Add an entry
result = await add_memory(
    agent_name="test-agent",
    content="Test message for v2"
)
print(f"Added entry: {result.entry_id}")

# 2. Read entries
entries = await read_memory(response_format="json")
print(f"Total entries: {entries.total_entries}")

# 3. Check health
health = await health_check({})
print(f"Health status: {health.message}")
```

### Test New Features

```python
# Test search
results = await search_memory(query="test")
print(f"Search results: {len(results.entries)}")

# Test stats
stats = await get_memory_stats()
print(f"Memory stats: {stats.total_entries} entries")

# Test filtering
filtered = await read_memory(
    tags=["test"],
    priority="medium"
)
print(f"Filtered: {filtered.total_entries} entries")
```

---

## Troubleshooting

### Issue: "No module named 'utils'"

**Solution:** Make sure utils directory is in the correct location:
```bash
ls -la utils/
# Should show:
# __init__.py
# file_lock.py
# logger.py
```

### Issue: "JSON parse error"

**Solution:** v2 automatically recovers from backups. If needed:
```bash
# Restore from backup
cp ~/.shared_memory_mcp/backups/memory_backup_*.json \
   ~/.shared_memory_mcp/memory.json
```

### Issue: "File lock timeout"

**Cause:** Another process is holding the lock.

**Solution:**
1. Check for other MCP server instances
2. Wait 10 seconds for timeout
3. Increase timeout in code if needed: `file_lock(timeout=30.0)`

### Issue: Log file growing too large

**Solution:** v2 automatically rotates logs at 10MB. If needed:
```bash
# Manually clean old logs
rm ~/.shared_memory_mcp/mcp_memory.log.*
```

### Issue: Too many backups

**Solution:** v2 automatically keeps last 10. If needed:
```bash
# Manually clean old backups
cd ~/.shared_memory_mcp/backups
ls -t memory_backup_*.json | tail -n +11 | xargs rm
```

---

## Performance Considerations

### Storage Growth

v2 adds fields to each entry, increasing storage:
- v1: ~300-500 bytes per entry
- v2: ~500-1000 bytes per entry

**Impact:** Minimal for typical usage (< 1000 entries)

### Write Performance

v2 creates backups on every write:
- Adds ~5-10ms per write operation

**Impact:** Negligible for typical usage

### Read Performance

v2 uses same read mechanism:
- No performance change for reads

---

## Feature Comparison

| Feature | v1 | v2 |
|---------|----|----|
| Add entries | ✅ | ✅ Enhanced |
| Read entries | ✅ | ✅ Enhanced |
| Clear memory | ✅ | ✅ Enhanced |
| Update entries | ❌ | ✅ NEW |
| Delete entries | ❌ | ✅ NEW |
| Get single entry | ❌ | ✅ NEW |
| Search entries | ❌ | ✅ NEW |
| Get statistics | ❌ | ✅ NEW |
| Health check | ❌ | ✅ NEW |
| Tags | ❌ | ✅ NEW |
| Priority levels | ❌ | ✅ NEW |
| Metadata | ❌ | ✅ NEW |
| Entry IDs | ❌ | ✅ NEW |
| File locking | ❌ | ✅ NEW |
| Logging | ❌ | ✅ NEW |
| Auto backups | ❌ | ✅ NEW |
| Corruption recovery | ❌ | ✅ NEW |

---

## FAQ

### Q: Will my existing code break?
**A:** No! v2 is 100% backward compatible. All v1 code works unchanged.

### Q: Do I need to migrate my data manually?
**A:** No. Migration is automatic on first write.

### Q: Can I still use v1 after upgrading?
**A:** Yes. Keep `shared_memory_mcp_v1_backup.py` and switch back if needed.

### Q: What if I don't want the new features?
**A:** That's fine! v2 works exactly like v1 if you don't use new features.

### Q: Will logging/backups use a lot of disk space?
**A:** Minimal. Logs rotate at 10MB (5 backups = 50MB max). Backups depend on memory size (10 backups of your memory.json).

### Q: Can I disable logging?
**A:** Yes. Set log level to ERROR or remove logger calls from code.

### Q: Can I disable backups?
**A:** Not recommended, but you can comment out `create_backup()` calls.

### Q: How do I check which version I'm running?
**A:** Run `health_check()` or check `STORAGE_VERSION` constant in code (should be "2.0").

### Q: What's the minimum Python version?
**A:** Python 3.10+ (same as v1).

---

## Getting Help

### Documentation
- **API Reference:** See API_REFERENCE_V2.md
- **Changelog:** See CHANGELOG_V2.md
- **Implementation:** See IMPLEMENTATION_SUMMARY.md

### Testing
- Run basic tests: `python3 run_basic_tests.py`
- Check health: `await health_check({})`
- View logs: `tail -f ~/.shared_memory_mcp/mcp_memory.log`

### Support
- File issues on GitHub
- Check documentation
- Review examples in docs

---

## Summary

### ✅ Upgrade is Safe
- Zero breaking changes
- Automatic migration
- Data preserved
- Reversible

### ✅ Upgrade is Easy
1. Backup (optional)
2. Replace files
3. Add utils directory
4. Restart server
5. Done!

### ✅ Upgrade is Worth It
- Production-ready reliability
- 6 new tools
- Better organization (tags, priority)
- Search and analytics
- Logging and monitoring
- Auto backups and recovery

**Ready to upgrade? You're just 5 minutes away from v2!** 🚀

---

**Version:** 2.0.0
**Last Updated:** 2025-10-30
