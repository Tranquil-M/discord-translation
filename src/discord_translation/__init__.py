from asyncio import run
from os import environ
from os.path import exists, isfile
from pathlib import Path

from dotenv import load_dotenv

from .main import main

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_VARS = PROJECT_ROOT / ".env"

if exists(ENV_VARS) and isfile(ENV_VARS):
    load_dotenv(ENV_VARS)
    TOKEN = environ.get("TOKEN")
    if not TOKEN:
        print("No token environment variable found.")
        raise SystemExit(1)
else:
    print("No .env file found in project root.")
    print(
        "Create a new file and define the environment variable TOKEN with your bot token."
    )
    raise SystemExit(1)
