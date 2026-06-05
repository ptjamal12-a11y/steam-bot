import re
import difflib
import requests
import os
from aiohttp import web
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = "8997212415:AAFd-Kdg_R1N6QDgPD1HR07jDB_WSjujHU"
STEAM_SEARCH = "https://store.steampowered.com/search/results/?term={q}&category1=998&cc=us&l=english"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
gameback.com
# ⚠️ ضع رابط موقعك الفعلي الأزرق من Render هنا بدلاً من الرابط أدناه إذا كان مختلفاً
RENDER_EXTERNAL_URL = "https://your-bot-name.onrender.com"


def cover_url(appid):
    return f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"

def image_exists(url):
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
    return re.sub(r"\s+", " ", s).strip().lower()

def similarity(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()

def get_steam(game):
    try:
        r = requests.get(STEAM_SEARCH.format(q=requests.utils.quote(game)),
                         headers=HEADERS, timeout=12)
        rows = re.findall(
            r'data-ds-appid="(\d+)"[^>]*>.*?<span class="title">(.*?)</span>',
            r.text, re.S)
        if not rows:
            return None, 0.0
        rows.sort(key=lambda x: similarity(game, x[1]), reverse=True)
        for appid, title in rows[:6]:
            score = similarity(game, title)
            if score < 0.45:
                break
            url = cover_url(appid)
            if image_exists(url):
                return url, score
        return None, 0.0
    except Exception as e:
        print("STEAM ERROR:", e)
        return None, 0.0

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

# دالة للاستجابة لرابط الفحص الخاص بـ Render لمنع الإغلاق تلقائياً
async def html_index(request):
    return web.Response(text="Bot is alive!", content_type="text/plain")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    port = int(os.environ.get("PORT", 8080))
    
    # بناء سيرفر ويب متكامل يتعامل مع طلبات تليجرام وطلبات Render الفحصية معاً
    updater = app.updater
    if updater:
        # إعداد منفذ الويب للبوت
        webhook_app = web.Application()
        
        # 1. الرابط الرئيسي: لإرضاء سيرفر Render وجعله أخضر Live دائماً
        webhook_app.router.add_get("/", html_index)
        
        # 2. رابط التوكن المخصص لاستقبال رسائل تليجرام
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{TOKEN}",
            webhook_app=webhook_app
        )

if __name__ == "__main__":
    main()
