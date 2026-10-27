import re

import discord
from deep_translator import MyMemoryTranslator
from discord import app_commands
from discord.ext import commands
from langdetect import detect

from discord_translation.database import create_channel, get_channels

SUPPORTED_LANGUAGES = [
    app_commands.Choice(name="Spanish", value="spanish"),
    app_commands.Choice(name="German", value="german"),
    app_commands.Choice(name="Czech", value="czech"),
    app_commands.Choice(name="English", value="english"),
    app_commands.Choice(name="French", value="french"),
    app_commands.Choice(name="Portuguese", value="portuguese"),
    app_commands.Choice(name="Russian", value="russian"),
    app_commands.Choice(name="Japanese", value="japanese"),
    app_commands.Choice(name="Korean", value="korean"),
    app_commands.Choice(name="Arabic", value="arabic"),
    app_commands.Choice(name="Chinese Simplified", value="chinese simplified"),
    app_commands.Choice(name="Chinese Traditional", value="chinese traditional"),
    app_commands.Choice(name="Hindi", value="hindi"),
    app_commands.Choice(name="Italian", value="italian"),
    app_commands.Choice(name="Turkish", value="turkish"),
    app_commands.Choice(name="Polish", value="polish"),
    app_commands.Choice(name="Dutch", value="dutch"),
]


LANGUAGES = {
    "es": "spanish",
    "de": "german",
    "cs": "czech",
    "en": "english",
    "fr": "french",
    "pt": "portuguese",
    "ru": "russian",
    "ja": "japanese",
    "ko": "korean",
    "ar": "arabic",
    "zh-cn": "chinese simplified",
    "zh-tw": "chinese traditional",
    "hi": "hindi",
    "it": "italian",
    "tr": "turkish",
    "pl": "polish",
    "nl": "dutch",
}


class LiveTranslation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhook_cache = {}

    async def send_as_user(
        self,
        payload: discord.Message,
        translated_text: str | list[str],
        channel: discord.TextChannel,
    ):

        author_name = payload.author.name
        channel_id = channel.id
        identifier = f"{author_name}-{channel_id}"

        if identifier not in self.webhook_cache:
            webhook = await channel.create_webhook(name=identifier)
            self.webhook_cache[identifier] = webhook
        else:
            webhook = self.webhook_cache.get(identifier)

        await webhook.send(
            content=translated_text,
            username=payload.author.display_name,
            avatar_url=payload.author.display_avatar.url,
            allowed_mentions=discord.AllowedMentions.none(),
        )

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
        pattern = r"[^.!?]*[.!?]"
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
        try:
            if len(text) > chunk_size:
                chunks = self.chunk(text, size=chunk_size)
                translated = MyMemoryTranslator(
                    source=source, target=language
                ).translate_batch(chunks)
                return "".join(translated)
            return MyMemoryTranslator(source="english", target=language).translate(text)
        except Exception as e:
            print(e)
            return ""

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
        detected = LANGUAGES[detect(text)]
        await interaction.followup.send(self.translate(text, target, source=detected))

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

        source_language = LANGUAGES[detect(message.content)]
        for channel_id, language in channels:
            if message.channel.id == channel_id:
                continue

            translated_text = self.translate(message.content, language, source_language)
            await self.send_as_user(
                message, translated_text, await message.guild.fetch_channel(channel_id)
            )

    async def cog_unload(self):
        await self.cleanup_webhook_cache()


async def setup(bot):
    await bot.add_cog(LiveTranslation(bot))
