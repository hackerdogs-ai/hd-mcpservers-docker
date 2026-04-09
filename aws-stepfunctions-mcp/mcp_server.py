#!/usr/bin/env python3
"""AWS Step Functions MCP Server — placeholder until awslabs package is released."""
import json, logging, os, sys
import boto3
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8625"))
mcp = FastMCP("AWS Step Functions MCP Server", instructions="Run and manage AWS Step Functions state machines.")

@mcp.tool()
def list_state_machines(max_results: int = 10) -> str:
    """List Step Functions state machines in the configured AWS account."""
    try:
        client = boto3.client("stepfunctions", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        r = client.list_state_machines(maxResults=max_results)
        machines = [{"name": m["name"], "arn": m["stateMachineArn"], "type": m["type"]} for m in r.get("stateMachines", [])]
        return json.dumps({"stateMachines": machines, "count": len(machines)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def describe_state_machine(state_machine_arn: str) -> str:
    """Get details of a Step Functions state machine."""
    try:
        client = boto3.client("stepfunctions", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        r = client.describe_state_machine(stateMachineArn=state_machine_arn)
        return json.dumps({"name": r["name"], "arn": r["stateMachineArn"], "definition": r["definition"], "roleArn": r["roleArn"]}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
