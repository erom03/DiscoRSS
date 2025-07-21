from discord.ext import commands
from .basic import setup_basic
from .feeds import setup_feeds


def register_all_commands(bot: commands.Bot) -> None:
    setup_basic(bot)
    setup_feeds(bot)
