from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import requests
import re
import os
import difflib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = "8997212415:AAFd-Kdg_R1N6QDgPD1HR07jDB_WSjujHU"

# بحث Steam — category1=998 يعني "ألعاب فقط" (يستبعد DLC والموسيقى والفيديو والحزم)
STEAM_SEARCH = "https://store.steampowered.com/search/results/?term={q}&category1=998&cc=us&l=english"

# ---- خدعة Render: سيرفر ويب وهمي لجعل المنصة المجانية تعمل ----
class HealthCheckServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is Alive!")
    def log_message(self, *args):
        pass  # كتم سجلات السيرفر الوهمي

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), HealthCheckServer).serve_forever()

# ---------------- أدوات مساعدة ----------------
def cover_url(appid):
    # هوست akamai أوثق من cloudflare للغلاف العمودي 600x900
    return f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"

def image_exists(url):
    """يرجّع True فقط لو الصورة موجودة فعلاً (HTTP 200) — يمنع الروابط الميتة."""
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"},
                         timeout=8, stream=True)
        ok = (r.status_code == 200 and
              "image" in r.headers.get("Content-Type", ""))
        r.close()
        return ok
    except Exception:
        return False

def clean(s):
    s = re.sub(r"<.*?>", "", s)              # شيل أي HTML
    s = re.sub(r"[™®©:\-–—!]", " ", s)        # شيل رموز وعلامات
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()

def similarity(a, b):
    return difflib.SequenceMatcher(None, clean(a), clean(b)).ratio()

# ---------------- البحث في Steam ----------------
def get_steam(game):
    try:
        r = requests.get(
            STEAM_SEARCH.format(q=requests.utils.quote(game)),
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=12,
        )
        # كل نتيجة فيها رقم اللعبة + عنوانها — نسحبهم سوا عشان نطابق بالاسم
        rows = re.findall(
            r'data-ds-appid="(\d+)"[^>]*>.*?<span class="title">(.*?)</span>',
            r.text, re.S
        )
        if not rows:
            return None, None, 0.0

        # رتّب المرشحين حسب قرب الاسم من اللي طلبته (الأعلى تطابقاً أولاً)
        ranked = sorted(rows, key=lambda x: similarity(game, x[1]), reverse=True)

        # امشِ على أفضل 6 مطابقات، ورجّع أول وحدة صورتها موجودة فعلاً
        for appid, title in ranked[:6]:
            score = similarity(game, title)
            if score < 0.45:        # تطابق ضعيف جداً = لا تخمّن
                break
            url = cover_url(appid)
            if image_exists(url):
                return url, clean(title), score
        return None, None, 0.0
    except Exception as e:
        print("STEAM ERROR:", e)
        return None, None, 0.0

# ---------------- معالج الرسائل ----------------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    games = [g.strip() for g in re.split(r"\n|,", text) if g.strip()][:100]

    if not games:
        await update.message.reply_text("ارسل أسماء ألعاب (اسم في كل سطر)")
        return

    results = []
    for game in games:
        url, matched, score = get_steam(game)
        if url:
            flag = "  ⚠️تأكد" if score < 0.7 else ""   # تطابق متوسط = راجعه بعينك
            results.append(f"{game} | {url}{flag}")
        else:
            results.append(f"{game} | NOT FOUND")

    # أرسل النتائج على دفعات عشان حد طول رسالة تيليجرام
    msg = ""
    for line in results:
        if len(msg) + len(line) > 3500:
            await update.message.reply_text(msg)
            msg = line
        else:
            msg += ("\n" + line if msg else line)
    if msg:
        await update.message.reply_text(msg)

# ---------------- التشغيل ----------------
def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("BOT RUNNING 🚀")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
