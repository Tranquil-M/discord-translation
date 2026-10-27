from os import getenv, listdir
from pathlib import Path

import discord
from discord.ext import commands

COGS_DIR = Path(__file__).resolve().parent / "cogs"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


async def load_cogs():
    for file in listdir(COGS_DIR):
        if file.endswith(".py") and file != "__init__.py":
            await bot.load_extension(f"discord_translation.cogs.{file[:-3]}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(getenv("TOKEN"))
