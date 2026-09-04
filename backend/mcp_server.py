from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

import asyncio
import base64
import os
import re
import subprocess
import urllib.parse
import webbrowser
import httpx

from services.realtime_service import RealtimeService


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer(
    name="EchoSphere System Control",
    version="1.0.0"
)

realtime_service = RealtimeService()

# ============================================================
# RAPID DUPLICATE-ACTION GUARD
# ============================================================

import time as _action_time

_recent_actions = {}
_DUPLICATE_WINDOW_SECONDS = 2.5


def _duplicate_action(key: str) -> bool:
    now = _action_time.monotonic()
    previous = _recent_actions.get(key)

    # Remove stale entries.
    stale = [
        action_key
        for action_key, timestamp in _recent_actions.items()
        if now - timestamp > _DUPLICATE_WINDOW_SECONDS
    ]
    for action_key in stale:
        _recent_actions.pop(action_key, None)

    if previous is not None and now - previous < _DUPLICATE_WINDOW_SECONDS:
        return True

    _recent_actions[key] = now
    return False



# ============================================================
# WEB SEARCH
# ============================================================

@mcp.tool(
    name="search_web",
    description="Search the web for current or general information."
)
async def search_web(query: str) -> str:
    try:
        result = await realtime_service.search(query)

        if not result:
            return "No search result was found."

        return str(result)

    except Exception as exc:
        print(f"[MCP] search_web error: {type(exc).__name__}: {exc}")
        return f"Unable to search the web: {exc}"


# ============================================================
# OPEN WINDOWS APPLICATION
# ============================================================

