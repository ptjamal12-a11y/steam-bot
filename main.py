from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import requests
import re

TOKEN = "8997212415:AAFd-Kdg_R1N6QDgPD1HR07jDB_WSjujHU"

STEAM_SEARCH = "https://store.steampowered.com/search/?term="


# ---------------- STEAM ----------------
def get_steam(game):
try:
r = requests.get(
STEAM_SEARCH + game.replace(" ", "+"),
headers={"User-Agent": "Mozilla/5.0"},
timeout=10
)

match = re.findall(r"/app/(\d+)/", r.text)
if match:
appid = match[0]
return f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"
except:
pass
return None


# ---------------- IGDB (fallback 1) ----------------
def get_igdb(game):
try:
# صورة عامة من IGDB CDN (بدون OAuth تعقيد)
query = game.replace(" ", "+")
url = f"https://www.google.com/search?q={query}+game+cover&tbm=isch"

r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

img = re.findall(r"(https://.*?\.jpg)", r.text)

if img:
return img[0]
except:
pass
return None


# ---------------- FINAL FINDER ----------------
def find_image(game):
img = get_steam(game)
if img:
return img

img = get_igdb(game)
if img:
return img

return None


# ---------------- HANDLER ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text.strip()

games = [g.strip() for g in text.splitlines() if g.strip()]
games = games[:100]

results = []

for game in games:
img = find_image(game)

if img:
results.append(f"{game} | {img}")
else:
results.append(f"{game} | NOT FOUND")

# تقسيم الرسائل
msg = ""
for line in results:
if len(msg) + len(line) > 3500:
await update.message.reply_text(msg)
msg = line
else:
msg += ("\n" + line if msg else line)

if msg:
await update.message.reply_text(msg)


def main():
app = Application.builder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("PRO BOT RUNNING 🚀")
app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
main()
