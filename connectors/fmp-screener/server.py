#!/usr/bin/env python3
"""
FMP Screener MCP Server
A Claude MCP connector for screening stocks using the Financial Modeling Prep API.
"""

import os
import sys
from typing import Optional

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Helper for Claude Desktop logs
def log(msg: str):
    print(f"[FMPScreener] {msg}", file=sys.stderr)

# Get API key from environment
FMP_API_KEY = os.getenv("FMP_API_KEY")
if not FMP_API_KEY:
    log("FMP_API_KEY not found in environment variables. Please check your .env file.")
    sys.exit(1)

# Create the MCP server
mcp = FastMCP("fmp-screener")

@mcp.tool(
    name="screen_for_stocks",
    description="""Screens for stocks using the Financial Modeling Prep API based on a wide range of criteria. Returns a list of matching companies. Translate natural language queries into the appropriate parameters. For example, "large cap" means marketCapMoreThan=10000000000. "Profitable" can be ignored as there is no direct filter."""
)
async def screen_for_stocks(
    marketCapMoreThan: Optional[int] = None,
    marketCapLowerThan: Optional[int] = None,
    priceMoreThan: Optional[float] = None,
    priceLowerThan: Optional[float] = None,
    betaMoreThan: Optional[float] = None,
    betaLowerThan: Optional[float] = None,
    volumeMoreThan: Optional[int] = None,
    volumeLowerThan: Optional[int] = None,
    dividendMoreThan: Optional[float] = None,
    dividendLowerThan: Optional[float] = None,
    dividendYieldMoreThan: Optional[float] = None,
    dividendYieldLowerThan: Optional[float] = None,
    isActivelyTrading: Optional[bool] = None,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    country: Optional[str] = None,
    exchange: Optional[str] = None,
    limit: int = 20
) -> dict:
    """Screen for stocks using the Financial Modeling Prep API."""
    
    try:
        # Build parameters dictionary, only including non-None values
        params = {"apikey": FMP_API_KEY}
        
        if marketCapMoreThan is not None:
            params["marketCapMoreThan"] = marketCapMoreThan
        if marketCapLowerThan is not None:
            params["marketCapLowerThan"] = marketCapLowerThan
        if priceMoreThan is not None:
            params["priceMoreThan"] = priceMoreThan
        if priceLowerThan is not None:
            params["priceLowerThan"] = priceLowerThan
        if betaMoreThan is not None:
            params["betaMoreThan"] = betaMoreThan
        if betaLowerThan is not None:
            params["betaLowerThan"] = betaLowerThan
        if volumeMoreThan is not None:
            params["volumeMoreThan"] = volumeMoreThan
        if volumeLowerThan is not None:
            params["volumeLowerThan"] = volumeLowerThan
        if dividendMoreThan is not None:
            params["dividendMoreThan"] = dividendMoreThan
        if dividendLowerThan is not None:
            params["dividendLowerThan"] = dividendLowerThan
        if dividendYieldMoreThan is not None:
            params["dividendYieldMoreThan"] = dividendYieldMoreThan
        if dividendYieldLowerThan is not None:
            params["dividendYieldLowerThan"] = dividendYieldLowerThan
        if isActivelyTrading is not None:
            params["isActivelyTrading"] = str(isActivelyTrading).lower()
        if sector is not None:
            params["sector"] = sector
        if industry is not None:
            params["industry"] = industry
        if country is not None:
            params["country"] = country
        if exchange is not None:
            params["exchange"] = exchange
        
        # Ensure limit is within bounds
        if limit > 100:
            limit = 100
        elif limit < 1:
            limit = 1
        params["limit"] = limit
        
        # Make the API request
        url = "https://financialmodelingprep.com/api/v3/stock-screener"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        # Return the JSON response
        data = response.json()
        
        return {
            "success": True,
            "count": len(data),
            "stocks": data
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error making request to FMP API: {str(e)}"
        log(error_msg)
        return {
            "success": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log(error_msg)
        return {
            "success": False,
            "error": error_msg
        }

if __name__ == "__main__":
    try:
        mcp.run()  # defaults to stdio transport for Claude Desktop
    except KeyboardInterrupt:
        log("Server shutting down.")