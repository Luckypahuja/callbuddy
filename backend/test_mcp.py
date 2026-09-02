import asyncio

from mcp import Client


async def main():
   async with Client("https://germproof-viscous-unlearned.ngrok-free.dev/mcp/") as client:

        result = await client.list_tools()

        print("AVAILABLE TOOLS:")

        print(result)

        print("\nSEARCH RESULT:")

        search_result = await client.call_tool(
            "search_web",
            {
                "query": "What is the current USD to INR exchange rate?"
            },
        )

        print(search_result)


if __name__ == "__main__":
    asyncio.run(main())