@mcp.tool(
    name="open_application",
    description=(
        "Open a Windows application such as File Explorer, "
        "Task Manager, Notepad, Calculator, Word, Excel, "
        "PowerPoint, Chrome, Edge, VS Code, Paint, Settings, "
        "Terminal, Command Prompt or WhatsApp."
    )
)
async def open_application(application: str) -> str:

    requested = application.strip()
    app = requested.lower()

    print(f"[MCP] open_application requested: {requested}", flush=True)

    action_key = f"open_application:{app}"
    if _duplicate_action(action_key):
        return f"IGNORED: Duplicate open request for {requested}. The application was already opened."

    applications = {
        "file explorer": ["explorer.exe"],
        "file manager": ["explorer.exe"],
        "windows explorer": ["explorer.exe"],
        "explorer": ["explorer.exe"],

        "task manager": ["taskmgr.exe"],
        "taskmanager": ["taskmgr.exe"],

        "notepad": ["notepad.exe"],
        "calculator": ["calc.exe"],
        "calc": ["calc.exe"],
        "paint": ["mspaint.exe"],
        "microsoft paint": ["mspaint.exe"],

        "terminal": ["wt.exe"],
        "windows terminal": ["wt.exe"],
        "command prompt": ["cmd.exe"],
        "cmd": ["cmd.exe"],

        "word": ["winword.exe"],
        "microsoft word": ["winword.exe"],
        "word document": ["winword.exe"],

        "excel": ["excel.exe"],
        "microsoft excel": ["excel.exe"],

        "powerpoint": ["powerpnt.exe"],
        "microsoft powerpoint": ["powerpnt.exe"],

        "vs code": ["code.exe"],
        "visual studio code": ["code.exe"],
        "vscode": ["code.exe"],

        "chrome": ["chrome.exe"],
        "google chrome": ["chrome.exe"],
        "edge": ["msedge.exe"],
        "microsoft edge": ["msedge.exe"],
    }

    # Dedicated URI handlers.
    uri_handlers = {
        "settings": "ms-settings:",
        "windows settings": "ms-settings:",
    }

    if app in uri_handlers:
        try:
            os.startfile(uri_handlers[app])
            print(f"[MCP] Successfully opened URI: {uri_handlers[app]}", flush=True)
            return f"SUCCESS: Opened {requested}. Do not perform another action."
        except Exception as exc:
            print(f"[MCP] URI launch error: {type(exc).__name__}: {exc}", flush=True)
            return f"FAILED: Could not open {requested}: {exc}"

    command = applications.get(app)

    if not command:
        return (
            f"FAILED: I don't have a configured launcher for {requested}. "
            "Ask the user to name a supported Windows application."
        )

    try:
        # Resolve the executable first. This gives us a real failure instead
        # of silently starting a broken command.
        import shutil
        executable = shutil.which(command[0])

        if executable is None:
            # Windows system executables can normally be found by CreateProcess
            # even when shutil.which is conservative, so try the command anyway.
            executable = command[0]

        if app in {"file explorer", "file manager", "windows explorer", "explorer"}:
            # explorer.exe is a shell process. Launch it directly and do not
            # inherit the backend's stdio.
            subprocess.Popen(
                ["explorer.exe"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS
                | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            subprocess.Popen(
                [executable],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS
                | subprocess.CREATE_NEW_PROCESS_GROUP,
            )

        print(f"[MCP] Successfully launched: {requested} -> {executable}", flush=True)

        return (
            f"SUCCESS: Opened {requested}. "
            "This task is complete. Do not call another tool for this request."
        )

    except FileNotFoundError:
        return f"FAILED: {requested} is not installed or could not be found."

    except Exception as exc:
        print(
            f"[MCP] open_application error: {type(exc).__name__}: {exc}",
            flush=True,
        )
        return f"FAILED: Unable to open {requested}: {exc}"


# ============================================================
# OPEN WEBSITE
# ============================================================

@mcp.tool(
    name="open_website",
    description="Open a website in the user's default browser."
)
async def open_website(website: str) -> str:

    requested = website.strip()
    site = requested.lower()

    action_key = f"open_website:{site}"
    if _duplicate_action(action_key):
        return f"IGNORED: Duplicate website-open request for {requested}. It was already opened."

    websites = {
        "youtube": "https://www.youtube.com/",
        "google": "https://www.google.com/",
        "gmail": "https://mail.google.com/",
        "google maps": "https://www.google.com/maps/",
        "maps": "https://www.google.com/maps/",
        "whatsapp": "https://web.whatsapp.com/",
        "whatsapp web": "https://web.whatsapp.com/",
        "github": "https://github.com/",
        "linkedin": "https://www.linkedin.com/",
        "amazon": "https://www.amazon.in/",
        "amazon india": "https://www.amazon.in/",
        "amazon.in": "https://www.amazon.in/",
        "flipkart": "https://www.flipkart.com/",
        "instagram": "https://www.instagram.com/",
        "facebook": "https://www.facebook.com/",
        "twitter": "https://x.com/",
        "x": "https://x.com/",
        "reddit": "https://www.reddit.com/",
        "netflix": "https://www.netflix.com/",
        "spotify": "https://open.spotify.com/",
        "chatgpt": "https://chatgpt.com/",
        "openai": "https://openai.com/",
    }

    url = websites.get(site)

    if not url:
        # Allow a direct domain such as amazon.in, flipkart.com, or example.com.
        candidate = requested.strip().rstrip("/")
        if candidate.startswith(("http://", "https://")):
            url = candidate
        elif re.match(r"^(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/.*)?$", candidate, re.IGNORECASE):
            url = "https://" + candidate
        else:
            return (
                f"FAILED: I don't recognize the website {requested}. "
                "Try a known site name or say the full domain, for example amazon.in."
            )

    try:
        # Open exactly one browser navigation for this tool call.
        subprocess.Popen(
            ["cmd", "/c", "start", "", url],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

        print(f"[MCP] Opened website: {url}", flush=True)

        return (
            f"SUCCESS: Opened {requested}. "
            "This task is complete. Do not call another tool for this request."
        )

    except Exception as exc:
        print(
            f"[MCP] open_website error: {type(exc).__name__}: {exc}",
            flush=True,
        )
        return f"FAILED: Unable to open {requested}: {exc}"


# ============================================================
# PLAY YOUTUBE
# ============================================================

@mcp.tool(
    name="play_youtube",
    description=(
        "Open YouTube search results for a requested song or music. "
        "Use this when the user asks to play music."
    )
)
async def play_youtube(song: str) -> str:

    song = song.strip()

    action_key = f"play_youtube:{song.lower()}"
    if _duplicate_action(action_key):
        return f"IGNORED: Duplicate YouTube request for {song}. It was already opened."

    if not song:
        return "FAILED: Please tell me which song you want to play."

    query = urllib.parse.quote_plus(song)
    url = f"https://www.youtube.com/results?search_query={query}"

    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "", url],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )

        print(f"[MCP] YouTube opened for: {song}", flush=True)

        return (
            f"SUCCESS: Opened YouTube search for {song}. "
            "Do not call WhatsApp, open_website, or any other tool for this request."
        )

    except Exception as exc:
        print(
            f"[MCP] play_youtube error: {type(exc).__name__}: {exc}",
            flush=True,
        )
        return f"FAILED: Unable to open YouTube for {song}: {exc}"


# ============================================================
# GEOCODING
# ============================================================

async def geocode_place(place: str):

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": place,
        "format": "json",
        "limit": 1,
        "countrycodes": "in",
    }

    headers = {
        "User-Agent": "EchoSphere-CallingBuddy/1.0"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:

        response = await client.get(
            url,
            params=params,
            headers=headers
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            return None

        return {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
            "name": data[0].get("display_name", place),
        }


# ============================================================
# ROUTE CALCULATION
# ============================================================

async def calculate_route(
    origin_lat,
    origin_lon,
    destination_lat,
    destination_lon
):

    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{origin_lon},{origin_lat};"
        f"{destination_lon},{destination_lat}"
    )

    params = {
        "overview": "false"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:

        response = await client.get(
            url,
            params=params
        )

        response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":
            return None

        routes = data.get("routes", [])

        if not routes:
            return None

        route = routes[0]

        return {
            "distance_km": route["distance"] / 1000,
            "duration_minutes": route["duration"] / 60,
        }


# ============================================================
# DISTANCE + GOOGLE MAPS
# ============================================================

@mcp.tool(
    name="get_directions",
    description=(
        "Calculate driving distance and approximate travel time "
        "between two places and open the route in Google Maps."
    )
)
async def get_directions(
    destination: str,
    origin: str = "",
    travel_mode: str = "driving"
) -> str:

    destination = destination.strip()
    origin = origin.strip()

    print(
        f"[MCP] get_directions: "
        f"{origin or 'current location'} -> {destination}"
    )

    if not destination:
        return "Please tell me the destination."

    try:

        # ----------------------------------------------------
        # If origin was not supplied, use current location
        # through Google Maps only.
        # ----------------------------------------------------

        if not origin:

            encoded_destination = urllib.parse.quote_plus(
                destination
            )

            maps_url = (
                "https://www.google.com/maps/dir/"
                f"?api=1"
                f"&destination={encoded_destination}"
                f"&travelmode={travel_mode}"
            )

            webbrowser.open(maps_url)

            return (
                f"I opened Google Maps for directions to "
                f"{destination}."
            )

        # ----------------------------------------------------
        # Geocode origin
        # ----------------------------------------------------

        origin_location = await geocode_place(origin)

        if not origin_location:
            return (
                f"I could not find the starting location "
                f"{origin}."
            )

        # ----------------------------------------------------
        # Geocode destination
        # ----------------------------------------------------

        destination_location = await geocode_place(
            destination
        )

        if not destination_location:
            return (
                f"I could not find the destination "
                f"{destination}."
            )

        # ----------------------------------------------------
        # Calculate route
        # ----------------------------------------------------

        route = await calculate_route(
            origin_location["lat"],
            origin_location["lon"],
            destination_location["lat"],
            destination_location["lon"],
        )

        if not route:
            return (
                f"I found both locations but could not "
                f"calculate the route."
            )

        distance_km = route["distance_km"]
        duration_minutes = route["duration_minutes"]

        # ----------------------------------------------------
        # Open Google Maps route
        # ----------------------------------------------------

        encoded_origin = urllib.parse.quote_plus(origin)
        encoded_destination = urllib.parse.quote_plus(
            destination
        )

        maps_url = (
            "https://www.google.com/maps/dir/"
            "?api=1"
            f"&origin={encoded_origin}"
            f"&destination={encoded_destination}"
            f"&travelmode={travel_mode}"
        )

        webbrowser.open(maps_url)

        # ----------------------------------------------------
        # Human-readable response
        # ----------------------------------------------------

        if distance_km < 1:
            distance_text = f"{distance_km * 1000:.0f} meters"
        else:
            distance_text = f"{distance_km:.1f} kilometers"

        if duration_minutes < 60:
            duration_text = (
                f"{round(duration_minutes)} minutes"
            )
        else:
            hours = int(duration_minutes // 60)
            minutes = int(round(duration_minutes % 60))

            if minutes:
                duration_text = (
                    f"{hours} hours {minutes} minutes"
                )
            else:
                duration_text = f"{hours} hours"

        return (
            f"The driving distance from {origin} to "
            f"{destination} is approximately {distance_text}, "
            f"with an estimated travel time of {duration_text}. "
            f"I also opened the route in Google Maps."
        )

    except httpx.TimeoutException:

        return (
            "The map service took too long to respond. "
            "Please try the distance request again."
        )

    except Exception as exc:

        print(
            f"[MCP] get_directions error: "
            f"{type(exc).__name__}: {exc}"
        )

        return (
            "I was unable to calculate the route right now. "
            f"Technical error: {exc}"
        )



# ============================================================
# WHATSAPP MESSAGE
# ============================================================

@mcp.tool(
    name="send_whatsapp_message",
    description="Open a WhatsApp chat for a phone number with a pre-filled message."
)
async def send_whatsapp_message(phone_number: str, message: str) -> str:
    phone = re.sub(r"\D", "", phone_number or "")
    message = (message or "").strip()
    if not phone:
        return "Please provide the WhatsApp phone number including country code."
    if not message:
        return "Please provide the message."
    url = f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"
    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "", url],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        return (
            f"SUCCESS: Opened WhatsApp for {phone_number} with the message filled in. "
            "Do not call another tool for this request."
        )
    except Exception as exc:
        return f"Unable to open WhatsApp: {exc}"


# ============================================================
# WHATSAPP CALL
# ============================================================

@mcp.tool(
    name="call_whatsapp",
    description=(
        "Open a WhatsApp chat for a phone number so the user can place a "
        "WhatsApp voice call. Requires the phone number with country code."
    )
)
async def call_whatsapp(phone_number: str) -> str:
    phone = re.sub(r"\D", "", phone_number or "")

    if not phone:
        return "Please provide the WhatsApp phone number including country code."

    # WhatsApp's public click-to-chat URL opens the contact/chat.
    # It does not expose a supported public URL that silently starts a voice call.
    url = f"https://wa.me/{phone}"

    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "", url],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        print(f"[MCP] WhatsApp call contact opened for: {phone}", flush=True)
        return (
            f"SUCCESS: Opened WhatsApp for {phone_number}. "
            "The contact chat is ready; start the WhatsApp voice call from there. "
            "Do not call another tool for this request."
        )
    except Exception as exc:
        print(f"[MCP] call_whatsapp error: {type(exc).__name__}: {exc}", flush=True)
        return f"FAILED: Unable to open WhatsApp for {phone_number}: {exc}"


# ============================================================
# EMAIL
# ============================================================

@mcp.tool(
    name="compose_email",
    description="Open the default email application with recipient, subject and message pre-filled."
)
async def compose_email(recipient: str, subject: str = "", message: str = "") -> str:
    recipient = recipient.strip()
    if not recipient:
        return "Please provide the email recipient."
    params = urllib.parse.urlencode({"subject": subject.strip(), "body": message.strip()})
    try:
        os.startfile(f"mailto:{urllib.parse.quote(recipient)}?{params}")
        return f"I opened a new email to {recipient}. Please review and send it."
    except Exception as exc:
        return f"Unable to open the email composer: {exc}"


# ============================================================
# GOOGLE CALENDAR
# ============================================================

@mcp.tool(
    name="create_calendar_event",
    description="Open Google Calendar with a new event pre-filled for review."
)
async def create_calendar_event(title: str, start: str, end: str = "", details: str = "") -> str:
    if not title.strip() or not start.strip():
        return "Please provide an event title and start time."
    text = title.strip()
    if details.strip():
        text += f" — {details.strip()}"
    url = "https://calendar.google.com/calendar/u/0/r/eventedit?" + urllib.parse.urlencode({"text": text})
    try:
        webbrowser.open(url)
        return f"I opened Google Calendar for {title}. Please review the time and save it."
    except Exception as exc:
        return f"Unable to open Google Calendar: {exc}"


# ============================================================
# FILE SEARCH
# ============================================================

@mcp.tool(
    name="find_file",
    description="Search common Windows user folders for a file or folder by name and open the first match."
)
async def find_file(name: str) -> str:
    name = name.strip()
    if not name:
        return "Please provide the file or folder name."

    home = os.path.expanduser("~")
    roots = [os.path.join(home, x) for x in ("Desktop", "Documents", "Downloads", "Pictures", "Videos")]
    matches = []
    target = name.lower()

    def search():
        for root in roots:
            if not os.path.exists(root):
                continue
            for current, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if d.lower() not in {"node_modules", ".git", "__pycache__"}]
                for item in files + dirs:
                    if target in item.lower():
                        matches.append(os.path.join(current, item))
                        if len(matches) >= 10:
                            return

    try:
        await asyncio.wait_for(asyncio.to_thread(search), timeout=12)
        if not matches:
            return f"I could not find '{name}' in your common user folders."
        os.startfile(matches[0])
        return f"I found and opened {os.path.basename(matches[0])}."
    except asyncio.TimeoutError:
        return "The file search took too long. Please give me a more specific name."
    except Exception as exc:
        return f"Unable to search for the file: {exc}"


