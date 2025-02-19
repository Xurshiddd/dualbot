import logging
import requests
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
)

# 🔑 Telegram bot tokeni
TOKEN = "8164954118:AAGMubXTB8fJeHKbvD-Qg9Q39201EQdUi4I"
API_URL = "https://request-test.xyz/api/getuser"
API_URL2 = "https://request-test.xyz/api/savedata"

# 🔹 Logger sozlamalari
logging.basicConfig(level=logging.INFO)

# 📲 Telefon raqamini yuborish tugmasi
phone_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True)]],
    resize_keyboard=True
)

# 📤 Asosiy menyu tugmalari
main_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("📤 Rasm yuborish")]],
    resize_keyboard=True
)

# 🚀 /start komandasi
async def start_command(update: Update, context: CallbackContext):
    await update.message.reply_text("👋 Salom! Iltimos, telefon raqamingizni yuboring.", reply_markup=phone_keyboard)

# 📞 Telefon raqamini qabul qilish
async def receive_contact(update: Update, context: CallbackContext):
    user = update.message.from_user
    contact = update.message.contact

    # 🔴 Faqat foydalanuvchining o‘z raqamini qabul qilish
    if user.id != contact.user_id:
        await update.message.reply_text("❌ Siz faqat o‘z telefon raqamingizni yubora olasiz!")
        return

    phone_number = contact.phone_number
    data = {"phone": phone_number, "telegram_id": user.id}

    response = requests.post(API_URL, json=data)
    result = response.json()

    if result.get('status') == 'success':
        context.user_data["phone_registered"] = True
        await update.message.reply_text(result.get('message', '✅ Telefon raqamingiz qabul qilindi!'), reply_markup=main_keyboard)
    else:
        await update.message.reply_text(result.get('message', '❌ Xatolik yuz berdi. Qayta urinib ko‘ring!'))

# 📷 Rasm yuborish tugmasi bosilganda
async def ask_for_photo(update: Update, context: CallbackContext):
    await update.message.reply_text("📷 Iltimos, rasm yuboring.")

# 🖼 Rasm qabul qilish va file_id saqlash
async def receive_photo(update: Update, context: CallbackContext):
    photo = update.message.photo[-1]  # Eng katta o'lchamli rasmni olish
    file_id = photo.file_id  # Telegram file_id

    context.user_data["file_id"] = file_id  # Saqlash

    keyboard = [[InlineKeyboardButton("📍 Geolokatsiyani yuborish", callback_data="send_location")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("📍 Endi geolokatsiyangizni yuboring.", reply_markup=reply_markup)

# 📍 Geolokatsiya tugmasi bosilganda
async def send_location_request(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📍 Iltimos, geolokatsiyangizni yuboring.", reply_markup=ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Geolokatsiyani yuborish", request_location=True)]], resize_keyboard=True
    ))

# 📍 Geolokatsiyani qabul qilish
async def receive_location(update: Update, context: CallbackContext):
    message = update.message or update.edited_message  
    if not message or not message.location:
        await update.effective_message.reply_text("❌ Lokatsiya topilmadi. Iltimos, yana urinib ko‘ring.")
        return

    location = message.location
    accuracy = getattr(location, "horizontal_accuracy", None)

    if accuracy is None:
        await message.reply_text("❌ Siz faqat real GPS-lokatsiyani yuborishingiz mumkin!")
        return

    lat = location.latitude
    lon = location.longitude

    if accuracy > 100:  
        await message.reply_text("❌ GPS signal sifati past! Iltimos, ochiq joyga chiqing va qayta urinib ko‘ring.")
        return

    file_id = context.user_data.get("file_id")
    if not file_id:
        await message.reply_text("❌ Xatolik! Avval rasm yuboring.")
        return

    data = {
        "telegram_id": message.from_user.id,
        "file_id": file_id,
        "latitude": lat,
        "longitude": lon
    }

    try:
        response = requests.post(API_URL2, json=data)
        result = response.json()
    except requests.exceptions.JSONDecodeError:
        await message.reply_text("❌ Server noto‘g‘ri javob qaytardi. Keyinroq qayta urinib ko‘ring.")
        return

    await message.reply_text(f"📩 Natija:\nStatus: {result.get('status')}\nXabar: {result.get('message')}")
    await message.reply_text("📤 Keyingi amaliyot kunigacha xayr!!!", reply_markup=main_keyboard)

# 🚀 Botni ishga tushirish
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start_command))
app.add_handler(MessageHandler(filters.CONTACT, receive_contact))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("📤 Rasm yuborish"), ask_for_photo))
app.add_handler(MessageHandler(filters.PHOTO, receive_photo))
app.add_handler(CallbackQueryHandler(send_location_request, pattern="send_location"))
app.add_handler(MessageHandler(filters.LOCATION, receive_location))

app.run_polling()
