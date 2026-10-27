import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML

from .main import run

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_VARS = PROJECT_ROOT / ".env"

if os.path.exists(ENV_VARS) and os.path.isfile(ENV_VARS):
    load_dotenv(ENV_VARS)
else:
    print("No .env file found in project root.")
    token = prompt(
        HTML("<ansiblue>Token: </ansiblue>"),
        placeholder=HTML("<ansigray>Paste Token Here</ansigray>"),
    )
    os.environ["TOKEN"] = token


asyncio.run(run())
