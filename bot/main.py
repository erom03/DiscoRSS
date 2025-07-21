import discord
import asyncio
from discord.ext import commands
from bot.config import get_token
from bot import db
from bot.commands import register_all_commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    description="A selfhosted RSS reader for discord",
    intents=intents,
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


# Load database and register commands
async def setup():
    await db.init_db()
    register_all_commands(bot)

    await bot.start(get_token())


asyncio.run(setup())
