import asyncio
import sys
import os
from mcp.server.stdio import stdio_server
from mcp.server.fastmcp import FastMCP
from typing import Annotated, Optional, Literal
from dotenv import load_dotenv
from pydantic import Field
import httpx

load_dotenv()

# Create MCP server
mcp = FastMCP("mcp-fredapi", dependencies=["httpx", "python-dotenv"])

FRED_API_URL = "https://api.stlouisfed.org/fred"

async def make_request(url: str, params: dict):
    """Make a request to the Federal Reserve Economic Data API."""
    
    if FRED_API_KEY := os.getenv("FRED_API_KEY"):
        params["api_key"] = FRED_API_KEY

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"Failed to fetch data from the FRED API: {e}")

@mcp.tool(name="get_fred_series_observations", description="""Get series observations from the Fred API.""")
async def get_fred_series_observations(
    series_id: Annotated[str, Field(description="The id for a series.")],
    realtime_start: Annotated[Optional[str], Field(description="The start of the real-time period. Format: YYYY-MM-DD. Defaults to today's date.")] = None,
    realtime_end: Annotated[Optional[str], Field(description="The end of the real-time period. Format: YYYY-MM-DD. Defaults to today's date.")] = None,
    limit: Annotated[Optional[int | str], Field(description="Maximum number of observations to return. Defaults to 10.")] = 10,
    offset: Annotated[Optional[int | str], Field(description="Number of observations to offset from first. Defaults to 0.")] = 0,
    sort_order: Annotated[Literal['asc', 'desc'], Field(description="Sort order of observations. Options: 'asc' or 'desc'. Defaults to 'asc'.")] = 'asc',
    observation_start: Annotated[Optional[str], Field(description="Start date of observations. Format: YYYY-MM-DD.")] = None,
    observation_end: Annotated[Optional[str], Field(description="End date of observations. Format: YYYY-MM-DD.")] = None,
    units: Annotated[Literal['lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'], Field(description="Data value transformation. Options: 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'. Defaults to 'lin'.")] = 'lin',
    frequency: Annotated[Literal['d', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'], Field(description="Frequency of observations. Options: 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'. Defaults to no value for no frequency aggregation.")] = None,
    aggregation_method: Annotated[Literal['avg', 'sum', 'eop'], Field(description="Aggregation method for frequency. Options: 'avg', 'sum', 'eop'. Defaults to 'avg'.")] = 'avg',
    output_type: Annotated[Literal[1, 2, 3, 4], Field(description="Output type of observations. Options: 1, 2, 3, 4. Defaults to 1.")] = 1,
    vintage_dates: Annotated[Optional[str], Field(description="Comma-separated list of vintage dates.")] = None,
):
    """Get series observations from the Fred API.
    
    Args:
        series_id (str): The id for a series.
        realtime_start (str): The start of the real-time period. YYYY-MM-DD formatted string, optional, default: today's date.
        realtime_end (str): The end of the real-time period. YYYY-MM-DD formatted string, optional, default: today's date.
        limit (int or str): The maximum number of observations to return. Optional, default: 1000.
        offset (int or str): The number of observations to offset from the first observation. Optional, default: 0.
        sort_order (str): The sort order of the observations. Possible values: "asc" or "desc". Optional, default: "asc".
        observation_start (str): The start date of the observations to get. YYYY-MM-DD formatted string. Optional, default: 1776-07-04 (earliest available).
        observation_end (str): The end date of the observations to get. YYYY-MM-DD formatted string. Optional, default: 9999-12-31 (latest available).
        units (str): A key that indicates a data value transformation. Posible values: 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'. Optional, default: 'lin' (No transformation).
        frequency (str): The frequency of the observations. Posible values: 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'. Optional, default: no value for no frequency aggregation.
        aggregation_method (str): A key that indicates the aggregation method used for frequency aggregation. This parameter has no affect if the frequency parameter is not set. Posible values: 'avg', 'sum', 'eop'. Optional, default: "avg".
        output_type (int): The output type of the observations. Optional, default: 1.
        vintage_dates (str): A comma-separated list of vintage dates to return. Optional, default: no vintage dates are set by default.

    Returns:
        dict[str, str]: A dictionary containing the observations or data values for an economic data series.
    """
    params = {
        "series_id": series_id,
        "realtime_start": realtime_start,
        "realtime_end": realtime_end,
        "limit": limit,
        "offset": offset,
        "sort_order": sort_order,
        "observation_start": observation_start,
        "observation_end": observation_end,
        "units": units,
        "frequency": frequency,
        "aggregation_method": aggregation_method,
        "output_type": output_type,
        "vintage_dates": vintage_dates,
        "file_type": "json"
    }
    
    data = await make_request(f"{FRED_API_URL}/series/observations", params)

    if not data:
        raise ConnectionError("Failed to fetch data from the FRED API")
    
    observations = data["observations"]

    if not observations:
        raise ValueError("No observations found for the given series")
    
    return observations

def run_mcp_server():
    """Run the MCP server using stdio transport."""
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await mcp.run(read_stream, write_stream)
    
    asyncio.run(main())

if __name__ == "__main__":
    # Check if running on Render or similar cloud platform
    if os.getenv("PORT") or os.getenv("RENDER"):
        # For cloud deployment, we need to keep the process alive
        # This is a simple HTTP server to satisfy Render's health checks
        import http.server
        import socketserver
        import threading
        
        class HealthHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "healthy", "service": "mcp-fredapi"}')
                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"message": "MCP FRED API Server", "status": "running", "usage": "Connect via MCP protocol"}')
        
        port = int(os.getenv("PORT", 8000))
        
        # Start HTTP server in background for health checks
        with socketserver.TCPServer(("", port), HealthHandler) as httpd:
            print(f"MCP FRED API Server running on port {port}")
            print("HTTP health check available at /health")
            print("MCP server ready for stdio connections")
            
            # Keep the server running
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("Server stopped")
    else:
        # Local development - run as MCP server
        run_mcp_server()
