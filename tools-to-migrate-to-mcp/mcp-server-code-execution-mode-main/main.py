import asyncio

from mcp_server_code_execution_mode import main as run_bridge


def main() -> None:
    asyncio.run(run_bridge())


if __name__ == "__main__":
    main()
