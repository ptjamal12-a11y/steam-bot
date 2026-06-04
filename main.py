from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
from bs4 import BeautifulSoup
import re

TOKEN = "‏8997212415:AAFScTTokC9ugWm3Bu0MDcVW1DJAQaGxmy4"

HEADERS = {"User-Agent": "Mozilla/5.0"}

STEAM_SEARCH = "https://store.steampowered.com/search/?term="
STEAMDB_SEARCH = "https://steamdb.info/search/?a=app&q="


def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        return r.text if r.status_code == 200 else None
    except:
        return None


def find_game(name):
    html = fetch(STEAM_SEARCH + name.replace(" ", "+"))

    if html:
        soup = BeautifulSoup(html, "html.parser")
        results = soup.select(".search_result_row")

        for r in results:
            title = r.select_one(".title").text.strip()
            link = r["href"]

            if name.split()[0].lower() in title.lower():
                m = re.search(r"/app/(\d+)/", link)
                if m:
                    return m.group(1), title

    html = fetch(STEAMDB_SEARCH + name.replace(" ", "+"))

    if html:
        soup = BeautifulSoup(html, "html.parser")
        row = soup.select_one("tr.app")

        if row:
            link = row.select_one("a[href*='/app/']")
            if link:
                m = re.search(r"/app/(\d+)/", link["href"])
                if m:
                    return m.group(1), link.text.strip()

    return None, None


async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("اكتب: /game اسم اللعبة")
        return

    query = " ".join(context.args)

    appid, title = find_game(query)

    if not appid:
        await update.message.reply_text("❌ NOT FOUND")
        return

    image = f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"

    await update.message.reply_text(
        f"🎮 {title}\n\n🆔 {appid}\n\n🖼 {image}"
    )


app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("game", game))

app.run_polling()
