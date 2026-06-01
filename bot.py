import logging
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, KeyboardButton)
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                           MessageHandler, filters, ContextTypes)
from config import *
from database import *

logging.basicConfig(level=logging.INFO)

# ═══════════════════════════════════════
#         KANAL TEKSHIRISH
# ═══════════════════════════════════════
async def kanal_tekshir(bot, user_id):
    if user_id == ADMIN_ID:
        return True
    for kanal in KANALLAR:
        try:
            member = await bot.get_chat_member(kanal["username"], user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ═══════════════════════════════════════
#         MENYULAR
# ═══════════════════════════════════════
def user_menyu():
    return ReplyKeyboardMarkup([
        ["🚀 Konkursda qatnashish"],
        ["🎁 Sovgalar", "👤 Ballarim"],
        ["📊 Reyting", "💡 Shartlar"],
    ], resize_keyboard=True)

def admin_menyu():
    return ReplyKeyboardMarkup([
        ["📊 Statistika", "👥 Ishtirokchilar"],
        ["🏆 Goliblar", "📢 Xabar yuborish"],
        ["🚀 Konkursda qatnashish"],
        ["🎁 Sovgalar", "👤 Ballarim"],
        ["📊 Reyting", "💡 Shartlar"],
    ], resize_keyboard=True)

def get_menyu(uid):
    return admin_menyu() if uid == ADMIN_ID else user_menyu()

# ═══════════════════════════════════════
#         /START
# ═══════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id
    args = context.args

    referrer_id = 0
    if args:
        try:
            referrer_id = int(args[0])
        except:
            pass

    yangi = user_qoshish(uid, user.username, user.first_name, referrer_id)

    if yangi and referrer_id and referrer_id != uid:
        if user_olish(referrer_id):
            if referral_qoshish(referrer_id, uid):
                ball_qoshish(referrer_id, REFERRAL_BALL)
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 {user.first_name} sizning havolangiz orqali qoshildi!\n"
                             f"✅ Sizga +{REFERRAL_BALL} ball qoshildi!"
                    )
                except:
                    pass

    obunachi = await kanal_tekshir(context.bot, uid)

    if not obunachi:
        btns = [[InlineKeyboardButton(f"➕ {k['nomi']}", url=k["url"])] for k in KANALLAR]
        btns.append([InlineKeyboardButton("✅ Azo boldim", callback_data="tekshir")])
        await update.message.reply_text(
            "🚀 Ishtirok etish uchun kanallarga azo buling:\n\n"
            "Azolashdan so'ng pastdagi tugmani bosing.",
            reply_markup=InlineKeyboardMarkup(btns)
        )
        return

    db_user = user_olish(uid)

    if not db_user[4]:
        await update.message.reply_text(
            f"Xush kelibsiz, {user.first_name}!\n\n"
            "Telefon raqamingizni yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📱 Raqamni yuborish", request_contact=True)]],
                resize_keyboard=True, one_time_keyboard=True
            )
        )
        return

    await update.message.reply_text(
        f"👑 Salom, {user.first_name}!\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"🏆 KONKURS BOTIGA XO'SH KELIBSIZ!\n\n"
        f"Konkurs: {KONKURS_KUN} kun\n"
        f"Goliblar: TOP {GOLIB_SONI}\n"
        f"Sizda: {db_user[5]} ball\n\n"
        f"Quyidan bolim tanlang:",
        reply_markup=get_menyu(uid)
    )

# ═══════════════════════════════════════
#         AZOLIK TEKSHIRISH
# ═══════════════════════════════════════
async def tekshir_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    user = query.from_user

    obunachi = await kanal_tekshir(context.bot, uid)
    if not obunachi:
        await query.answer("Hali barcha kanallarga azo bolmadingiz!", show_alert=True)
        return

    db_user = user_olish(uid)

    if not db_user[4]:
        await query.message.reply_text(
            "✅ Zo'r! Barcha kanallarga azo boldingiz!\n\n"
            "Telefon raqamingizni yuboring:",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📱 Raqamni yuborish", request_contact=True)]],
                resize_keyboard=True, one_time_keyboard=True
            )
        )
        return

    await query.message.reply_text(
        f"✅ Xush kelibsiz!\nSizda: {db_user[5]} ball",
        reply_markup=get_menyu(uid)
    )

