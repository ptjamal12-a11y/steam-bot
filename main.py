import os
import re
import difflib
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = "8997212415:AAFd-Kdg_R1N6QDgPD1HR07jDB_WSjujHU"

# بحث Steam — category1=998 يعني "ألعاب فقط" (يستبعد DLC والموسيقى والفيديو)
STEAM_SEARCH = "https://store.steampowered.com/search/results/?term={q}&category1=998&cc=us&l=english"
HEADERS = {"User-Agent": "Mozilla/5.0"}


# ---- سيرفر ويب وهمي حتى ترضى منصة Render ----
class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Alive!")

    def log_message(self, *args):
        pass


def run_health():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Health).serve_forever()


# ---- أدوات مساعدة ----
def cover_url(appid):
    # هوست akamai أوثق من cloudflare للغلاف العمودي
    return f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"


def image_exists(url):
    """True فقط لو الصورة موجودة فعلاً — يمنع الروابط الميتة (404)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, stream=True)
        ok = r.status_code == 200 and "image" in r.headers.get("Content-Type", "")
        r.close()
        return ok
    except Exception:
        return False


def norm(s):
    s = re.sub(r"<.*?>", "", s)
    s = re.sub(r"[™®©:\-–—!,.']", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def similarity(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


# ---- البحث في Steam ----
def get_steam(game):
    try:
        r = requests.get(STEAM_SEARCH.format(q=requests.utils.quote(game)),
                         headers=HEADERS, timeout=12)
        # نسحب رقم اللعبة + اسمها سوا عشان نطابق بالاسم مو بالموقع
        rows = re.findall(
            r'data-ds-appid="(\d+)"[^>]*>.*?<span class="title">(.*?)</span>',
            r.text, re.S)
        if not rows:
            return None, 0.0

        # رتّب حسب قرب الاسم من المطلوب (الأعلى أولاً)
        rows.sort(key=lambda x: similarity(game, x[1]), reverse=True)

        # أفضل 6 مرشحين: رجّع أول وحدة صورتها موجودة فعلاً
        for appid, title in rows[:6]:
            score = similarity(game, title)
            if score < 0.45:        # تطابق ضعيف = لا تخمّن
                break
            url = cover_url(appid)
            if image_exists(url):
                return url, score
        return None, 0.0
    except Exception as e:
        print("STEAM ERROR:", e)
        return None, 0.0


# ---- معالج الرسائل ----
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    games = [g.strip() for g in re.split(r"[\n,]", update.message.text) if g.strip()][:100]
    if not games:
        await update.message.reply_text("ارسل أسماء ألعاب (اسم في كل سطر)")
        return

    lines = []
    for game in games:
        url, score = get_steam(game)
        if url:
            flag = "  ⚠️تأكد" if score < 0.7 else ""
            lines.append(f"{game} | {url}{flag}")
        else:
            lines.append(f"{game} | NOT FOUND")

    msg = ""
    for line in lines:
        if len(msg) + len(line) > 3500:
            await update.message.reply_text(msg)
            msg = line
        else:
            msg += ("\n" + line if msg else line)
    if msg:
        await update.message.reply_text(msg)


def main():
    threading.Thread(target=run_health, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("BOT RUNNING 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
