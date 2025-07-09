import os
import discord
from dotenv import load_dotenv

_ = load_dotenv()

intents = discord.Intents.default()

client = discord.Client(intents=intents)

# Here is where some code stuff goes apparently
# refer to docs here: https://discordpy.readthedocs.io/en/stable/quickstart.html

token = os.getenv("token")
assert token is not None, "Please add token to .env file"

client.run(token)
