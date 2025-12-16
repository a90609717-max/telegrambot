# Telegram-бот «Карта Тривог»
# Творець: Артем Процко

import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "7733643731:AAFlN-E4RDBu4YTiaJpBmUXsbSLgKq1E6A0"  # ⚠️ ВСТАВ СВІЙ ТОКЕН
CREATOR = "Артем Процко"
MODERATOR_PASSWORD = "QazMlp123"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# ===== Тимчасове сховище (пізніше БД) =====
users = {}  # user_id: {"regions": [], "role": "user"}

# ===== Області України =====
REGIONS = [
    "Київська область", "Сумська область", "Харківська область", "Чернігівська область",
    "Полтавська область", "Дніпропетровська область", "Одеська область", "Львівська область"
]

# ===== Клавіатури =====
def regions_keyboard():
    kb = InlineKeyboardBuilder()
    for r in REGIONS:
        kb.button(text=r, callback_data=f"region:{r}")
    kb.adjust(2)
    return kb.as_markup()

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🗺 Моя область"), KeyboardButton(text="🚨 Статус тривоги")],
        [KeyboardButton(text="🔔 Налаштування"), KeyboardButton(text="🛡 Укриття поруч")],
        [KeyboardButton(text="👤 Мій профіль"), KeyboardButton(text="ℹ️ Про бота")]
    ],
    resize_keyboard=True
)

# ===== /start =====
@dp.message(CommandStart())
async def start(message: types.Message):
    users.setdefault(message.from_user.id, {"regions": [], "role": "user"})
    await message.answer(
        f"🇺🇦 <b>Карта Тривог України</b>\n\n"
        f"Отримуйте сповіщення про тривоги в реальному часі.\n"
        f"🔔 Оновлення кожні 4 хвилини\n\n"
        f"👤 Творець: {CREATOR}\n\n"
        f"⬇️ Оберіть область:",
        reply_markup=regions_keyboard()
    )

# ===== Вибір області =====
@dp.callback_query(lambda c: c.data.startswith("region:"))
async def choose_region(callback: types.CallbackQuery):
    region = callback.data.split(":", 1)[1]
    user = users[callback.from_user.id]

    if region not in user["regions"]:
        user["regions"].append(region)

    await callback.answer("Область додано")
    await callback.message.answer(
        f"✅ Ви обрали: <b>{', '.join(user['regions'])}</b>",
        reply_markup=main_menu
    )

# ===== Про бота =====
@dp.message(lambda m: m.text == "ℹ️ Про бота")
async def about(message: types.Message):
    await message.answer(
        "🇺🇦 <b>Карта Тривог</b>\n\n"
        "Бот для сповіщень про повітряні тривоги.\n"
        "Дані оновлюються кожні 4 хвилини.\n\n"
        f"👤 Творець: {CREATOR}"
    )

# ===== Профіль =====
@dp.message(lambda m: m.text == "👤 Мій профіль")
async def profile(message: types.Message):
    user = users.get(message.from_user.id)
    await message.answer(
        f"👤 <b>Ваш профіль</b>\n\n"
        f"ID: {message.from_user.id}\n"
        f"Статус: {user['role']}\n"
        f"Області: {', '.join(user['regions']) if user['regions'] else 'не обрано'}\n\n"
        "Для статусу модератора введіть пароль повідомленням."
    )

# ===== Пароль модератора =====
@dp.message(lambda m: m.text == MODERATOR_PASSWORD)
async def moderator_login(message: types.Message):
    users[message.from_user.id]["role"] = "moderator"
    await message.answer("✅ Ви отримали статус <b>МОДЕРАТОР</b>")

# ===== Статус тривоги (заглушка) =====
@dp.message(lambda m: m.text == "🚨 Статус тривоги")
async def alarm_status(message: types.Message):
    await message.answer("🟢 Наразі тривог немає (демо-режим)")

# ===== Фонове оновлення (заглушка) =====
async def background_updater():
    while True:
        # Тут буде запит до API тривог кожні 4 хвилини
        await asyncio.sleep(240)

# ===== Запуск =====
async def main():
    asyncio.create_task(background_updater())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
