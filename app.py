import os
import json
from typing import Annotated, Optional, Literal
from dotenv import load_dotenv
from pydantic import Field
import httpx
from mcp.server.fastmcp import FastMCP

load_dotenv()

FRED_DIR = "fred_data"

# Get port from environment variable (Render sets this, defaults to 8001 for local dev)
PORT = int(os.environ.get("PORT", 8001))

# Initialize FastMCP server with host and port in constructor
mcp = FastMCP("mcp-fredapi", host="0.0.0.0", port=PORT)

FRED_API_URL = "https://api.stlouisfed.org/fred"

async def make_request(url: str, params: dict):
    """Make a request to the Federal Reserve Economic Data API."""
    
    if FRED_API_KEY := os.getenv("FRED_API_KEY"):
        params["api_key"] = FRED_API_KEY
    else:
        raise ValueError("FRED_API_KEY environment variable is required")

    # Remove None values from params
    params = {k: v for k, v in params.items() if v is not None}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise ConnectionError(f"Failed to fetch data from the FRED API: {e}")
        except Exception as e:
            raise ConnectionError(f"Error processing FRED API request: {str(e)}")

def save_fred_data(series_id: str, data: dict) -> None:
    """Save FRED data to a file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(FRED_DIR, exist_ok=True)
        
        # Create filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{series_id}_{timestamp}.json"
        filepath = os.path.join(FRED_DIR, filename)
        
        # Add timestamp to data
        data['saved_at'] = datetime.now().isoformat()
        data['series_id'] = series_id
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"FRED data saved to: {filepath}")
        
    except Exception as e:
        print(f"Error saving FRED data: {str(e)}")

@mcp.tool()
def get_fred_series_observations(
    series_id: Annotated[str, Field(description="The id for a series.")],
    realtime_start: Annotated[Optional[str], Field(description="The start of the real-time period. Format: YYYY-MM-DD. Defaults to today's date.")] = None,
    realtime_end: Annotated[Optional[str], Field(description="The end of the real-time period. Format: YYYY-MM-DD. Defaults to today's date.")] = None,
    limit: Annotated[Optional[int | str], Field(description="Maximum number of observations to return. Defaults to 10.")] = 10,
    offset: Annotated[Optional[int | str], Field(description="Number of observations to offset from first. Defaults to 0.")] = 0,
    sort_order: Annotated[Literal['asc', 'desc'], Field(description="Sort order of observations. Options: 'asc' or 'desc'. Defaults to 'asc'.")] = 'asc',
    observation_start: Annotated[Optional[str], Field(description="Start date of observations. Format: YYYY-MM-DD.")] = None,
    observation_end: Annotated[Optional[str], Field(description="End date of observations. Format: YYYY-MM-DD.")] = None,
    units: Annotated[Literal['lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'], Field(description="Data value transformation. Options: 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'. Defaults to 'lin'.")] = 'lin',
    frequency: Annotated[Optional[Literal['d', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem']], Field(description="Frequency of observations. Options: 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'. Defaults to no value for no frequency aggregation.")] = None,
    aggregation_method: Annotated[Literal['avg', 'sum', 'eop'], Field(description="Aggregation method for frequency. Options: 'avg', 'sum', 'eop'. Defaults to 'avg'.")] = 'avg',
    output_type: Annotated[Literal[1, 2, 3, 4], Field(description="Output type of observations. Options: 1, 2, 3, 4. Defaults to 1.")] = 1,
    vintage_dates: Annotated[Optional[str], Field(description="Comma-separated list of vintage dates.")] = None,
) -> str:
    """
    Get series observations from the Federal Reserve Economic Data (FRED) API.

    Args:
        series_id: The id for a series (e.g., 'GDP', 'UNRATE', 'FEDFUNDS')
        realtime_start: The start of the real-time period. Format: YYYY-MM-DD
        realtime_end: The end of the real-time period. Format: YYYY-MM-DD
        limit: Maximum number of observations to return
        offset: Number of observations to offset from first
        sort_order: Sort order of observations ('asc' or 'desc')
        observation_start: Start date of observations. Format: YYYY-MM-DD
        observation_end: End date of observations. Format: YYYY-MM-DD
        units: Data value transformation
        frequency: Frequency of observations
        aggregation_method: Aggregation method for frequency
        output_type: Output type of observations
        vintage_dates: Comma-separated list of vintage dates

    Returns:
        JSON string with FRED series observations
    """
    try:
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
        
        # Use asyncio to run the async function
        import asyncio
        data = asyncio.run(make_request(f"{FRED_API_URL}/series/observations", params))

        if not data:
            return f"Error: Failed to fetch data from the FRED API"
        
        observations = data.get("observations", [])

        if not observations:
            return f"No observations found for series: {series_id}"
        
        # Create response data
        response_data = {
            'series_id': series_id,
            'count': len(observations),
            'observations': observations[:int(limit)] if limit else observations,
            'realtime_start': data.get('realtime_start'),
            'realtime_end': data.get('realtime_end'),
            'observation_start': data.get('observation_start'),
            'observation_end': data.get('observation_end'),
            'units': data.get('units'),
            'output_type': data.get('output_type'),
            'file_type': data.get('file_type'),
            'order_by': data.get('order_by'),
            'sort_order': data.get('sort_order'),
            'limit': data.get('limit'),
            'offset': data.get('offset')
        }
        
        # Save data
        save_fred_data(series_id, response_data)
        
        return json.dumps(response_data, indent=2)
        
    except Exception as e:
        return f"Error fetching FRED data: {str(e)}"

@mcp.tool()
def get_fred_series_history(series_id: str) -> list:
    """
    Get previously saved FRED data for a series.

    Args:
        series_id: The series ID to get history for

    Returns:
        List of saved FRED data filenames for the series
    """
    try:
        if not os.path.exists(FRED_DIR):
            return []
        
        history_files = []
        series_lower = series_id.lower()
        
        for filename in os.listdir(FRED_DIR):
            if series_lower in filename.lower() and filename.endswith('.json'):
                history_files.append(filename)
        
        return history_files
        
    except Exception as e:
        return [f"Error reading FRED history: {str(e)}"]

@mcp.resource("fred://series")
def get_saved_series() -> str:
    """
    List all FRED series with saved data.

    This resource provides a simple list of all series with data history.
    """
    try:
        if not os.path.exists(FRED_DIR):
            return "# No FRED Data\n\nNo FRED data has been saved yet."
        
        series = set()
        
        for filename in os.listdir(FRED_DIR):
            if filename.endswith('.json'):
                # Extract series ID from filename
                series_part = filename.split('_')[0]
                series.add(series_part.upper())
        
        content = "# Saved FRED Series\n\n"
        if series:
            for series_id in sorted(series):
                content += f"- {series_id}\n"
            content += f"\nTotal series: {len(series)}\n"
        else:
            content += "No series found.\n"
        
        return content
        
    except Exception as e:
        return f"# Error\n\nError reading FRED series: {str(e)}"

@mcp.resource("fred://{series_id}")
def get_series_data_history(series_id: str) -> str:
    """
    Get detailed data history for a specific FRED series.

    Args:
        series_id: The series ID to retrieve data history for
    """
    try:
        if not os.path.exists(FRED_DIR):
            return f"# No FRED Data for {series_id.upper()}\n\nNo FRED data found."
        
        series_lower = series_id.lower()
        data_files = []
        
        for filename in os.listdir(FRED_DIR):
            if filename.startswith(series_lower) and filename.endswith('.json'):
                filepath = os.path.join(FRED_DIR, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    data_files.append((filename, data))
                except:
                    continue
        
        if not data_files:
            return f"# No FRED Data for {series_id.upper()}\n\nNo data history found for this series."
        
        # Sort by filename (which includes timestamp)
        data_files.sort(key=lambda x: x[0], reverse=True)
        
        content = f"# FRED Data History for {series_id.upper()}\n\n"
        content += f"Total records: {len(data_files)}\n\n"
        
        for filename, data in data_files[:3]:  # Show last 3 records
            content += f"## {data.get('saved_at', 'Unknown time')}\n"
            content += f"**Series ID:** {data.get('series_id', 'N/A')}\n"
            content += f"**Observations:** {data.get('count', 'N/A')}\n"
            content += f"**Date Range:** {data.get('observation_start', 'N/A')} to {data.get('observation_end', 'N/A')}\n"
            content += f"**Units:** {data.get('units', 'N/A')}\n"
            
            # Show some recent observations
            observations = data.get('observations', [])
            if observations:
                content += f"**Recent Values:**\n"
                for obs in observations[-5:]:  # Last 5 observations
                    content += f"- {obs.get('date', 'N/A')}: {obs.get('value', 'N/A')}\n"
            
            content += "\n---\n\n"
        
        return content
        
    except Exception as e:
        return f"# Error\n\nError reading FRED data history for {series_id}: {str(e)}"

@mcp.prompt()
def generate_fred_prompt(series_id: str, limit: int = 10) -> str:
    """Generate a prompt for getting comprehensive FRED economic data for a series."""
    return f"""Get comprehensive economic data for FRED series '{series_id}' using the FRED tools.

    Follow these instructions:
    1. First, get current observations using get_fred_series_observations(series_id='{series_id}', limit={limit})
    2. Check if there's any historical data using get_fred_series_history(series_id='{series_id}')

    3. Provide a comprehensive economic data report that includes:
       - Current data values and trends
       - Date range and frequency of observations
       - Data transformation units and methodology
       - Recent historical patterns if available
       - Economic context and interpretation

    4. Format your response in a clear, readable format with sections for:
       - Current Data Summary
       - Key Observations
       - Historical Context
       - Economic Analysis & Insights

    Present the information in a way that's useful for economic analysis, research, or decision-making.
    
    Common FRED series examples:
    - GDP: Gross Domestic Product
    - UNRATE: Unemployment Rate
    - FEDFUNDS: Federal Funds Rate
    - CPIAUCSL: Consumer Price Index
    - PAYEMS: Total Nonfarm Payrolls"""

if __name__ == "__main__":
    # Initialize and run the server
    print(f"Starting FRED MCP server on 0.0.0.0:{PORT}")
    # Run with SSE transport (host and port already set in constructor)
    mcp.run(transport='sse')
