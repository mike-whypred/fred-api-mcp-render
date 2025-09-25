#!/usr/bin/env python3
"""
Example MCP client to test the FRED API MCP server.
This demonstrates how to connect to and use the MCP server programmatically.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_mcp_client():
    """Test the MCP server by sending requests and parsing responses."""
    
    print("=" * 60)
    print("MCP Client Example - FRED API Server")
    print("=" * 60)
    
    # Test requests
    test_requests = [
        {
            "name": "GDP Data",
            "request": {
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
        },
        {
            "name": "Unemployment Rate",
            "request": {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_fred_series_observations",
                    "arguments": {
                        "series_id": "UNRATE",
                        "limit": 5,
                        "sort_order": "desc",
                        "frequency": "m"
                    }
                }
            }
        },
        {
            "name": "Consumer Price Index (Inflation)",
            "request": {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_fred_series_observations",
                    "arguments": {
                        "series_id": "CPIAUCSL",
                        "limit": 3,
                        "sort_order": "desc",
                        "units": "pch"
                    }
                }
            }
        }
    ]
    
    for test in test_requests:
        print(f"\nTesting: {test['name']}")
        print("-" * 40)
        
        try:
            # Start MCP server process
            process = subprocess.Popen(
                [sys.executable, "app.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path(__file__).parent
            )
            
            # Send request
            request_json = json.dumps(test['request']) + "\n"
            stdout, stderr = process.communicate(input=request_json, timeout=30)
            
            if stderr:
                print(f"Error: {stderr}")
                continue
                
            if stdout:
                try:
                    response = json.loads(stdout.strip())
                    
                    if "result" in response:
                        observations = response["result"]
                        print(f"✓ Retrieved {len(observations)} observations")
                        
                        # Show first few observations
                        for i, obs in enumerate(observations[:3]):
                            date = obs.get('date', 'N/A')
                            value = obs.get('value', 'N/A')
                            print(f"  {date}: {value}")
                            
                    elif "error" in response:
                        print(f"✗ MCP Error: {response['error']}")
                    else:
                        print(f"? Unexpected response: {response}")
                        
                except json.JSONDecodeError as e:
                    print(f"✗ JSON decode error: {e}")
                    print(f"Raw response: {stdout}")
            else:
                print("✗ No response from server")
                
        except subprocess.TimeoutExpired:
            print("✗ Request timed out")
            if process:
                process.kill()
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("MCP Client Example Complete")
    print("=" * 60)
    print("\nNOTE: Make sure you have FRED_API_KEY set in your environment")
    print("Get your free API key from: https://fred.stlouisfed.org/docs/api/api_key.html")

if __name__ == "__main__":
    asyncio.run(test_mcp_client())
