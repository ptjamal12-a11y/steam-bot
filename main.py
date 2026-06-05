from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import requests
import re
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = “8997212415:AAFd-Kdg_R1N6QDgPD1HR07jDB_WSjujHU”
STEAM_SEARCH = “https://store.steampowered.com/search/?term=”

–– خدعة Render: سيرفر ويب وهمي لجعل المنصة المجانية تعمل ––

class HealthCheckServer(BaseHTTPRequestHandler):
def do_GET(self):
self.send_response(200)
self.send_header(“Content-type”, “text/html”)
self.end_headers()
self.wfile.write(b”Bot is Alive!”)

def run_health_server():
port = int(os.environ.get(“PORT”, 10000))
server = HTTPServer((“0.0.0.0”, port), HealthCheckServer)
server.serve_forever()

–––––––– STEAM ––––––––

def get_steam(game):
try:
r = requests.get(
STEAM_SEARCH + game.replace(” “, “+”),
headers={“User-Agent”: “Mozilla/5.0”},
timeout=10
)

    matches = re.findall(r"/app/(\d+)/", r.text)
    
    if matches:
        appid = matches[0]
        img = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"
        return img
        
except Exception as e:
    print("STEAM ERROR:", e)

return None


–––––––– GOOGLE FALLBACK ––––––––

def get_google_image(game):
try:
url = f”https://www.google.com/search?q={game}+game+cover&tbm=isch”

    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10
    )

    imgs = re.findall(r"(https://.*?\.jpg)", r.text)

    if imgs:
        return imgs[0]

except Exception as e:
    print("GOOGLE ERROR:", e)

return None


–––––––– FIND IMAGE ––––––––

def find_image(game):
img = get_steam(game)
if img:
return img

img = get_google_image(game)
if img:
    return img

return None


–––––––– HANDLER ––––––––

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not update.message or not update.message.text:
return

text = update.message.text.strip()

games = re.split(r"\n|,", text)
games = [g.strip() for g in games if g.strip()][:100]

if not games:
    await update.message.reply_text("ارسل أسماء ألعاب")
    return

results = []

for game in games:
    img = find_image(game)

    if img:
        results.append(f"{game} | {img}")
    else:
        results.append(f"{game} | NOT FOUND")

msg = ""

for line in results:
    if len(msg) + len(line) > 3500:
        await update.message.reply_text(msg)
        msg = line
    else:
        msg += ("\n" + line if msg else line)

if msg:
    await update.message.reply_text(msg)


–––––––– MAIN ––––––––

def main():
# تشغيل سيرفر الويب الوهمي في مسار جانبي لكي يرضى موقع Render
threading.Thread(target=run_health_server, daemon=True).start()

app = Application.builder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING 🚀")
app.run_polling(drop_pending_updates=True)


if name == “main”:
main()
