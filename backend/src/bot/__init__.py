import os
import platform
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from ollama import AsyncClient
from pymongo import AsyncMongoClient

from bot.tools import filesystem, web
from bot.helpers import initialize_workspace
from core.agents import Agent, AgentConfig, OllamaAgent
from core.runners import Runner, SimpleRunner
from core.sessions import InMemorySessionService, MongoSessionService, SessionService

WORKSPACE: Path = Path("/home/hyunix/workspace").expanduser().resolve()
RUNNER: Runner | None = None
AGENT: Agent | None = None
SESSION_SERVICE: SessionService | None = None


async def init():
    global AGENT, RUNNER, SESSION_SERVICE

    initialize_workspace(WORKSPACE)

    client = AsyncClient(
        host="https://ollama.com",
        headers={"Authorization": "Bearer " + os.environ["OLLAMA_API_KEY"]},
    )
    agent_config = AgentConfig(model="gpt-oss:20b-cloud")
    AGENT = OllamaAgent(client, agent_config)
    AGENT.tool(filesystem.list_directory)
    AGENT.tool(filesystem.read_file)
    AGENT.tool(filesystem.write_file)
    AGENT.tool(web.web_read)
    AGENT.tool(web.web_search)

    # SESSION_SERVICE = InMemorySessionService()
    mongoclient = AsyncMongoClient(os.environ["MONGO_URI"])
    SESSION_SERVICE = MongoSessionService(mongoclient, collection="sessions")

    RUNNER = SimpleRunner(agent=AGENT, session_service=SESSION_SERVICE)


async def load_prompt() -> str | None:
    BASE_PROMPT = f"""
Current Directory: {os.getcwd()}
Workspace: {os.path.abspath(WORKSPACE)}
Environment:
- Current Date & Time: {datetime.now()}
- OS: {platform.system()} {platform.release()}
"""

    components = [BASE_PROMPT]

    with open(WORKSPACE / "SOUL.md", "r") as fp:
        components.append(fp.read())

    with open(WORKSPACE / "IDENTITY.md", "r") as fp:
        components.append(fp.read())

    with open(WORKSPACE / "USER.md", "r") as fp:
        components.append(fp.read())

    return "\n\n".join(components)


async def get_runner() -> Runner:
    if AGENT is None:
        raise Exception("Agent is not initialized")

    if SESSION_SERVICE is None:
        raise Exception("Session Service is not initialized")

    if RUNNER is None:
        raise Exception("Runner is not initialized")

    AGENT.config.system_prompt = await load_prompt()

    return RUNNER
