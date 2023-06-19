import lightbulb

bot = lightbulb.Bot(prefix="!")

bot.load_extensions(
    "cogs.starboard"
)

bot.run("token")
