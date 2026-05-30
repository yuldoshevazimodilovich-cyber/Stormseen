#Azim Akaga smm bot!
import logging
import sqlite3
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

BOT_TOKEN      = "8661186608:AAHYdVwpUMkgnbpJ7CMHtSbOeFvLJ9LBGTg"  
ADMIN_ID       = 8792279190
DB_PATH        = "bot.db"
REFERRAL_BONUS = 100

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)


STARS_PACKAGES = [
    ("s100", "💫 100 Stars", 30000),
    ("s150", "💫 150 Stars", 42000),
    ("s250", "💫 250 Stars", 78000),
    ("s350", "💫 350 Stars", 95000),
    ("s500", "💫 500 Stars", 132000),
    ("s1000", "💫 1000 Stars", 268000),
    ("s1500", "💫 1500 Stars", 420000),
    ("s2500", "💫 2500 Stars", 665000),
    ("s5000", "💫 5000 Stars", 1285000),
    ("s10000", "💫 10000 Stars", 2570000)
]
PREMIUM_PACKAGES = [
    ("p1", "⭐️ 1 Oylik - 40,000 so'm", 40000), 
    ("p3", "⭐️ 3 Oylik - 190,000 so'm", 190000), 
    ("p12", "⭐️ 12 Oylik - 470,000 so'm", 470000),
    ("p12_acc", "⭐️ 12 Oylik (Akkauntga kirib) - 310,000 so'm", 310000)
]
GIFTS_PACKAGES = [("g1", "🎁 Mini Gift", 50000), ("g2", "🎁 Standard Gift", 100000)]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        username TEXT, 
        full_name TEXT,
        balance REAL DEFAULT 0.0, 
        referred_by INTEGER DEFAULT NULL)""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER, 
        file_id TEXT, 
        amount REAL DEFAULT 0, 
        status TEXT DEFAULT 'pending')""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER, 
        product TEXT, 
        price REAL, 
        status TEXT DEFAULT 'pending')""")
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row[0] if row else 0.0

def update_user_balance(user_id, amount):
    with sqlite3.connect(DB_PATH, timeout=30) as conn:
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id=?",
            (amount, user_id)
        )
        conn.commit()

def main_kb():
    kb = [
        [KeyboardButton("💼 Xizmatlar"), KeyboardButton("☎️ Qo'llab-quvvatlash")],
        [KeyboardButton("💳 Pul kiritish"), KeyboardButton("👤 Hisobim")],
        [KeyboardButton("👥 Referal")]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    ref_id = None

    with sqlite3.connect(DB_PATH, timeout=30) as conn:

        curr = conn.execute(
            "SELECT user_id FROM users WHERE user_id=?",
            (u.id,)
        ).fetchone()

        if not curr:

            if ctx.args and ctx.args[0].startswith("ref"):
                try:
                    rid = int(ctx.args[0].replace("ref", ""))
                    if rid != u.id:
                        ref_id = rid
                except:
                    pass

            conn.execute(
                "INSERT INTO users (user_id, username, full_name, referred_by) VALUES (?,?,?,?)",
                (u.id, u.username, u.full_name, ref_id)
            )

            conn.commit()

    if ref_id:
        update_user_balance(ref_id, REFERRAL_BONUS)

        try:
            await ctx.bot.send_message(
                ref_id,
                f"🎁 <b>Yangi referal!</b>\nHisobingizga {REFERRAL_BONUS} so'm qo'shildi.",
                parse_mode="HTML"
            )
        except:
            pass

    await update.message.reply_text(
        f"Assalomu alaykum, {u.full_name}!",
        reply_markup=main_kb()
    )

async def admin_add_money(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        t_id, amt = int(ctx.args[0]), float(ctx.args[1])
        update_user_balance(t_id, amt)
        await update.message.reply_text(f"✅ ID {t_id} balansiga {amt:,.0f} so'm qo'shildi.")
        await ctx.bot.send_message(t_id, f"💰 Balansingiz {amt:,.0f} so'mga to'ldirildi!")
    except: await update.message.reply_text("Xato! Format: /addmoney ID SUMMA")

async def cmd_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    text = update.message.text

    if u.id == ADMIN_ID and ctx.user_data.get("approving"):
        info = ctx.user_data.pop("approving")
        try:
            amount = float(text.replace(" ", ""))
            update_user_balance(info['uid'], amount)
            await update.message.reply_text(f"✅ Tasdiqlandi.")
            await ctx.bot.send_message(info['uid'], f"✅ Balansingiz {amount:,.0f} so'mga to'ldirildi!")
        except: await update.message.reply_text("Iltimos, faqat son yozing.")
        return

    if text == "💼 Xizmatlar":
        skb = [[KeyboardButton("⭐️ Premium"), KeyboardButton("🌟 Stars")], [KeyboardButton("🎁 Gifts")], [KeyboardButton("🔙 Orqaga")]]
        await update.message.reply_text("Xizmat turini tanlang:", reply_markup=ReplyKeyboardMarkup(skb, resize_keyboard=True))
    
    elif text == "🌟 Stars":
        btns = [[InlineKeyboardButton(f"{l} - {p:,} so'm", callback_data=f"buy|stars|{k}|{p}")] for k,l,p in STARS_PACKAGES]
        await update.message.reply_text("🌟 Telegram Stars paketlari:", reply_markup=InlineKeyboardMarkup(btns))

    elif text == "⭐️ Premium":
        btns = [[InlineKeyboardButton(f"{l} - {p:,} so'm", callback_data=f"buy|prem|{k}|{p}")] for k,l,p in PREMIUM_PACKAGES]
        await update.message.reply_text("⭐️ Telegram Premium paketlari:", reply_markup=InlineKeyboardMarkup(btns))

    elif text == "🎁 Gifts":
        btns = [[InlineKeyboardButton(f"{l} - {p:,} so'm", callback_data=f"buy|gift|{k}|{p}")] for k,l,p in GIFTS_PACKAGES]
        await update.message.reply_text("🎁 Telegram Gifts paketlari:", reply_markup=InlineKeyboardMarkup(btns))

    elif text == "💳 Pul kiritish":
        ctx.user_data["waiting_pay"] = True
        msg = "<b>💸 Karta:</b> <code>9860040116891538</code>\n<b>Fazilov.O</b>\n\nTo'lov qilgach, chekni (rasm) yuboring."
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Bekor qilish")]], resize_keyboard=True))

    elif text == "👤 Hisobim":
        bal = get_balance(u.id)
        role = "💎 VIP (Admin)" if u.id == ADMIN_ID else "Foydalanuvchi"
        await update.message.reply_text(f"<b>👤 Hisobim:</b>\n🆔 ID: <code>{u.id}</code>\n💰 Balans: {bal:,.0f} so'm\n✨ Daraja: {role}", parse_mode="HTML")

    elif text == "☎️ Qo'llab-quvvatlash":
        support_text = (
            "<b>☎️ Qo'llab-quvvatlash</b>\n\n"
            "🔉 Bot yangiliklari: @Storm_seen\n"
            "👤 Qo'llab-quvvatlash: @ST_rrsa\n\n"
            "⚠️ <b>Diqqat!</b> Barcha to'lovlar xavfsiz. "
            "Bot hisobidagi pulni qaytarish imkoni yo'q!"
        )
        await update.message.reply_text(support_text, parse_mode="HTML")

    elif text == "👥 Referal":
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (u.id,)).fetchone()[0]
        conn.close()
        bot = await ctx.bot.get_me()
        link = f"https://t.me/{bot.username}?start=ref{u.id}"
        msg = (
            f"<b>👥 Referal tizimi</b>\n\n"
            f"Do'stlaringizni taklif qiling va har biri uchun <b>{REFERRAL_BONUS} so'm</b> oling!\n\n"
            f"📊 Takliflaringiz: {count} ta\n"
            f"🔗 Havolangiz:\n<code>{link}</code>"
        )
        await update.message.reply_text(msg, parse_mode="HTML")

    elif text in ["🔙 Orqaga", "❌ Bekor qilish"]:
        ctx.user_data.pop("waiting_pay", None)
        await update.message.reply_text("Asosiy menyu:", reply_markup=main_kb())

async def cmd_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not ctx.user_data.get("waiting_pay"): return
    file_id = update.message.photo[-1].file_id
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("INSERT INTO payments (user_id, file_id) VALUES (?,?)", (u.id, file_id))
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    ctx.user_data.pop("waiting_pay", None)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"app|{pid}|{u.id}")]])
    await ctx.bot.send_photo(ADMIN_ID, photo=file_id, caption=f"💳 To'lov #{pid}\nID: {u.id}\nUser: @{u.username}", reply_markup=kb)
    await update.message.reply_text("✅ Chek adminlarga yuborildi. Tez orada tasdiqlanadi.")

async def cmd_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    u_id = query.from_user.id

    if data[0] == "app":
        ctx.user_data["approving"] = {"pid": int(data[1]), "uid": int(data[2])}
        await query.message.reply_text(f"To'lov miqdorini yozing (ID: {data[2]} uchun):")
    elif data[0] == "buy":
        item, price = data[2], int(data[3])
        bal = get_balance(u_id)
        if u_id == ADMIN_ID or bal >= price:
            if u_id != ADMIN_ID: update_user_balance(u_id, -price)
            await query.message.edit_text(f"✅ Xarid bajarildi: {item}\nAdminlar tez orada yetkazib berishadi.")
            await ctx.bot.send_message(ADMIN_ID, f"🛒 YANGI BUYURTMA!\nMahsulot: {item}\nUser: {u_id} (@{query.from_user.username})")
        else:
            await query.message.reply_text("❌ Mablag' yetarli emas. Iltimos, hisobingizni to'ldiring.")

def main():
    init_db() 
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("addmoney", admin_add_money))
    app.add_handler(CallbackQueryHandler(cmd_callback))
    app.add_handler(MessageHandler(filters.PHOTO, cmd_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cmd_text))
    app.run_polling()

if __name__ == "__main__":
    main()