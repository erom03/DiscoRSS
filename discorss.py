import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

_ = load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

description = """A selfhosted RSS reader for discord"""

bot = commands.Bot(command_prefix="/", description=description, intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)


token = os.getenv("token")
assert token is not None, "Please add token to .env file"

bot.run(token)
