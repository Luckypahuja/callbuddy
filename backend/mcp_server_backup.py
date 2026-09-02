from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from services.realtime_service import RealtimeService


mcp = MCPServer(
    name="EchoSphere Web Search",
    version="1.0.0",
)

realtime_service = RealtimeService()


@mcp.tool(
    name="search_web",
    description=(
        "Search the web for current information. "
        "Use this when the user asks for current prices, "
        "exchange rates, news, weather, or other information "
        "that may have changed."
    ),
)
async def search_web(query: str) -> str:
    result = await realtime_service.search(query)

    if not result.get("success"):
        return "Unable to retrieve current web information right now."

    answer = result.get("answer", "")
    sources = result.get("sources", [])

    if sources:
        answer += "\n\nSources:\n" + "\n".join(sources[:5])

    return answer

transport_security = TransportSecuritySettings(
    allowed_hosts=[
        "127.0.0.1:8000",
        "localhost:8000",
        "germproof-viscous-unlearned.ngrok-free.dev",
    ],
    allowed_origins=[
        "https://germproof-viscous-unlearned.ngrok-free.dev",
    ],
)

mcp_app = mcp.streamable_http_app(
    streamable_http_path="/",
    json_response=True,
    stateless_http=True,
    transport_security=transport_security,
)