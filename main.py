from bot import bot, load_cogs
from config import config

bot.database.create_databases()
bot.database.check_config()
load_cogs()

bot.run(token=config["token"])
