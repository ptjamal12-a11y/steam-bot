from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import re
import asyncio

TOKEN = "‏8997212415:AAFScTTokC9ugWm3Bu0MDcVW1DJAQaGxmy4"

STEAM_SEARCH = "https://store.steampowered.com/search/?term="


def get_image(game):
    try:
        r = requests.get(STEAM_SEARCH + game.replace(" ", "+"), timeout=10)
        matches = re.findall(r"/app/(\d+)/", r.text)

        if matches:
            appid = matches[0]
            img = f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"
            return game, img
    except:
        pass

    return game, "NOT FOUND"


async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("اكتب: /game اسم اللعبة")
        return

    q = " ".join(context.args)
    title, img = get_image(q)

    await update.message.reply_text(f"{title}\n{img}")


async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("game", game))

    await app.run_polling()


if _name_ == "_main_":
    asyncio.run(main())
