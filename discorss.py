import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

_ = load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

description = """A selfhosted RSS reader for discord"""

bot = commands.Bot(command_prefix="!", description=description, intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


@bot.hybrid_command()
async def test(ctx):
    await ctx.send("This is a hybrid command!")


class AddFlags(commands.FlagConverter):
    left: int = commands.flag(default=0, description="Number on the left")
    right: int = commands.flag(default=0, description="Number on the right")


@bot.hybrid_command()
async def add(ctx, *, flags: AddFlags):
    """Adds two numbers together."""
    await ctx.send(flags.left + flags.right)


@bot.command()
async def sync(ctx):
    OWNER_USERID = os.getenv("userid")
    if OWNER_USERID is None:
        await ctx.send("Please configure user id in .env file")
        return

    if ctx.author.id != int(OWNER_USERID):
        await ctx.send("You must be the owner to use this command!")
        return

    await bot.tree.sync()
    await ctx.send("Command tree synced.")


token = os.getenv("token")
assert token is not None, "Please add token to .env file"

bot.run(token)
