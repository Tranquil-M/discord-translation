import asyncio
import io
import re

import discord
from discord import app_commands
from discord.ext import commands

from discord_translation.database import create_channel, get_channels
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
        self.webhook_cache = {}
        self.translator_cache = {}

    async def send_as_user(
        self,
        payload: discord.Message,
        translated_text: str,
        channel: discord.TextChannel,
    ):
        try:
            author_name = payload.author.name
            channel_id = channel.id
            identifier = f"{author_name}-{channel_id}"

            webhook = self.webhook_cache.get(identifier)
            if webhook is None:
                webhook = await channel.create_webhook(name=identifier)
                self.webhook_cache[identifier] = webhook

            files = []
            try:
                for attachment in payload.attachments or []:
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
        except Exception as e:
            print(e)

    async def cleanup_webhook_cache(self):
        for webhook in list(self.webhook_cache.values()):
            try:
                await webhook.delete(reason="Translator cog unloaded")
            except discord.NotFound:
                pass
            except discord.HTTPException as e:
                print(f"Could not delete webhook: {e}")

        self.webhook_cache.clear()

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
        name="translate",
        description="Manually translate text into any supported language. Returns as ephemeral.",
    )
    @app_commands.choices(target=SUPPORTED_LANGUAGES)
    async def manual_translation(
        self, interaction: discord.Interaction, text: str, target: str
    ):
        await interaction.response.defer(ephemeral=True)
        translated_text = await asyncio.to_thread(self.translate, text, target)
        await interaction.followup.send(self.translate(text, target))

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog '{__name__}' loaded.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        channels = await get_channels(message.guild)
        if not any(message.channel.id in channel for channel in channels):
            return

        try:
            for channel_id, language in channels:
                if message.channel.id == channel_id:
                    continue

                translated_text = await asyncio.to_thread(
                    self.translate, message.content, language
                )

                await self.send_as_user(
                    message,
                    translated_text,
                    await message.guild.fetch_channel(channel_id),
                )
        except Exception as e:
            print(e)

    async def cog_unload(self):
        await self.cleanup_webhook_cache()


async def setup(bot):
    await bot.add_cog(LiveTranslation(bot))
