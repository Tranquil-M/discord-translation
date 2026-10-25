from discord.ext import commands

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello!")

async def setup(bot):
    await bot.add_cog(Example(bot))
