import asyncio

from services.realtime_service import RealtimeService


async def main():

    service = RealtimeService()

    query = (
        "What is the current USD to INR exchange rate? "
        "Search the web and give the latest available information."
    )

    result = await service.search(query)

    print("\n==============================")
    print("REAL-TIME SEARCH TEST")
    print("==============================")

    print("Provider:", result["provider"])
    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")
    for source in result["sources"]:
        print(source)


if __name__ == "__main__":
    asyncio.run(main())