# ============================================================
# WHAT'S ON MY SCREEN — SCREENSHOT + VISION AI
# ============================================================

def _capture_screen_base64():
    from PIL import ImageGrab
    from io import BytesIO

    image = ImageGrab.grab(all_screens=True)
    max_width = 1600
    if image.width > max_width:
        ratio = max_width / image.width
        image = image.resize((max_width, int(image.height * ratio)))

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=80)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@mcp.tool(
    name="whats_on_my_screen",
    description="Take a screenshot and ask a vision AI model to answer what is visible or explain it."
)
async def whats_on_my_screen(question: str = "") -> str:
    question = question.strip() or (
        "Describe what is visible on the screen. Read important text and explain "
        "errors, applications, buttons, or other useful information."
    )

    # Use Groq vision instead of OpenRouter. This avoids the current
    # OpenRouter credit/token-limit failure and keeps the vision feature
    # on the same provider already used by EchoSphere.
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Screen analysis requires GROQ_API_KEY in the backend .env file."

    try:
        image_b64 = await asyncio.to_thread(_capture_screen_base64)
        payload = {
            "model": "qwen/qwen3.8-27b",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }],
            "temperature": 0.1,
            "max_tokens": 300
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )

        response.raise_for_status()
        data = response.json()
        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if isinstance(answer, list):
            answer = " ".join(x.get("text", "") for x in answer if isinstance(x, dict))
        return str(answer).strip() or "The vision model did not return an answer."

    except ImportError:
        return "Screen capture requires Pillow. Run: pip install pillow"
    except httpx.HTTPStatusError as exc:
        print(f"[MCP] screen AI HTTP error: {exc.response.status_code} {exc.response.text[:500]}")
        return f"Screen analysis failed with HTTP {exc.response.status_code}."
    except Exception as exc:
        print(f"[MCP] whats_on_my_screen error: {type(exc).__name__}: {exc}")
        return f"Unable to analyze the screen: {exc}"


