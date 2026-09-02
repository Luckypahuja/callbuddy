import asyncio

from mcp import Client


async def main():
    async with Client(
        "https://germproof-viscous-unlearned.ngrok-free.dev/mcp/"
    ) as client:

        result = await client.list_tools()

        print("AVAILABLE TOOLS:")
        print(result)

        print("\nOPEN APPLICATION RESULT:")

        application_result = await client.call_tool(
            "open_application",
            {
                "application": "Task Manager"
            },
        )

        print(application_result)


if __name__ == "__main__":
    asyncio.run(main())