# ═══════════════════════════════════════
#         TELEFON RAQAM
# ═══════════════════════════════════════
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    phone = update.message.contact.phone_number
    phone_saqlash(uid, phone)
    db_user = user_olish(uid)

    await update.message.reply_text(
        f"🎉 Tabriklaymiz!\n\n"
        f"Royxatdan o'tdingiz va {BOSHLANGICH_BALL} ball oldingiz!\n\n"
        f"Sizning ballingiz: {db_user[5]}\n\n"
        f"Quyidan bolim tanlang:",
        reply_markup=get_menyu(uid)
    )

# ═══════════════════════════════════════
#         KONKURSDA QATNASHISH
# ═══════════════════════════════════════
async def konkursda_qatnashish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    db_user = user_olish(uid)
    if not db_user:
        await start(update, context)
        return

    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={uid}"
    ref_soni = referral_soni(uid)

    await update.message.reply_text(
        f"🚀 KONKURSDA QATNASHISH\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"Havolangiz:\n{ref_link}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"Taklif qilganlar: {ref_soni} kishi\n"
        f"Sizning ballingiz: {db_user[5]}\n"
        f"Har bir do'st uchun: +{REFERRAL_BALL} ball\n\n"
        f"Havolani do'stlaringizga ulashing!",
        reply_markup=get_menyu(uid)
    )

# ═══════════════════════════════════════
#         BALLARIM
# ═══════════════════════════════════════
async def ballarim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    db_user = user_olish(uid)
    if not db_user:
        await start(update, context)
        return

    ref_soni = referral_soni(uid)
    top = top_users(50)
    pozitsiya = next((i+1 for i, u in enumerate(top) if u[0] == uid), "?")

    await update.message.reply_text(
        f"👤 SIZNING MALUMOTLARINGIZ\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"Pozitsiya: #{pozitsiya}\n"
        f"Ball: {db_user[5]}\n"
        f"Taklif qilganlar: {ref_soni} kishi\n"
        f"Telefon: {db_user[4] or 'Kiritilmagan'}\n\n"
        f"Har bir do'st: +{REFERRAL_BALL} ball"
    )

# ═══════════════════════════════════════
#         REYTING
# ═══════════════════════════════════════
async def reyting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = top_users(10)
    if not top:
        await update.message.reply_text("Hozircha ishtirokchilar yoq.")
        return

    medals = ["🥇","🥈","🥉","4.","5.","6.","7.","8.","9.","10."]
    text = "🏆 TOP 10 ISHTIROKCHILAR\n━━━━━━━━━━━━━━\n\n"
    for i, u in enumerate(top):
        name = u[2] or u[1] or "Anonim"
        un = f"@{u[1]}" if u[1] else ""
        text += f"{medals[i]} {name} {un} — {u[3]} ball\n"

    await update.message.reply_text(text)

# ═══════════════════════════════════════
#         SOVGALAR
# ═══════════════════════════════════════
async def sovgalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🎁 SOVGALAR\n━━━━━━━━━━━━━━\n\n"
        f"TOP {GOLIB_SONI} ishtirokchi sovga oladi!\n\n"
        f"🥇 1-orin — Maxsus sovga\n"
        f"🥈 2-orin — Maxsus sovga\n"
        f"🥉 3-orin — Maxsus sovga\n\n"
        f"Konkurs davomiyligi: {KONKURS_KUN} kun\n\n"
        f"Ko'proq do'st taklif qiling!"
    )

# ═══════════════════════════════════════
#         SHARTLAR
# ═══════════════════════════════════════
async def shartlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💡 KONKURS SHARTLARI\n━━━━━━━━━━━━━━\n\n"
        f"1. Barcha kanallarga azo buling\n"
        f"2. Telefon raqamni tasdiqlang\n"
        f"3. Havolani do'stlarga ulashing\n"
        f"4. Har bir do'st uchun +{REFERRAL_BALL} ball\n\n"
        f"Konkurs: {KONKURS_KUN} kun\n"
        f"Goliblar: TOP {GOLIB_SONI}\n\n"
        f"Nakrutka va multi akkaunt taqiqlangan!\n\n"
        f"Savollar: {ADMIN_USERNAME}"
    )

