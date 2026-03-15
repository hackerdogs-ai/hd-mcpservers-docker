import logging
import abusech_intel
from fastmcp import FastMCP, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('abusech-mcp')

mcp = FastMCP(name='abusech-mcp')

# --- ABUSECH MCP TOOLS ---

@mcp.tool()
async def get_ip_report(
    ip: str
) -> dict:
    """
        Name: Get IP Report
        Description: Get a comprehensive IP report from URLhaus, and ThreatFox
        Parameters:
            - ip: The IP address to retrieve the report for
    """

    # abusech_intel._get_ip_report is async
    return await abusech_intel._get_ip_report(ip)

@mcp.tool()
async def get_domain_report(
    domain: str
) -> dict:
    """
        Name: Get Domain Report
        Description: Get a comprehensive domain report from URLhaus and ThreatFox
        Parameters:
            - domain: The domain to retrieve the report for
    """

    # abusech_intel._get_domain_report is async
    return await abusech_intel._get_domain_report(domain)

@mcp.tool()
async def get_url_report(
    url: str
) -> dict:
    """
        Name: Get URL Report
        Description: Get a comprehensive URL report from URLhaus and ThreatFox
        Parameters:
            - url: The URL to retrieve the report for
    """

    # abusech_intel._get_url_report is async
    return await abusech_intel._get_url_report(url)


@mcp.tool()
async def get_file_report(
    hash_value: str
) -> dict:
    """
        Name: Get File Report
        Description: Get a comprehensive file report using its hash (MD5/SHA-1/SHA-256) from MalwareBazaar, URLhaus (only MD5/SHA-256), and ThreatFox
        Parameters:
            - hash: The hash of the file to retrieve the report for (MD5/SHA-1/SHA-256)
    """
    return await abusech_intel._get_file_report(hash_value)

def main() -> None:
    """Run the MCP server for AbuseCH (abuse.ch) tools."""

    logger.info("Starting AbuseCh MCP server...")
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
