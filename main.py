from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import re

TOKEN = "‏8997212415:AAFScTTokC9ugWm3Bu0MDcVW1DJAQaGxmy4"

STEAM_SEARCH = "https://store.steampowered.com/search/?term="

def get_image(game):
    try:
        r = requests.get(STEAM_SEARCH + game.replace(" ", "+"))
        matches = re.findall(r"/app/(\d+)/", r.text)

        if matches:
            appid = matches[0]
            img = f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"
            return game, img
    except:
        pass

    return game, "NOT FOUND"

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = " ".join(context.args)

    if not q:
        await update.message.reply_text("اكتب: /game اسم اللعبة")
        return

    title, img = get_image(q)
    await update.message.reply_text(f"{title}\n{img}")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("game", game))

app.run_polling()
