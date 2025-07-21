from discord.ext import commands
from bot.config import get_owner_id


class AddFlags(commands.FlagConverter):
    left: int = commands.flag(default=0, description="Number on the left")
    right: int = commands.flag(default=0, description="Number on the right")


def setup_basic(bot: commands.Bot):
    @bot.hybrid_command()
    async def test(ctx):
        await ctx.send("This is a hybrid command!")

    @bot.hybrid_command()
    async def add(ctx, *, flags: AddFlags):
        """Adds two numbers together."""
        await ctx.send(flags.left + flags.right)

    @bot.command()
    async def sync(ctx):
        if ctx.author.id != get_owner_id():
            await ctx.send("You must be the owner to use this command!")
            return

        await bot.tree.sync()
        await ctx.send("Command tree synced.")
