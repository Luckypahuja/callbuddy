import os
import asyncio
import httpx

from dotenv import load_dotenv

load_dotenv()


async def main():

    api_key = os.getenv("GROQ_API_KEY")

    print("API key loaded:", bool(api_key))

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {
                "role": "user",
                "content": "Say hello in one sentence.",
            }
        ],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:

        response = await client.post(
            url,
            headers=headers,
            json=payload,
        )

        print("\n==============================")
        print("GROQ NORMAL MODEL TEST")
        print("==============================")

        print("HTTP status:", response.status_code)

        print("\nResponse:")
        print(response.text)


if __name__ == "__main__":
    asyncio.run(main())