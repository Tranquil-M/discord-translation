import asyncio
from os import environ, listdir
from pathlib import Path

import discord
from discord.ext import commands

COGS_DIR = Path(__file__).resolve().parent / "cogs"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


async def load_cogs():
    for file in listdir(COGS_DIR):
        if file.endswith(".py") and file != "__init__.py":
            await bot.load_extension(f"discord_translation.cogs.{file[:-3]}")


async def unload_cogs():
    for file in listdir(COGS_DIR):
        if file.endswith(".py") and file != "__init__.py":
            await bot.unload_extension(f"discord_translation.cogs.{file[:-3]}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx):
    if ctx.guild is None:
        await ctx.send("This command must be used in a guild, sorry!")
        return

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print("Sync failed:", e)
    finally:
        await ctx.message.delete()


@bot.command(name="reload")
@commands.is_owner()
async def reload(ctx):
    if ctx.guild is None:
        await ctx.send("This command must be used in a guild, sorry!")
        return

    try:
        await unload_cogs()
        await load_cogs()

    except Exception as e:
        print("Failed to reload cogs:", e)
    finally:
        await ctx.message.delete()


async def main():
    async with bot:
        try:
            await load_cogs()
            await bot.start(environ.get("TOKEN"))
        finally:
            # Removing each cog calls its cog_unload hook.
            for cog in list(bot.cogs.values()):
                await bot.remove_cog(cog.qualified_name)


def entry():
    asyncio.run(main())