# ============================================================
# WINDOWS VOLUME
# ============================================================

@mcp.tool(
    name="control_volume",
    description="Increase, decrease or mute Windows volume."
)
async def control_volume(action: str) -> str:
    action = action.strip().lower()
    keys = {
        "up": "{VOLUME_UP}", "increase": "{VOLUME_UP}",
        "down": "{VOLUME_DOWN}", "decrease": "{VOLUME_DOWN}",
        "mute": "{VOLUME_MUTE}", "unmute": "{VOLUME_MUTE}"
    }
    key = keys.get(action)
    if not key:
        return "Use volume action: up, down, mute or unmute."
    try:
        subprocess.run([
            "powershell", "-NoProfile", "-Command",
            "$w=New-Object -ComObject WScript.Shell; $w.SendKeys('" + key + "')"
        ], timeout=10, check=True)
        return "Volume adjusted."
    except Exception as exc:
        return f"Unable to control volume: {exc}"


# ============================================================
# BLUETOOTH SETTINGS
# ============================================================

@mcp.tool(
    name="open_bluetooth",
    description="Open Windows Bluetooth settings."
)
async def open_bluetooth() -> str:
    try:
        os.startfile("ms-settings:bluetooth")
        print("[MCP] Opened Bluetooth settings.", flush=True)
        return (
            "SUCCESS: Opened Windows Bluetooth settings. "
            "This task is complete. Do not call another tool for this request."
        )
    except Exception as exc:
        return f"Unable to open Bluetooth settings: {exc}"


