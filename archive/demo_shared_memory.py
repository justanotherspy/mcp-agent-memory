#!/usr/bin/env python3
"""
Demo script for Shared Memory MCP Server
=========================================

This script simulates a conversation between two agents using the shared
memory MCP server. It demonstrates the add_memory and read_memory tools.

This is for testing purposes only - it directly calls the tool functions
rather than going through the MCP protocol.
"""

import asyncio
import json
from shared_memory_mcp import (
    add_memory, read_memory, clear_memory,
    AddMemoryInput, ReadMemoryInput, ClearMemoryInput,
    ResponseFormat
)


async def simulate_agent_conversation():
    """Simulate a conversation between two Claude Code instances."""
    
    print("=" * 70)
    print("Shared Memory MCP Server - Demo Simulation")
    print("=" * 70)
    print()
    
    # Clear any existing memory to start fresh
    print("🧹 Clearing existing memory...")
    clear_result = await clear_memory(ClearMemoryInput(confirm=True))
    print(json.loads(clear_result)["message"])
    print()
    
    # Simulate Claude Alpha starting work
    print("🤖 Claude Alpha: Starting to analyze sales data...")
    result = await add_memory(AddMemoryInput(
        agent_name="claude-alpha",
        content=(
            "Starting analysis of Q4 2024 sales data. I'll focus on regional "
            "trends first, then look at product categories. Initial observation: "
            "West Coast sales are up 15% compared to Q3."
        )
    ))
    response = json.loads(result)
    print(f"   ✓ Added entry #{response['entry_number']} ({response['word_count']} words)")
    print()
    
    await asyncio.sleep(1)  # Simulate time passing
    
    # Simulate Claude Beta checking what Alpha is doing
    print("🤖 Claude Beta: Let me check what Alpha is working on...")
    result = await read_memory(ReadMemoryInput(response_format=ResponseFormat.MARKDOWN))
    print(result)
    print()
    
    # Simulate Claude Beta responding
    print("🤖 Claude Beta: I'll help with visualizations!")
    result = await add_memory(AddMemoryInput(
        agent_name="claude-beta",
        content=(
            "Noticed Alpha is analyzing Q4 sales. I can help create visualizations "
            "once the analysis is complete. I'm particularly good at regional heatmaps "
            "and trend charts. Let me know when you're ready!"
        )
    ))
    response = json.loads(result)
    print(f"   ✓ Added entry #{response['entry_number']} ({response['word_count']} words)")
    print()
    
    await asyncio.sleep(1)
    
    # Simulate Alpha continuing work
    print("🤖 Claude Alpha: Continuing analysis, found interesting patterns...")
    result = await add_memory(AddMemoryInput(
        agent_name="claude-alpha",
        content=(
            "Deep dive into West Coast data complete. Found that most growth is in "
            "tech sector sales, specifically cloud services and AI tools. This aligns "
            "with industry trends. Ready for Beta to create visualizations showing: "
            "(1) Regional comparison (2) Product category breakdown (3) Month-over-month trends."
        )
    ))
    response = json.loads(result)
    print(f"   ✓ Added entry #{response['entry_number']} ({response['word_count']} words)")
    print()
    
    await asyncio.sleep(1)
    
    # Simulate Beta reading updates
    print("🤖 Claude Beta: Checking for updates from Alpha...")
    result = await read_memory(ReadMemoryInput(
        response_format=ResponseFormat.MARKDOWN,
        agent_filter="claude-alpha"
    ))
    print("   [Filtered to show only Alpha's messages]")
    print(result)
    print()
    
    # Simulate Beta responding with next steps
    print("🤖 Claude Beta: Creating visualization plan...")
    result = await add_memory(AddMemoryInput(
        agent_name="claude-beta",
        content=(
            "Perfect! I'll create three visualizations as requested: "
            "(1) Interactive regional heatmap showing West Coast growth "
            "(2) Stacked bar chart for product categories "
            "(3) Line graph for monthly trends with Q3 comparison. "
            "Starting with the regional heatmap now. Will use D3.js for interactivity."
        )
    ))
    response = json.loads(result)
    print(f"   ✓ Added entry #{response['entry_number']} ({response['word_count']} words)")
    print()
    
    # Show full conversation in JSON format
    print("\n" + "=" * 70)
    print("Full Conversation (JSON Format)")
    print("=" * 70)
    result = await read_memory(ReadMemoryInput(response_format=ResponseFormat.JSON))
    print(result)
    print()
    
    # Test filtering by agent
    print("\n" + "=" * 70)
    print("Testing Agent Filter: Beta's Messages Only")
    print("=" * 70)
    result = await read_memory(ReadMemoryInput(
        response_format=ResponseFormat.MARKDOWN,
        agent_filter="claude-beta"
    ))
    print(result)
    print()
    
    # Test limit parameter
    print("\n" + "=" * 70)
    print("Testing Limit: Last 2 Messages Only")
    print("=" * 70)
    result = await read_memory(ReadMemoryInput(
        response_format=ResponseFormat.MARKDOWN,
        limit=2
    ))
    print(result)
    print()
    
    print("=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    print()
    print("The shared memory MCP server is working correctly!")
    print("You can now use it with Claude Code instances.")


async def test_word_limit():
    """Test the word count validation."""
    print("\n" + "=" * 70)
    print("Testing Word Limit Validation")
    print("=" * 70)
    print()
    
    # Create a message with too many words
    long_content = " ".join(["word"] * 201)
    
    print(f"Attempting to add entry with 201 words (limit is 200)...")
    try:
        result = await add_memory(AddMemoryInput(
            agent_name="test-agent",
            content=long_content
        ))
        print("❌ Should have failed but didn't!")
    except Exception as e:
        print(f"✓ Correctly rejected: {str(e)}")
    print()


async def main():
    """Run all demos."""
    await simulate_agent_conversation()
    await test_word_limit()
    
    print("\n💡 Next Steps:")
    print("1. Install MCP SDK: pip install mcp")
    print("2. Add to Claude Code config (see SHARED_MEMORY_README.md)")
    print("3. Start having multi-agent conversations!")


if __name__ == "__main__":
    asyncio.run(main())
