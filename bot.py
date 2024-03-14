import disnake
from disnake.ext import commands

from utilities.database import Database

intents = disnake.Intents.all()
bot = commands.Bot(command_prefix="-", intents=intents)
bot.database = Database("database.db")


def load_cogs():
    bot.load_extensions("cogs")


@bot.event
async def on_ready():
    print("Готов")
