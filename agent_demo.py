import asyncio
import os

from agent_framework import RawAgent
from agent_framework.openai import OpenAIChatClient


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "La variable OPENAI_API_KEY n'est pas définie. "
            "            read -s -p "Clé OpenAI : " OPENAI_API_KEY
            export OPENAI_API_KEY
            uvicorn src.app:app --reload --host 0.0.0.0 --port 8000Définis-la dans ce terminal avant de lancer le script."
        )

    agent = RawAgent(
        client=OpenAIChatClient(model="gpt-4o-mini", api_key=api_key),
        instructions="Tu es un assistant qui explique les choses simplement.",
    )

    response = await agent.run("Explique-moi ce qu'est une API en deux phrases.")
    print(response.text)


asyncio.run(main())