# ═══════════════════════════════════════
#         ADMIN — STATISTIKA
# ═══════════════════════════════════════
async def statistika(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    jami = jami_users()
    top = top_users(3)
    medals = ["🥇","🥈","🥉"]
    text = f"📊 STATISTIKA\n━━━━━━━━━━━━━━\n\nJami: {jami} kishi\n\nTOP 3:\n"
    for i, u in enumerate(top):
        name = u[2] or u[1] or "Anonim"
        text += f"{medals[i]} {name} — {u[3]} ball\n"
    await update.message.reply_text(text)

# ═══════════════════════════════════════
#         ADMIN — ISHTIROKCHILAR
# ═══════════════════════════════════════
async def ishtirokchilar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    users = barcha_users()
    if not users:
        await update.message.reply_text("Hozircha ishtirokchilar yoq.")
        return
    text = f"👥 ISHTIROKCHILAR ({len(users)} kishi)\n━━━━━━━━━━━━━━\n\n"
    for i, u in enumerate(users[:30], 1):
        name = u[2] or "Anonim"
        un = f"@{u[1]}" if u[1] else ""
        text += f"{i}. {name} {un} — {u[3]} ball\n"
    if len(users) > 30:
        text += f"\n+{len(users)-30} kishi yana..."
    await update.message.reply_text(text)

# ═══════════════════════════════════════
#         ADMIN — GOLIBLAR
# ═══════════════════════════════════════
async def goliblar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    top = top_users(GOLIB_SONI)
    medals = ["🥇","🥈","🥉"]
    text = f"🏆 GOLIBLAR — TOP {GOLIB_SONI}\n━━━━━━━━━━━━━━\n\n"
    for i, u in enumerate(top):
        name = u[2] or u[1] or "Anonim"
        un = f"@{u[1]}" if u[1] else f"ID:{u[0]}"
        m = medals[i] if i < 3 else f"{i+1}."
        text += f"{m} {name} ({un})\nBall: {u[3]}\n\n"
    await update.message.reply_text(text)

# ═══════════════════════════════════════
#         ADMIN — BROADCAST
# ═══════════════════════════════════════
broadcast_mode = {}

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    broadcast_mode[ADMIN_ID] = True
    await update.message.reply_text(
        "📢 Xabar yozing — barcha ishtirokchilarga yuboriladi.\n"
        "Bekor qilish: /cancel"
    )

async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    broadcast_mode[ADMIN_ID] = False
    users = barcha_users()
    text = update.message.text
    ok = 0
    xato = 0
    await update.message.reply_text(f"Yuborilmoqda {len(users)} ta foydalanuvchiga...")
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=text)
            ok += 1
        except:
            xato += 1
    await update.message.reply_text(f"✅ Yuborildi!\nMuvaffaqiyatli: {ok}\nXato: {xato}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    broadcast_mode[ADMIN_ID] = False
    await update.message.reply_text("Bekor qilindi.", reply_markup=get_menyu(update.message.from_user.id))

# ═══════════════════════════════════════
#         XABAR HANDLER
# ═══════════════════════════════════════
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text

    if broadcast_mode.get(uid) and uid == ADMIN_ID:
        await broadcast_send(update, context)
        return

    handlers = {
        "🚀 Konkursda qatnashish": konkursda_qatnashish,
        "👤 Ballarim": ballarim,
        "📊 Reyting": reyting,
        "🎁 Sovgalar": sovgalar,
        "💡 Shartlar": shartlar,
    }

    admin_handlers = {
        "📊 Statistika": statistika,
        "👥 Ishtirokchilar": ishtirokchilar,
        "🏆 Goliblar": goliblar,
        "📢 Xabar yuborish": broadcast_start,
    }

    if text in handlers:
        await handlers[text](update, context)
    elif text in admin_handlers and uid == ADMIN_ID:
        await admin_handlers[text](update, context)

# ═══════════════════════════════════════
#         MAIN
# ═══════════════════════════════════════
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(tekshir_callback, pattern="^tekshir$"))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("✅ Konkurs Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
