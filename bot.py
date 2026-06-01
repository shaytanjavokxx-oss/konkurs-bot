import logging
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove)
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                           MessageHandler, filters, ContextTypes)
from config import *
from database import *

logging.basicConfig(level=logging.INFO)

# ═══════════════════════════════════════
#         KANAL TEKSHIRISH
# ═══════════════════════════════════════
async def kanal_tekshir(bot, user_id):
    for kanal in KANALLAR:
        try:
            member = await bot.get_chat_member(kanal["username"], user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ═══════════════════════════════════════
#         ASOSIY MENYU
# ═══════════════════════════════════════
def asosiy_menyu():
    keyboard = [
        ["🚀 Konkursda qatnashish"],
        ["🎁 Sovg'alar", "👤 Ballarim"],
        ["📊 Reyting", "💡 Shartlar"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_menyu():
    keyboard = [
        ["📊 Statistika", "👥 Ishtirokchilar"],
        ["🏆 G'oliblar", "📢 Xabar yuborish"],
        ["🚀 Konkursda qatnashish"],
        ["🎁 Sovg'alar", "👤 Ballarim"],
        ["📊 Reyting", "💡 Shartlar"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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

    # Referral ball berish
    if yangi and referrer_id and referrer_id != uid:
        ref_user = user_olish(referrer_id)
        if ref_user:
            if referral_qoshish(referrer_id, uid):
                ball_qoshish(referrer_id, REFERRAL_BALL)
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 *{user.first_name}* sizning havolangiz orqali ro'yxatdan o'tdi!\n"
                             f"✅ Sizga *+{REFERRAL_BALL} ball* qo'shildi! 🏆",
                        parse_mode="Markdown"
                    )
                except:
                    pass

    menu = admin_menyu() if uid == ADMIN_ID else asosiy_menyu()

    # Kanal obuna tekshirish
    obunachi = await kanal_tekshir(context.bot, uid)

    if not obunachi:
        keyboard = []
        for k in KANALLAR:
            keyboard.append([InlineKeyboardButton(f"➕ {k['nomi']}", url=k["url"])])
        keyboard.append([InlineKeyboardButton("✅ A'zo bo'ldim", callback_data="tekshir")])

        await update.message.reply_text(
            f"🚀 *Loyihada ishtirok etish uchun*\n"
            f"quyidagi kanallarga a'zo bo'ling:\n\n"
            f"⚠️ *Yopiq kanallarga ulanish so'rovini yuborishingiz kifoya.*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    db_user = user_olish(uid)

    # Telefon raqam so'rash
    if not db_user[4]:  # phone yo'q
        phone_btn = KeyboardButton("📱 Raqamni yuborish", request_contact=True)
        await update.message.reply_text(
            f"🎉 *Xush kelibsiz, {user.first_name}!*\n\n"
            f"Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[phone_btn]], resize_keyboard=True, one_time_keyboard=True)
        )
        return

    await update.message.reply_text(
        f"👑 *Salom, {user.first_name}!*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🏆 *KONKURS BOTIGA XO'SH KELIBSIZ!*\n\n"
        f"📅 Konkurs davomiyligi: *{KONKURS_KUN} kun*\n"
        f"🎯 G'oliblar soni: *TOP {GOLIB_SONI}*\n"
        f"⭐ Sizda: *{db_user[5]} ball*\n\n"
        f"👇 Quyidan bo'lim tanlang:",
        parse_mode="Markdown",
        reply_markup=menu
    )

# ═══════════════════════════════════════
#         OBUNA TEKSHIRISH CALLBACK
# ═══════════════════════════════════════
async def tekshir_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    user = query.from_user

    obunachi = await kanal_tekshir(context.bot, uid)

    if not obunachi:
        await query.answer("❌ Hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)
        return

    db_user = user_olish(uid)
    menu = admin_menyu() if uid == ADMIN_ID else asosiy_menyu()

    if not db_user[4]:
        phone_btn = KeyboardButton("📱 Raqamni yuborish", request_contact=True)
        await query.message.reply_text(
            f"✅ *Zo'r! Barcha kanallarga a'zo bo'ldingiz!*\n\n"
            f"Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[phone_btn]], resize_keyboard=True, one_time_keyboard=True)
        )
        return

    await query.message.reply_text(
        f"✅ *Tekshirildi! Xush kelibsiz!*\n\n"
        f"⭐ Sizda: *{db_user[5]} ball*",
        parse_mode="Markdown",
        reply_markup=menu
    )

# ═══════════════════════════════════════
#         TELEFON RAQAM
# ═══════════════════════════════════════
async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    phone = update.message.contact.phone_number
    phone_saqlash(uid, phone)

    menu = admin_menyu() if uid == ADMIN_ID else asosiy_menyu()
    db_user = user_olish(uid)

    await update.message.reply_text(
        f"🎉 *Tabriklaymiz!*\n\n"
        f"Siz loyihamizga to'liq ro'yxatdan o'tdingiz\n"
        f"va boshlang'ich *{BOSHLANGICH_BALL} ballga* ega bo'ldingiz! 🏆\n\n"
        f"📊 Sizning ballingiz: *{db_user[5]}*\n\n"
        f"👇 Quyidan bo'lim tanlang:",
        parse_mode="Markdown",
        reply_markup=menu
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

    ref_link = f"https://t.me/{context.bot.username}?start={uid}"
    ref_soni = referral_soni(uid)

    await update.message.reply_text(
        f"🚀 *KONKURSDA QATNASHISH*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📣 Quyidagi havolani do'stlaringizga ulashing:\n\n"
        f"`{ref_link}`\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 Taklif qilganlaringiz: *{ref_soni} kishi*\n"
        f"⭐ Sizning ballingiz: *{db_user[5]}*\n"
        f"🎯 Har bir do'stingiz uchun: *+{REFERRAL_BALL} ball*\n\n"
        f"💡 Havola orqali ro'yxatdan o'tgan har bir do'stingiz uchun avtomatik ball qo'shiladi!",
        parse_mode="Markdown"
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
        f"👤 *SIZNING MA'LUMOTLARINGIZ*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🏅 Pozitsiya: *#{pozitsiya}*\n"
        f"⭐ Ball: *{db_user[5]}*\n"
        f"👥 Taklif qilganlar: *{ref_soni} kishi*\n"
        f"📱 Telefon: *{db_user[4] or 'Kiritilmagan'}*\n\n"
        f"🎯 Har bir do'st: *+{REFERRAL_BALL} ball*",
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════
#         REYTING
# ═══════════════════════════════════════
async def reyting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = top_users(10)

    if not top:
        await update.message.reply_text("Hozircha ishtirokchilar yo'q.")
        return

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "🏆 *TOP 10 ISHTIROKCHILAR*\n━━━━━━━━━━━━━━━━━━\n\n"

    for i, u in enumerate(top):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        name = u[2] or u[1] or "Anonim"
        username = f"@{u[1]}" if u[1] else ""
        text += f"{medal} *{name}* {username}\n⭐ {u[3]} ball\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# ═══════════════════════════════════════
#         SOVG'ALAR
# ═══════════════════════════════════════
async def sovgalar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🎁 *SOVG'ALAR*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🏆 Konkurs yakunida eng ko'p ball yig'gan\n"
        f"*TOP {GOLIB_SONI}* ishtirokchi sovg'a oladi!\n\n"
        f"🥇 *1-o'rin* — Maxsus sovg'a\n"
        f"🥈 *2-o'rin* — Maxsus sovg'a\n"
        f"🥉 *3-o'rin* — Maxsus sovg'a\n\n"
        f"📅 Konkurs davomiyligi: *{KONKURS_KUN} kun*\n\n"
        f"💪 Ko'proq do'st taklif qiling va g'alaba qozoning!",
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════
#         SHARTLAR
# ═══════════════════════════════════════
async def shartlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💡 *KONKURS SHARTLARI*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"1️⃣ Barcha kanallarga a'zo bo'ling\n"
        f"2️⃣ Telefon raqamingizni tasdiqlang\n"
        f"3️⃣ Maxsus havolangizni do'stlaringizga ulashing\n"
        f"4️⃣ Har bir ro'yxatdan o'tgan do'stingiz uchun *+{REFERRAL_BALL} ball*\n\n"
        f"📅 Konkurs davomiyligi: *{KONKURS_KUN} kun*\n"
        f"🏆 G'oliblar soni: *TOP {GOLIB_SONI}*\n\n"
        f"⛔ *Taqiqlangan:*\n"
        f"• Nakrutka (bot orqali ball yig'ish)\n"
        f"• Multi akkauntdan foydalanish\n"
        f"• Spam tarqatish\n\n"
        f"✅ Isbot olinadi, halol bo'ling!\n\n"
        f"📞 Savollar: {ADMIN_USERNAME}",
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════
#         ADMIN — STATISTIKA
# ═══════════════════════════════════════
async def statistika(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    jami = jami_users()
    top = top_users(3)

    text = (
        f"📊 *STATISTIKA*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Jami ishtirokchilar: *{jami}*\n\n"
        f"🏆 *TOP 3:*\n"
    )

    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(top):
        name = u[2] or u[1] or "Anonim"
        text += f"{medals[i]} {name} — *{u[3]} ball*\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# ═══════════════════════════════════════
#         ADMIN — ISHTIROKCHILAR
# ═══════════════════════════════════════
async def ishtirokchilar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    users = barcha_users()
    if not users:
        await update.message.reply_text("Hozircha ishtirokchilar yo'q.")
        return

    text = f"👥 *ISHTIROKCHILAR ({len(users)} kishi):*\n━━━━━━━━━━━━━━━━━━\n\n"
    for i, u in enumerate(users[:30], 1):
        name = u[2] or "Anonim"
        username = f"@{u[1]}" if u[1] else ""
        text += f"{i}. *{name}* {username} — ⭐{u[3]}\n"

    if len(users) > 30:
        text += f"\n... va yana {len(users)-30} kishi"

    await update.message.reply_text(text, parse_mode="Markdown")

# ═══════════════════════════════════════
#         ADMIN — G'OLIBLAR
# ═══════════════════════════════════════
async def goliblar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    top = top_users(GOLIB_SONI)
    medals = ["🥇", "🥈", "🥉"]

    text = f"🏆 *G'OLIBLAR — TOP {GOLIB_SONI}*\n━━━━━━━━━━━━━━━━━━\n\n"
    for i, u in enumerate(top):
        name = u[2] or u[1] or "Anonim"
        username = f"@{u[1]}" if u[1] else f"ID: {u[0]}"
        medal = medals[i] if i < 3 else f"{i+1}."
        text += f"{medal} *{name}* ({username})\n⭐ Ball: *{u[3]}*\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# ═══════════════════════════════════════
#         ADMIN — BROADCAST
# ═══════════════════════════════════════
broadcast_mode = {}

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    broadcast_mode[ADMIN_ID] = True
    await update.message.reply_text(
        "📢 *Xabar yuborish rejimi*\n\n"
        "Barcha ishtirokchilarga yuboriladigan xabarni yozing:\n\n"
        "❌ Bekor qilish: /cancel",
        parse_mode="Markdown"
    )

async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if not broadcast_mode.get(ADMIN_ID):
        return

    broadcast_mode[ADMIN_ID] = False
    users = barcha_users()
    text = update.message.text
    yuborildi = 0
    xato = 0

    await update.message.reply_text(f"⏳ {len(users)} ta foydalanuvchiga yuborilmoqda...")

    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=text, parse_mode="Markdown")
            yuborildi += 1
        except:
            xato += 1

    await update.message.reply_text(
        f"✅ *Yuborildi!*\n\n"
        f"✔️ Muvaffaqiyatli: *{yuborildi}*\n"
        f"❌ Xato: *{xato}*",
        parse_mode="Markdown"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    broadcast_mode[ADMIN_ID] = False
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=admin_menyu())

# ═══════════════════════════════════════
#         XABAR HANDLER
# ═══════════════════════════════════════
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.message.from_user.id

    # Admin broadcast rejimi
    if broadcast_mode.get(uid) and uid == ADMIN_ID:
        await broadcast_send(update, context)
        return

    if text == "🚀 Konkursda qatnashish":
        await konkursda_qatnashish(update, context)
    elif text == "👤 Ballarim":
        await ballarim(update, context)
    elif text == "📊 Reyting":
        await reyting(update, context)
    elif text == "🎁 Sovg'alar":
        await sovgalar(update, context)
    elif text == "💡 Shartlar":
        await shartlar(update, context)
    elif text == "📊 Statistika" and uid == ADMIN_ID:
        await statistika(update, context)
    elif text == "👥 Ishtirokchilar" and uid == ADMIN_ID:
        await ishtirokchilar(update, context)
    elif text == "🏆 G'oliblar" and uid == ADMIN_ID:
        await goliblar(update, context)
    elif text == "📢 Xabar yuborish" and uid == ADMIN_ID:
        await broadcast_start(update, context)

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
