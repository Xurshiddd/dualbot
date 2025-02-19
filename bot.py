import logging
import requests
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
)

# Bot tokeni
TOKEN = "8164954118:AAGMubXTB8fJeHKbvD-Qg9Q39201EQdUi4I"
API_URL = "https://request-test.xyz/api/getuser"
API_URL2 = "https://request-test.xyz/api/savedata"

# Logger sozlamalari
logging.basicConfig(level=logging.INFO)

# Tugmalar
phone_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True)]],
    resize_keyboard=True
)

main_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton("📤 Rasm yuborish")]],
    resize_keyboard=True
)

# /start komandasi
async def start_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if "phone_registered" in context.user_data:
        await update.message.reply_text("Siz allaqachon ro‘yxatdan o‘tganingiz!", reply_markup=main_keyboard)
    else:
        await update.message.reply_text("Salom! Iltimos, telefon raqamingizni yuboring.", reply_markup=phone_keyboard)

# Telefon raqamini qabul qilish
async def receive_contact(update: Update, context: CallbackContext):
    if "phone_registered" in context.user_data:
        return

    user_id = update.message.from_user.id
    phone_number = update.message.contact.phone_number

    data = {"phone": phone_number, "telegram_id": user_id}
    response = requests.post(API_URL, json=data)
    result = response.json()

    if result.get('status') == 'success':
        context.user_data["phone_registered"] = True
        await update.message.reply_text(result.get('message', 'Xatolik yuz berdi'), reply_markup=main_keyboard)
    else:
        await update.message.reply_text(result.get('message', 'Xatolik yuz berdi. Qayta urining!'))

# Rasm yuborish tugmasi bosilganda
async def ask_for_photo(update: Update, context: CallbackContext):
    await update.message.reply_text("📷 Iltimos, rasm yuboring.")

# Rasm qabul qilish va file_id saqlash
async def receive_photo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]  # Eng katta o'lchamli rasmni olish
    file_id = photo.file_id  # Telegram file_id

    context.user_data["file_id"] = file_id  # Saqlash

    keyboard = [[InlineKeyboardButton("📍 Geolokatsiyani yuborish", callback_data="send_location")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Endi geolokatsiyangizni yuboring.", reply_markup=reply_markup)

# Geolokatsiya tugmasi bosilganda
async def send_location_request(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📍 Iltimos, geolokatsiyangizni yuboring.", reply_markup=ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Geolokatsiyani yuborish", request_location=True)]], resize_keyboard=True
    ))

# Geolokatsiyani qabul qilish va API'ga yuborish
async def receive_location(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    lat = update.message.location.latitude
    lon = update.message.location.longitude

    file_id = context.user_data.get("file_id")
    if not file_id:
        await update.message.reply_text("❌ Xatolik! Rasm avval yuborilishi kerak.")
        return

    data = {
        "telegram_id": user_id,
        "file_id": file_id,  # Telegram file_id JSON ichida
        "latitude": lat,
        "longitude": lon
    }

    response = requests.post(API_URL2, json=data)
    result = response.json()

    await update.message.reply_text(f"📩 Natija:\nStatus: {result.get('status')}\nXabar: {result.get('message')}")
    await update.message.reply_text("📤 Keyingi amaliyot kunigacha xayr!!!", reply_markup=main_keyboard)

# Botni ishga tushirish
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start_command))
app.add_handler(MessageHandler(filters.CONTACT, receive_contact))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("📤 Rasm yuborish"), ask_for_photo))
app.add_handler(MessageHandler(filters.PHOTO, receive_photo))
app.add_handler(CallbackQueryHandler(send_location_request, pattern="send_location"))
app.add_handler(MessageHandler(filters.LOCATION, receive_location))

app.run_polling()