# ============================================================
# CODING WORKSPACE
# ============================================================

@mcp.tool(
    name="coding_workspace",
    description="Open VS Code, Chrome and a coding website as a multi-step workflow."
)
async def coding_workspace(website: str = "https://leetcode.com/") -> str:
    opened = []
    for command, label in (("code.exe", "VS Code"), ("chrome.exe", "Chrome")):
        try:
            subprocess.Popen([command], shell=False, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            opened.append(label)
        except Exception as exc:
            print(f"[MCP] coding_workspace {label}: {exc}")
    try:
        webbrowser.open(website)
        opened.append("coding website")
    except Exception:
        pass
    return "Coding workspace opened: " + ", ".join(opened) + "." if opened else "I could not open the coding workspace."


# ============================================================
# INTERVIEW MODE
# ============================================================

@mcp.tool(
    name="start_interview",
    description="Start a technical interview practice session."
)
async def start_interview(topic: str = "data structures and algorithms") -> str:
    topic = topic.strip() or "data structures and algorithms"
    return (
        f"Interview mode started for {topic}. Question 1: Explain the difference "
        "between an array and a linked list, and when you would prefer each."
    )


# ============================================================
# NEARBY / EMERGENCY
# ============================================================

@mcp.tool(
    name="find_nearby",
    description="Open Google Maps to search for a nearby place category."
)
async def find_nearby(category: str) -> str:
    category = category.strip()
    if not category:
        return "Please specify what place you need."
    try:
        webbrowser.open("https://www.google.com/maps/search/" + urllib.parse.quote_plus(category))
        return f"I opened Google Maps to find nearby {category}."
    except Exception as exc:
        return f"Unable to open Google Maps: {exc}"


# ============================================================
# WORD
# ============================================================

@mcp.tool(
    name="write_to_word",
    description=(
        "Open Microsoft Word and write the requested text "
        "into a new document."
    )
)
async def write_to_word(text: str) -> str:

    if not text.strip():
        return "Please provide the text you want me to write."

    try:

        import win32com.client

        # Run COM work off the MCP event loop so a slow Word startup
        # cannot freeze the MCP server.
        def _write_word_sync() -> None:
            import pythoncom
            import win32com.client

            # COM apartments are initialized per-thread.  asyncio.to_thread()
            # may use a worker thread that has not been initialized for COM.
            pythoncom.CoInitialize()
            try:
                word = win32com.client.DispatchEx("Word.Application")
                word.Visible = True
                document = word.Documents.Add()
                document.Content.Text = text
                document.Activate()
            finally:
                pythoncom.CoUninitialize()

        await asyncio.wait_for(asyncio.to_thread(_write_word_sync), timeout=30.0)

        print("[MCP] Word opened and text written.")

        return (
            "SUCCESS: Microsoft Word is open and the requested text was written. "
            "Do not perform another action."
        )

    except asyncio.TimeoutError:
        return "Microsoft Word took too long to open. Please make sure Word is installed and not blocked by a dialog."
    except ImportError:
        return "Microsoft Word automation is not installed. Run: pip install pywin32"

    except Exception as exc:

        print(
            f"[MCP] write_to_word error: "
            f"{type(exc).__name__}: {exc}"
        )

        return f"Unable to write to Word: {exc}"


# ============================================================
# WI-FI CONTROL
# ============================================================

@mcp.tool(
    name="control_wifi",
    description="Turn Windows Wi-Fi on or off."
)
async def control_wifi(action: str) -> str:

    action = action.strip().lower()

    if action not in ("on", "off"):
        return "Please specify whether to turn Wi-Fi on or off."

    if action == "on":
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Enable-NetAdapter -Name 'Wi-Fi' -Confirm:$false"
        ]
    else:
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Disable-NetAdapter -Name 'Wi-Fi' -Confirm:$false"
        ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:

            error = result.stderr.strip()

            return (
                f"Unable to turn Wi-Fi {action}. "
                f"{error}"
            )

        return f"Wi-Fi turned {action}."

    except Exception as exc:

        print(
            f"[MCP] control_wifi error: "
            f"{type(exc).__name__}: {exc}"
        )

        return f"Unable to control Wi-Fi: {exc}"


# ============================================================
# MCP SECURITY + HTTP APP
# ============================================================
#
# The installed MCP SDK exposes streamable_http_app(), not
# http_app(). main.py mounts mcp_app at /mcp, so the transport
# path is "/" here. The public MCP endpoint remains:
#
# https://germproof-viscous-unlearned.ngrok-free.dev/mcp/
#
# ============================================================

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
    transport_security=transport_security,
)
