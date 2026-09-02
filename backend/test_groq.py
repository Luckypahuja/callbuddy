import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

print("API key loaded:", bool(api_key))

client = Groq(
    api_key=api_key
)

response = client.chat.completions.create(
    model="groq/compound-mini",
    messages=[
        {
            "role": "user",
            "content": "What is the current weather in Delhi?",
        }
    ],
)

print("\n==============================")
print("GROQ COMPOUND TEST")
print("==============================")

print("\nAnswer:")
print(response.choices[0].message.content)

print("\nExecuted tools:")
print(response.choices[0].message.executed_tools)