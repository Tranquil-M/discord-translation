import discord
from discord.ext import commands


class LiveTranslation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhooks = {}

    async def send_as_user(
        self,
        payload: discord.Message,
        translated_text: str,
        channel: discord.TextChannel,
    ) -> None:
        if payload.author.bot:
            return

        if payload.author.name not in self.webhooks:
            webhook = await channel.create_webhook(name=payload.author.name)
            self.webhooks[payload.author.name] = webhook
        else:
            webhook = self.webhooks.get(payload.author.name)

        print(webhook)
        await webhook.send(
            content=translated_text,
            username=payload.author.display_name,
            avatar_url=payload.author.display_avatar.url,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Cog '{__name__}' loaded.")

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.send_as_user(
            message, message.content, self.bot.get_channel(1450655023846396025)
        )


async def setup(bot):
    await bot.add_cog(LiveTranslation(bot))
