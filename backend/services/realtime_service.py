"""Real-time information service for EchoSphere.

Provider priority:
1. Groq Compound Mini
2. Tavily
3. OpenRouter

Only one provider is used at a time.
A fallback is attempted only when the previous provider fails.
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()


class RealtimeService:

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

    async def search(self, query: str):
        """Get current information using one provider at a time."""

        # ---------------------------------------------------------
        # 1. GROQ COMPOUND MINI
        # ---------------------------------------------------------

        if self.groq_api_key:

            try:
                result = await self._search_groq(query)

                if result["success"]:
                    return result

            except Exception as exc:
                print(
                    f"Groq real-time search failed: "
                    f"{type(exc).__name__}: {exc}"
                )

        # ---------------------------------------------------------
        # 2. TAVILY FALLBACK
        # ---------------------------------------------------------

        if self.tavily_api_key:

            try:
                result = await self._search_tavily(query)

                if result["success"]:
                    return result

            except Exception as exc:
                print(
                    f"Tavily real-time search failed: "
                    f"{type(exc).__name__}: {exc}"
                )

        # ---------------------------------------------------------
        # 3. OPENROUTER FALLBACK
        # ---------------------------------------------------------

        if self.openrouter_api_key:

            try:
                result = await self._search_openrouter(query)

                if result["success"]:
                    return result

            except Exception as exc:
                print(
                    f"OpenRouter fallback failed: "
                    f"{type(exc).__name__}: {exc}"
                )

        # ---------------------------------------------------------
        # NOTHING WORKED
        # ---------------------------------------------------------

        return {
            "success": False,
            "provider": None,
            "answer": (
                "I am unable to retrieve current information right now."
            ),
            "sources": [],
        }

    # =============================================================
    # GROQ COMPOUND MINI
    # =============================================================

    async def _search_groq(self, query: str):

        from groq import AsyncGroq

        client = AsyncGroq(
            api_key=self.groq_api_key
        )

        # Keep the request minimal.
        #
        # Compound Mini automatically decides whether
        # it needs to use web search.
        response = await client.chat.completions.create(
            model="groq/compound-mini",
            messages=[
                {
                    "role": "user",
                    "content": query,
                }
            ],
        )

        message = response.choices[0].message

        answer = message.content

        if not answer:
            return {
                "success": False,
                "provider": "groq",
                "answer": "",
                "sources": [],
            }

        sources = []

        executed_tools = getattr(
            message,
            "executed_tools",
            None,
        )

        if executed_tools:

            for tool in executed_tools:

                search_results = getattr(
                    tool,
                    "search_results",
                    None,
                )

                if search_results:

                    results = getattr(
                        search_results,
                        "results",
                        None,
                    )

                    if results:

                        for result in results:

                            url = None

                            if isinstance(result, dict):
                                url = result.get("url")
                            else:
                                url = getattr(
                                    result,
                                    "url",
                                    None,
                                )

                            if url:
                                sources.append(url)

        return {
            "success": True,
            "provider": "groq",
            "answer": answer,
            "sources": sources,
        }

    # =============================================================
    # TAVILY
    # =============================================================

    async def _search_tavily(self, query: str):

        url = "https://api.tavily.com/search"

        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 5,
            "include_answer": True,
            "include_raw_content": False,
        }

        async with httpx.AsyncClient(
            timeout=15.0
        ) as client:

            response = await client.post(
                url,
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

        answer = data.get("answer")

        if not answer:

            results = data.get(
                "results",
                []
            )

            if results:

                answer = "\n".join(
                    result.get("content", "")
                    for result in results
                    if result.get("content")
                )

        if not answer:

            return {
                "success": False,
                "provider": "tavily",
                "answer": "",
                "sources": [],
            }

        sources = [
            result.get("url")
            for result in data.get("results", [])
            if result.get("url")
        ]

        return {
            "success": True,
            "provider": "tavily",
            "answer": answer,
            "sources": sources,
        }

    # =============================================================
    # OPENROUTER
    # =============================================================

    async def _search_openrouter(self, query: str):

        url = "https://openrouter.ai/api/v1/chat/completions"

        payload = {
            "model": "openrouter/free",
            "messages": [
                {
                    "role": "user",
                    "content": query,
                }
            ],
        }

        headers = {
            "Authorization": (
                f"Bearer {self.openrouter_api_key}"
            ),
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            timeout=20.0
        ) as client:

            response = await client.post(
                url,
                json=payload,
                headers=headers,
            )

            response.raise_for_status()

            data = response.json()

        choices = data.get("choices", [])

        if not choices:

            return {
                "success": False,
                "provider": "openrouter",
                "answer": "",
                "sources": [],
            }

        answer = choices[0].get(
            "message",
            {}
        ).get("content")

        if not answer:

            return {
                "success": False,
                "provider": "openrouter",
                "answer": "",
                "sources": [],
            }

        return {
            "success": True,
            "provider": "openrouter",
            "answer": answer,
            "sources": [],
        }