# MCP-FREDAPI-RENDER

**FRED (Federal Reserve Economic Data) API MCP Server for Render Deployment**

## Table of Contents

- [Introduction](#introduction)
- [How It Works](#how-it-works)
- [Render Deployment](#render-deployment)
- [Environment Variables](#environment-variables)
- [Local MCP Usage](#local-mcp-usage)
- [Cursor Integration](#cursor-integration)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Introduction

This is an MCP (Model Context Protocol) server for accessing FRED (Federal Reserve Economic Data), designed to be deployable on Render while maintaining full MCP functionality. It provides economic data from the Federal Reserve Bank of St. Louis through the MCP protocol.

The server integrates with the [official FRED API](https://fred.stlouisfed.org/docs/api/fred/), focusing specifically on the [series_observations endpoint](https://fred.stlouisfed.org/docs/api/fred/series_observations.html) which provides time series data for economic indicators.

## How It Works

This server is designed to work in two modes:

1. **Local MCP Mode**: When run locally without a `PORT` environment variable, it runs as a standard MCP server using stdio transport (perfect for Cursor integration)

2. **Render Deployment Mode**: When deployed on Render (with `PORT` env var), it runs a simple HTTP health check server to keep the service alive, while still being an MCP server at its core

The clever part is that it remains a true MCP server in both modes - the HTTP server is just for Render's health checks.

## Render Deployment

### Quick Deploy

1. Fork this repository
2. Connect your GitHub account to Render
3. Create a new Web Service on Render
4. Connect your forked repository
5. Set the environment variable `FRED_API_KEY` with your API key
6. Deploy!

### Manual Configuration

If you prefer manual setup:

1. **Build Command**: `pip install -r requirements.txt`
2. **Start Command**: `python app.py`
3. **Environment Variables**:
   - `FRED_API_KEY`: Your FRED API key (required)
   - `PORT`: Port number (automatically set by Render)

### Using render.yaml

This repository includes a `render.yaml` file for Infrastructure as Code deployment:

```yaml
services:
  - type: web
    name: mcp-fredapi
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.18
      - key: PORT
        value: 10000
      - key: FRED_API_KEY
        sync: false
```

## Environment Variables

### Required

- `FRED_API_KEY`: Your FRED API key. Get one from [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html).

### Optional

- `PORT`: Port number for health check server (automatically set by Render)
- `RENDER`: Set by Render automatically to indicate cloud deployment

## Local MCP Usage

When running locally (without `PORT` env var), the server runs in pure MCP mode:

```bash
# Local MCP server mode
python app.py
```

This starts the MCP server using stdio transport, perfect for integration with Cursor or other MCP clients.

## Cursor Integration

To use this MCP server with Cursor, add this to your `~/.cursor/mcp.json`:

### If Running Locally

```json
{
  "mcpServers": {
    "mcp-fredapi": {
      "command": "python",
      "args": ["/path/to/mcp-fredapi-render/app.py"]
    }
  }
}
```

### If Using Deployed Version

For now, MCP works best with local servers. The deployed version is mainly for hosting/health checks. However, you could potentially create a proxy that connects to your deployed server.

## Health Check Endpoints

When deployed on Render, these endpoints are available for monitoring:

- **GET** `/` - Root endpoint with service information  
- **GET** `/health` - Health check endpoint

## Testing

### Health Check Testing

Test the deployed service health endpoints:

```bash
# Test health check
curl https://your-render-app.onrender.com/health

# Test root endpoint  
curl https://your-render-app.onrender.com/
```

### Local MCP Testing

Run the test suite to verify MCP functionality:

```bash
# Run comprehensive test suite
python test_api.py
```

This will test:
- Health check endpoints (for Render)
- Local MCP mode functionality
- Direct MCP server communication (if FRED_API_KEY is set)

## MCP Usage Examples

When using this server with Cursor or other MCP clients, you can call the `get_fred_series_observations` tool:

### Getting GDP Data

```
Can you get the latest GDP data from FRED?
```

The MCP client will automatically call:
```json
{
  "tool": "get_fred_series_observations",
  "arguments": {
    "series_id": "GDP"
  }
}
```

### Getting GDP Data with Parameters

```
Can you get the last 5 GDP observations in descending order?
```

The MCP client will call:
```json
{
  "tool": "get_fred_series_observations", 
  "arguments": {
    "series_id": "GDP",
    "limit": 5,
    "sort_order": "desc"
  }
}
```

### Getting Inflation Data

```
What's the recent monthly inflation rate?
```

The MCP client will call:
```json
{
  "tool": "get_fred_series_observations",
  "arguments": {
    "series_id": "CPIAUCSL",
    "units": "pch",
    "frequency": "m",
    "sort_order": "desc",
    "limit": 12
  }
}
```

### Response Format

The MCP tool returns an array of observations:

```json
[
  {
    "realtime_start": "2024-01-01",
    "realtime_end": "2024-01-01", 
    "date": "2023-10-01",
    "value": "27000.000"
  }
]
```

## Local Development

### Prerequisites

- Python 3.9 or higher
- FRED API key

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd mcp-fredapi-render
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```env
FRED_API_KEY=your_api_key_here
```

5. Run the development server:
```bash
python app.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Parameters

The API supports all FRED API parameters:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| series_id | str | The ID of the economic series | Required |
| realtime_start | str | Start of real-time period (YYYY-MM-DD) | None |
| realtime_end | str | End of real-time period (YYYY-MM-DD) | None |
| limit | int | Maximum number of observations | 10 |
| offset | int | Number of observations to skip | 0 |
| sort_order | str | Sort order ('asc' or 'desc') | 'asc' |
| observation_start | str | Start date of observations (YYYY-MM-DD) | None |
| observation_end | str | End date of observations (YYYY-MM-DD) | None |
| units | str | Data transformation | 'lin' |
| frequency | str | Frequency aggregation | None |
| aggregation_method | str | Aggregation method | 'avg' |
| output_type | int | Output format (1-4) | 1 |
| vintage_dates | str | Comma-separated vintage dates | None |

## Common Economic Series IDs

- `GDP` - Gross Domestic Product
- `UNRATE` - Unemployment Rate
- `CPIAUCSL` - Consumer Price Index
- `FEDFUNDS` - Federal Funds Rate
- `DGS10` - 10-Year Treasury Constant Maturity Rate
- `DEXUSEU` - US/Euro Foreign Exchange Rate

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

- [FRED API Documentation](https://fred.stlouisfed.org/docs/api/fred/series_observations.html)
- [Render Documentation](https://render.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)