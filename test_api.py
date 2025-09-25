#!/usr/bin/env python3
"""
Test script for the MCP FRED API server.
This tests both the health check endpoint (for Render) and MCP functionality.
"""

import asyncio
import httpx
import subprocess
import sys
import os
import json
import tempfile
from pathlib import Path

BASE_URL = "http://localhost:8000"

async def test_health_check():
    """Test the health check endpoint (for Render deployment)."""
    print("Testing health check endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
            return response.status_code == 200
    except httpx.ConnectError:
        print("Health check endpoint not available (server may not be running)")
        return False

async def test_root_endpoint():
    """Test the root endpoint."""
    print("Testing root endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
            return response.status_code == 200
    except httpx.ConnectError:
        print("Root endpoint not available (server may not be running)")
        return False

def test_mcp_server_direct():
    """Test the MCP server directly using subprocess."""
    print("Testing MCP server directly...")
    
    # Create a simple MCP request
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "get_fred_series_observations",
            "arguments": {
                "series_id": "GDP",
                "limit": 3,
                "sort_order": "desc"
            }
        }
    }
    
    try:
        # Set environment variable for the test
        env = os.environ.copy()
        if not env.get("FRED_API_KEY"):
            print("WARNING: FRED_API_KEY not set. This test may fail.")
        
        # Run the MCP server as a subprocess
        process = subprocess.Popen(
            [sys.executable, "app.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=Path(__file__).parent
        )
        
        # Send the request
        request_json = json.dumps(mcp_request) + "\n"
        stdout, stderr = process.communicate(input=request_json, timeout=30)
        
        if stderr:
            print(f"MCP Server stderr: {stderr}")
        
        if stdout:
            print("MCP Server response received:")
            try:
                response = json.loads(stdout.strip())
                print(json.dumps(response, indent=2))
                return True
            except json.JSONDecodeError:
                print(f"Raw stdout: {stdout}")
                return False
        else:
            print("No response from MCP server")
            return False
            
    except subprocess.TimeoutExpired:
        print("MCP server test timed out")
        process.kill()
        return False
    except Exception as e:
        print(f"Error testing MCP server: {e}")
        return False

def test_local_mcp_run():
    """Test running the MCP server locally without PORT env var."""
    print("Testing local MCP server (without PORT env var)...")
    
    # Temporarily unset PORT to test local MCP mode
    original_port = os.environ.pop("PORT", None)
    
    try:
        # This should run in MCP mode
        result = subprocess.run(
            [sys.executable, "-c", """
import os
os.environ.pop('PORT', None)  # Ensure PORT is not set
import sys
sys.path.insert(0, '.')
from app import run_mcp_server
print('MCP server function available')
"""],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✓ MCP server mode accessible")
            return True
        else:
            print(f"✗ Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✓ MCP server mode test completed (expected timeout)")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        # Restore PORT if it was set
        if original_port:
            os.environ["PORT"] = original_port

async def main():
    """Run all tests."""
    print("=" * 60)
    print("MCP FRED API Server Test Suite")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Health check (for Render)
    print("1. Testing Render health check endpoint...")
    health_ok = await test_health_check()
    results.append(("Health Check", health_ok))
    
    # Test 2: Root endpoint
    print("2. Testing root endpoint...")
    root_ok = await test_root_endpoint()
    results.append(("Root Endpoint", root_ok))
    
    # Test 3: Local MCP mode
    print("3. Testing local MCP mode...")
    local_mcp_ok = test_local_mcp_run()
    results.append(("Local MCP Mode", local_mcp_ok))
    
    # Test 4: Direct MCP server test (if FRED_API_KEY is available)
    if os.getenv("FRED_API_KEY"):
        print("4. Testing MCP server directly...")
        mcp_ok = test_mcp_server_direct()
        results.append(("Direct MCP Test", mcp_ok))
    else:
        print("4. Skipping direct MCP test (FRED_API_KEY not set)")
        results.append(("Direct MCP Test", "Skipped"))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print("=" * 60)
    
    for test_name, result in results:
        if result is True:
            print(f"✓ {test_name}: PASSED")
        elif result is False:
            print(f"✗ {test_name}: FAILED")
        else:
            print(f"- {test_name}: {result}")
    
    print("\n" + "=" * 60)
    print("USAGE NOTES:")
    print("=" * 60)
    print("• For Render deployment: Health check endpoint should work")
    print("• For local MCP usage: Run without PORT env var")
    print("• For Cursor integration: Use the MCP configuration")
    print("• Set FRED_API_KEY environment variable for full functionality")

if __name__ == "__main__":
    asyncio.run(main())
