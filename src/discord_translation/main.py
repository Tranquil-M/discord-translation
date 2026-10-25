import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COGS_DIR = Path(__file__).resolve().parent / "cogs"

load_dotenv(PROJECT_ROOT / ".env")
TOKEN = os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX")

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.default())


async def load_cogs():
    for file in os.listdir(COGS_DIR):
        if file.endswith(".py") and file != "__init__.py":
            await bot.load_extension(f"discord_translation.cogs.{file[:-3]}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


import asyncio

asyncio.run(main())
