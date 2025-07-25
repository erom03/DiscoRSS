import discord
import asyncio
import logging
from discord.ext import commands
from bot.config import get_token
from bot import db
from bot.commands import register_all_commands
from bot.rss_poller import RSSPoller

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    description="A selfhosted RSS reader for discord",
    intents=intents,
)

rss_poller = None


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    
    global rss_poller
    rss_poller = RSSPoller(bot)
    rss_poller.start_polling()
    print(f"RSS polling started")


async def setup():
    await db.init_db()
    register_all_commands(bot)

    try:
        await bot.start(get_token())
    finally:
        if rss_poller:
            rss_poller.stop_polling()


asyncio.run(setup())
