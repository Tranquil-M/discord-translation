import asyncio
import io
import re

import discord
from discord import app_commands
from discord.ext import commands

from discord_translation.database import (
    create_channel,
    delete_channel,
    delete_webhook,
    get_channels,
    get_webhook_id,
    save_webhook,
)
from discord_translation.translators.libre import LibreTranslator

SUPPORTED_LANGUAGES = [
    app_commands.Choice(name="Spanish", value="Spanish"),
    app_commands.Choice(name="German", value="German"),
    app_commands.Choice(name="Czech", value="Czech"),
    app_commands.Choice(name="English", value="English"),
    app_commands.Choice(name="French", value="French"),
    app_commands.Choice(name="Portuguese", value="Portuguese"),
    app_commands.Choice(name="Russian", value="Russian"),
    app_commands.Choice(name="Japanese", value="Japanese"),
    app_commands.Choice(name="Korean", value="Korean"),
    app_commands.Choice(name="Arabic", value="Arabic"),
    app_commands.Choice(name="Chinese Simplified", value="Chinese"),
    app_commands.Choice(name="Chinese Traditional", value="Chinese (traditional)"),
    app_commands.Choice(name="Hindi", value="Hindi"),
    app_commands.Choice(name="Italian", value="Italian"),
    app_commands.Choice(name="Turkish", value="Turkish"),
    app_commands.Choice(name="Polish", value="Polish"),
    app_commands.Choice(name="Dutch", value="Dutch"),
]


class LiveTranslation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhook_cache: dict[int, discord.Webhook] = {}
        self.webhook_locks: dict[int, asyncio.Lock] = {}
        self.translator_cache = {}

    async def send_as_user(
        self,
        payload: discord.Message,
        translated_text: str,
        channel: discord.TextChannel,
    ):
        channel_id = channel.id
        lock = self.webhook_locks.setdefault(channel_id, asyncio.Lock())

        try:
            async with lock:
                webhook = self.webhook_cache.get(channel_id)

                if webhook is None:
                    webhook_id = get_webhook_id(channel.guild.id, channel_id)

                    if webhook_id is not None:
                        try:
                            webhook = await self.bot.fetch_webhook(webhook_id)
                        except discord.NotFound:
                            delete_webhook(channel.guild.id, channel_id)

                    if webhook is None:
                        webhook = await channel.create_webhook(
                            name=f"translation-{channel_id}"
                        )
                        save_webhook(
                            channel.guild.id,
                            channel_id,
                            webhook.id,
                        )

                    self.webhook_cache[channel_id] = webhook

            files = []
            try:
                for attachment in payload.attachments:
                    data = await attachment.read()
                    files.append(
                        discord.File(
                            io.BytesIO(data),
                            filename=attachment.filename,
                            spoiler=attachment.is_spoiler(),
                        )
                    )

                await webhook.send(
                    content=translated_text,
                    files=files,
                    username=payload.author.display_name,
                    avatar_url=payload.author.display_avatar.url,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            finally:
                for file in files:
                    file.close()

        except discord.NotFound:
            self.webhook_cache.pop(channel_id, None)
            delete_webhook(channel.guild.id, channel_id)
            print(f"Webhook for channel {channel_id} was not found.")
        except discord.HTTPException as e:
            print(f"Could not send webhook message: {e}")
        except Exception as e:
            print(f"Error sending translated message: {e}")

    async def cleanup_webhook_cache(self):
        self.webhook_cache.clear()
        self.webhook_locks.clear()

    def chunk(self, text, size=500):
        pattern = r"[^.!?]+(?:[.!?]|$)"

        sentences = re.findall(pattern, text)
        chunks = []
        chunk = ""
        for sentence in sentences:
            if len(chunk) + len(sentence) > size:
                chunks.append(chunk)
                chunk = ""
            chunk += sentence
        chunks.append(chunk)
        return chunks

    def translate(self, text, language, source="auto", chunk_size=500) -> str:
        identifier = f"{source}-{language}"
        translator = self.translator_cache.get(identifier)
        if translator is None:
            translator = LibreTranslator(
                source=source,
                target=language,
                custom_url="http://localhost:5000/",
            )
            self.translator_cache[identifier] = translator

        if len(text) > chunk_size:
            chunks = self.chunk(text, size=chunk_size)
            return "".join(translator.translate_batch(chunks))

        return translator.translate(text)

    @app_commands.command(
        name="create_mirror",
        description="Create a channel that mirrors LANGUAGES from another.",
    )
    @app_commands.choices(language=SUPPORTED_LANGUAGES)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def create_mirror(
        self,
        interaction: discord.Interaction,
        language: str,
        *,
        existing_channel: discord.TextChannel | None,
    ):
        await interaction.response.defer(ephemeral=True)
        if existing_channel:
            channel = existing_channel.id
        else:
            channel = await interaction.guild.create_text_channel(language)
            channel = channel.id

        create_channel(interaction.guild.id, channel, language)
        await interaction.followup.send("Channel created.")

    @app_commands.command(
        name="strip_mirrors",
        description="Delete a mirror from a channel.",
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def strip_mirrors(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        await interaction.response.defer(ephemeral=True)
        count = delete_channel(channel.id)
        if count == 0:
            await interaction.followup.send(
                "There aren't any mirrors attatched to this channel."
            )
            return
        await interaction.followup.send(
            f"Stripped {count} mirrors from {channel.mention}"
        )

    @app_commands.command(
        name="translate",
        description="Manually translate text into any supported language. Returns as ephemeral.",
    )
    @app_commands.choices(target=SUPPORTED_LANGUAGES)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def manual_translation(
        self, interaction: discord.Interaction, text: str, target: str
    ):
        await interaction.response.defer(ephemeral=True)
        translated_text = await asyncio.to_thread(
            self.translate,
            text,
            target,
        )
        await interaction.followup.send(translated_text)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog '{__name__}' loaded.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return

        try:
            channels = await get_channels(message.guild)

            if not any(
                channel_id == message.channel.id for channel_id, _language in channels
            ):
                return

            for channel_id, language in channels:
                if message.channel.id == channel_id:
                    continue

                translated_text = await asyncio.to_thread(
                    self.translate,
                    message.content,
                    language,
                )

                target_channel = message.guild.get_channel(channel_id)
                if target_channel is None:
                    try:
                        target_channel = await message.guild.fetch_channel(channel_id)
                    except discord.NotFound:
                        continue

                await self.send_as_user(
                    message,
                    translated_text,
                    target_channel,
                )

        except Exception as e:
            print(f"Error handling message translation: {e}")

    async def cog_unload(self):
        await self.cleanup_webhook_cache()


async def setup(bot):
    await bot.add_cog(LiveTranslation(bot))
