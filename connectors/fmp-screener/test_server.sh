#!/bin/bash

# Test script for FMP Screener MCP Server
# Run this in a new terminal while server.py is running

echo "Testing FMP Screener MCP Server..."

# Test 1: Initialize the server
echo "1. Testing initialization..."
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0"}}}' | python server.py

echo -e "\n\n2. Testing tools list..."
# Test 2: List available tools
(
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0"}}}'
echo '{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}'
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}'
) | python server.py

echo -e "\n\n3. Testing stock screening (Technology sector)..."
# Test 3: Call the screen_for_stocks tool
(
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0"}}}'
echo '{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}'
echo '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "screen_for_stocks", "arguments": {"sector": "Technology", "limit": 5}}}'
) | python server.py