import discord
from deep_translator import MyMemoryTranslator
from discord import app_commands
from discord.ext import commands

from discord_translation.database import create_channel, get_channels

SUPPORTED_LANGUAGES = [
    app_commands.Choice(name="Spanish", value="spanish"),
    app_commands.Choice(name="German", value="german"),
    app_commands.Choice(name="Czech", value="czech"),
    app_commands.Choice(name="English", value="english"),
]


class LiveTranslation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhook_cache = {}

    async def send_as_user(
        self,
        payload: discord.Message,
        translated_text: str,
        channel: discord.TextChannel,
    ):

        author_name = payload.author.name
        channel_id = channel.id
        key = f"{author_name}-{channel_id}"

        if key not in self.webhook_cache:
            webhook = await channel.create_webhook(name=key)
            self.webhook_cache[key] = webhook
        else:
            webhook = self.webhook_cache.get(key)

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

    def translate(self, text, language) -> str | list[str]:
        return MyMemoryTranslator(source="auto", target=language).translate(text)

    @app_commands.command(
        name="create_mirror",
        description="Create a channel that mirrors languages from another.",
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

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog '{__name__}' loaded.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        channels = await get_channels(message.guild)
        if not any(message.channel.id in channel for channel in channels):
            print(message.channel.id, channels)
            print("not in mirror")
            return

        for channel_id, language in channels:
            if message.channel.id == channel_id:
                print("not doing this in this channel lol", channel_id)
                continue
            print(f"Channels: {channels}, ID: {channel_id}, Language: {language}")
            await self.send_as_user(
                message, message.content, await message.guild.fetch_channel(channel_id)
            )

    async def cog_unload(self):
        await self.cleanup_webhook_cache()


async def setup(bot):
    await bot.add_cog(LiveTranslation(bot))
