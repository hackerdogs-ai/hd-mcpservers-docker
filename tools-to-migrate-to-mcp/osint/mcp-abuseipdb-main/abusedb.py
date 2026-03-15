import os
import sys
import json
import asyncio
import logging
import httpx
from typing import Any, Optional
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("abuseipdb-server")

API_BASE_URL = "https://api.abuseipdb.com/api/v2"

class AbuseIPDBServer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.server = Server("abuseipdb-server")
        self.setup_handlers()
    
    async def make_request(
        self, 
        endpoint: str, 
        method: str = "GET", 
        params: Optional[dict] = None,
        json_data: Optional[dict] = None
    ) -> dict:
        """Make an HTTP request to the AbuseIPDB API."""
        url = f"{API_BASE_URL}{endpoint}"
        headers = {
            "Key": self.api_key,
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                logger.debug(f"Making {method} request to {endpoint}")
                
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method == "POST":
                    headers["Content-Type"] = "application/json"
                    response = await client.post(url, headers=headers, json=json_data)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                logger.debug(f"Request to {endpoint} successful")
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {endpoint}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {endpoint}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {str(e)}")
            raise
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            return [
                Tool(
                    name="check",
                    description="Check the abuse reports for an IP address. Returns abuse confidence score, usage type, ISP, and recent reports.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ipAddress": {
                                "type": "string",
                                "description": "The IP address to check (IPv4 or IPv6)"
                            },
                            "maxAgeInDays": {
                                "type": "integer",
                                "description": "Maximum age of reports to include (default: 30, max: 365)",
                                "default": 30
                            },
                            "verbose": {
                                "type": "boolean",
                                "description": "Include detailed report information",
                                "default": False
                            }
                        },
                        "required": ["ipAddress"]
                    }
                ),
                Tool(
                    name="report",
                    description="Report an abusive IP address with categories. Categories include: 3-DNS Compromise, 4-DNS Poisoning, 5-Fraud Orders, 6-DDoS Attack, 7-FTP Brute-Force, 9-Open Proxy, 10-Web Spam, 11-Email Spam, 14-Port Scan, 15-Hacking, 18-Brute-Force, 19-Bad Web Bot, 20-Exploited Host, 21-Web App Attack, 22-SSH, 23-IoT Targeted",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ip": {
                                "type": "string",
                                "description": "The IP address to report"
                            },
                            "categories": {
                                "type": "string",
                                "description": "Comma-separated category IDs (e.g., '14,18' for Port Scan and Brute-Force)"
                            },
                            "comment": {
                                "type": "string",
                                "description": "Optional comment about the abuse (max 1024 chars)"
                            }
                        },
                        "required": ["ip", "categories"]
                    }
                ),
                Tool(
                    name="check-block",
                    description="Check an entire CIDR block for reported IPs. Useful for checking IP ranges.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "network": {
                                "type": "string",
                                "description": "The CIDR notation network (e.g., '192.168.1.0/24')"
                            },
                            "maxAgeInDays": {
                                "type": "integer",
                                "description": "Maximum age of reports to include (default: 30)",
                                "default": 30
                            }
                        },
                        "required": ["network"]
                    }
                ),
                Tool(
                    name="blacklist",
                    description="Download the blacklist of reported IP addresses. Useful for firewall integration.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "confidenceMinimum": {
                                "type": "integer",
                                "description": "Minimum abuse confidence score (0-100, default: 90)",
                                "default": 90
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of IPs to return (default: 10000, max: 10000)",
                                "default": 10000
                            }
                        }
                    }
                ),
                Tool(
                    name="get-categories",
                    description="Retrieve the list of abuse report categories with their IDs and descriptions.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="bulk-report",
                    description="Report multiple IPs at once in CSV format. Each line should contain: IP,categories,comment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "csv": {
                                "type": "string",
                                "description": "CSV data with format: IP,categories,comment (one per line)"
                            }
                        },
                        "required": ["csv"]
                    }
                ),
                Tool(
                    name="clear-address",
                    description="Clear your own IP address from reports if it was a false positive.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ipAddress": {
                                "type": "string",
                                "description": "The IP address to clear"
                            }
                        },
                        "required": ["ipAddress"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            try:
                logger.info(f"Handling tool call: {name}")
                
                if name == "check":
                    result = await self.handle_check(arguments)
                elif name == "report":
                    result = await self.handle_report(arguments)
                elif name == "check-block":
                    result = await self.handle_check_block(arguments)
                elif name == "blacklist":
                    result = await self.handle_blacklist(arguments)
                elif name == "get-categories":
                    result = await self.handle_get_categories(arguments)
                elif name == "bulk-report":
                    result = await self.handle_bulk_report(arguments)
                elif name == "clear-address":
                    result = await self.handle_clear_address(arguments)
                else:
                    logger.warning(f"Unknown tool requested: {name}")
                    raise ValueError(f"Unknown tool: {name}")
                
                logger.info(f"Tool {name} completed successfully")
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except Exception as e:
                logger.error(f"Error handling tool {name}: {str(e)}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    async def handle_check(self, args: dict) -> dict:
        params = {
            "ipAddress": args["ipAddress"],
            "maxAgeInDays": args.get("maxAgeInDays", 30),
            "verbose": args.get("verbose", False)
        }
        return await self.make_request("/check", "GET", params=params)
    
    async def handle_report(self, args: dict) -> dict:
        data = {
            "ip": args["ip"],
            "categories": args["categories"],
            "comment": args.get("comment", "")
        }
        return await self.make_request("/report", "POST", json_data=data)
    
    async def handle_check_block(self, args: dict) -> dict:
        params = {
            "network": args["network"],
            "maxAgeInDays": args.get("maxAgeInDays", 30)
        }
        return await self.make_request("/check-block", "GET", params=params)
    
    async def handle_blacklist(self, args: dict) -> dict:
        params = {
            "confidenceMinimum": args.get("confidenceMinimum", 90),
            "limit": args.get("limit", 10000)
        }
        return await self.make_request("/blacklist", "GET", params=params)
    
    async def handle_get_categories(self, args: dict) -> dict:
        # AbuseIPDB categories are fixed
        return {
            "data": [
                {"id": 3, "name": "DNS Compromise"},
                {"id": 4, "name": "DNS Poisoning"},
                {"id": 5, "name": "Fraud Orders"},
                {"id": 6, "name": "DDoS Attack"},
                {"id": 7, "name": "FTP Brute-Force"},
                {"id": 9, "name": "Open Proxy"},
                {"id": 10, "name": "Web Spam"},
                {"id": 11, "name": "Email Spam"},
                {"id": 14, "name": "Port Scan"},
                {"id": 15, "name": "Hacking"},
                {"id": 18, "name": "Brute-Force"},
                {"id": 19, "name": "Bad Web Bot"},
                {"id": 20, "name": "Exploited Host"},
                {"id": 21, "name": "Web App Attack"},
                {"id": 22, "name": "SSH"},
                {"id": 23, "name": "IoT Targeted"}
            ]
        }
    
    async def handle_bulk_report(self, args: dict) -> dict:
        data = {"csv": args["csv"]}
        return await self.make_request("/bulk-report", "POST", json_data=data)
    
    async def handle_clear_address(self, args: dict) -> dict:
        params = {"ipAddress": args["ipAddress"]}
        return await self.make_request("/clear-address", "DELETE", params=params)
    
    async def run(self):
        logger.info("Starting AbuseIPDB MCP Server")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="abuseipdb-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )

async def main():
    api_key = os.getenv("ABUSEIPDB_API_KEY")
    if not api_key:
        logger.error("ABUSEIPDB_API_KEY environment variable is required")
        sys.exit(1)
    
    logger.info("API key found, initializing server")
    server = AbuseIPDBServer(api_key)
    
    try:
        await server.run()
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())