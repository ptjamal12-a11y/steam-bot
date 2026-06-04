from telegram import Update

from telegram.ext import Application, CommandHandler, ContextTypes

from flask import Flask

import threading

import requests

import re

import os



TOKEN = "8997212415:AAFScTTokC9ugWm3Bu0MDcVW1DJAQaGxmy4”



STEAM_SEARCH = "https://store.steampowered.com/search/?term="



web_app = Flask(__name__)



@web_app.route("/")

def home():

    return "Bot is running"



def run_web():

    port = int(os.environ.get("PORT", 10000))

    web_app.run(host="0.0.0.0", port=port)



def get_image(game):

    try:

        r = requests.get(

            STEAM_SEARCH + game.replace(" ", "+"),

            timeout=10

        )



        matches = re.findall(r"/app/(\d+)/", r.text)



        if matches:

            appid = matches[0]

            return (

                game,

                f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"

            )

    except Exception as e:

        print(e)



    return game, "NOT FOUND"



async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text("اكتب: /game اسم اللعبة")

        return



    q = " ".join(context.args)

    title, img = get_image(q)



    await update.message.reply_text(f"{title}\n{img}")



def run_bot():

    app = Application.builder().token(TOKEN).build()



    app.add_handler(CommandHandler("game", game))



    print("Telegram bot started")



    app.run_polling(drop_pending_updates=True)



if __name__ == "__main__":

    threading.Thread(target=run_web).start()

    run_bot()
