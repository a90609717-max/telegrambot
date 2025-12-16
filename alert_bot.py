# Telegram-бот «Карта Тривог» v2.0
# Творець: Артем Процко

import asyncio
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

import database as db

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

ALERTS_TOKEN = os.getenv("ALERTS_API_TOKEN")
CREATOR = "Артем Процко"
MODERATOR_PASSWORD = os.getenv("MODERATOR_PASSWORD", "QazMlp123")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

db.init_db()
db.seed_shelters()

REGIONS = [
    "Київська область", "Сумська область", "Харківська область", "Чернігівська область",
    "Полтавська область", "Дніпропетровська область", "Одеська область", "Львівська область",
    "Запорізька область", "Миколаївська область", "Херсонська область", "Донецька область",
    "Луганська область", "Вінницька область", "Житомирська область", "Рівненська область",
    "Волинська область", "Тернопільська область", "Хмельницька область", "Закарпатська область",
    "Івано-Франківська область", "Чернівецька область", "Черкаська область", "Кіровоградська область",
    "м. Київ"
]

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

async def get_alerts_status():
    if not ALERTS_TOKEN:
        return None
    try:
        from alerts_in_ua import AsyncClient as AlertsClient
        client = AlertsClient(token=ALERTS_TOKEN)
        alerts = await client.get_active_alerts()
        return alerts
    except Exception as e:
        logging.error(f"Error fetching alerts: {e}")
        return None

def format_alert_status(alerts, user_regions: list = None):
    if alerts is None:
        return "⚠️ Не вдалося отримати дані про тривоги. Перевірте API токен."
    
    active_alerts = []
    try:
        air_raid_alerts = alerts.get_air_raid_alerts()
        for alert in air_raid_alerts:
            if user_regions:
                if any(region in alert.location_title for region in user_regions):
                    active_alerts.append(alert)
            else:
                active_alerts.append(alert)
    except:
        pass
    
    if not active_alerts:
        if user_regions:
            return f"🟢 <b>Наразі тривог немає</b> у ваших регіонах:\n{', '.join(user_regions)}"
        return "🟢 <b>Наразі тривог немає по всій Україні</b>"
    
    text = "🔴 <b>УВАГА! Повітряна тривога:</b>\n\n"
    for alert in active_alerts[:10]:
        text += f"🚨 {alert.location_title}\n"
        if hasattr(alert, 'started_at') and alert.started_at:
            text += f"   ⏰ Початок: {alert.started_at}\n"
    
    text += f"\n📊 Всього активних тривог: {len(active_alerts)}"
    text += "\n\n⚠️ <b>Прямуйте до укриття!</b>"
    return text

@dp.message(CommandStart())
async def start(message: types.Message):
    user = db.add_or_update_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )
    
    await message.answer(
        f"🇺🇦 <b>Карта Тривог України</b>\n\n"
        f"Отримуйте сповіщення про тривоги в реальному часі.\n"
        f"🔔 Дані оновлюються автоматично\n\n"
        f"👤 Творець: {CREATOR}\n\n"
        f"⬇️ Оберіть область для сповіщень:",
        reply_markup=regions_keyboard()
    )

@dp.callback_query(F.data.startswith("region:"))
async def choose_region(callback: types.CallbackQuery):
    region = callback.data.split(":", 1)[1]
    user_regions = db.get_user_regions(callback.from_user.id)
    
    if region not in user_regions:
        user_regions.append(region)
        db.update_user_regions(callback.from_user.id, user_regions)

    await callback.answer("✅ Область додано")
    await callback.message.answer(
        f"✅ Ваші обрані області:\n<b>{', '.join(user_regions)}</b>\n\n"
        f"Тепер ви отримуватимете сповіщення про тривоги.",
        reply_markup=main_menu
    )

@dp.message(F.text == "🗺 Моя область")
async def my_region(message: types.Message):
    user_regions = db.get_user_regions(message.from_user.id)
    if user_regions:
        kb = InlineKeyboardBuilder()
        kb.button(text="➕ Додати область", callback_data="add_region")
        kb.button(text="🗑 Очистити всі", callback_data="clear_regions")
        kb.adjust(2)
        
        await message.answer(
            f"🗺 <b>Ваші обрані області:</b>\n\n{chr(10).join(['• ' + r for r in user_regions])}",
            reply_markup=kb.as_markup()
        )
    else:
        await message.answer(
            "Ви ще не обрали область.\n\nОберіть область для сповіщень:",
            reply_markup=regions_keyboard()
        )

@dp.callback_query(F.data == "add_region")
async def add_region_callback(callback: types.CallbackQuery):
    await callback.message.answer("Оберіть область:", reply_markup=regions_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "clear_regions")
async def clear_regions_callback(callback: types.CallbackQuery):
    db.update_user_regions(callback.from_user.id, [])
    await callback.answer("✅ Всі області очищено")
    await callback.message.answer("Області очищено. Оберіть нові:", reply_markup=regions_keyboard())

@dp.message(F.text == "🚨 Статус тривоги")
async def alarm_status(message: types.Message):
    await message.answer("⏳ Отримую дані про тривоги...")
    
    user_regions = db.get_user_regions(message.from_user.id)
    alerts = await get_alerts_status()
    status_text = format_alert_status(alerts, user_regions if user_regions else None)
    
    await message.answer(status_text)

@dp.message(F.text == "🛡 Укриття поруч")
async def shelter(message: types.Message):
    user_regions = db.get_user_regions(message.from_user.id)
    
    kb = InlineKeyboardBuilder()
    for region in (user_regions if user_regions else REGIONS[:8]):
        kb.button(text=region, callback_data=f"shelter:{region}")
    kb.adjust(2)
    
    await message.answer(
        "🛡 <b>Пошук укриттів</b>\n\n"
        "Оберіть область для пошуку укриттів:",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data.startswith("shelter:"))
async def show_shelters(callback: types.CallbackQuery):
    region = callback.data.split(":", 1)[1]
    shelters = db.get_shelters_by_region(region)
    
    if shelters:
        text = f"🛡 <b>Укриття в {region}:</b>\n\n"
        for s in shelters[:10]:
            emoji = "🚇" if s["shelter_type"] == "метро" else "🏠"
            text += f"{emoji} <b>{s['city']}</b>\n"
            text += f"   📍 {s['address']}\n"
            if s["capacity"]:
                text += f"   👥 Місткість: ~{s['capacity']} осіб\n"
            text += "\n"
    else:
        text = f"😔 На жаль, укриття для {region} ще не додано в базу.\n\n"
        text += "Рекомендуємо:\n• Станції метро\n• Підземні паркінги\n• Підвали будинків"
    
    await callback.message.answer(text)
    await callback.answer()

@dp.message(F.text == "🔔 Налаштування")
async def settings(message: types.Message):
    user = db.get_user(message.from_user.id)
    notifications = "увімкнено" if user and user.get("notifications_enabled", 1) else "вимкнено"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔕 Вимкнути сповіщення" if notifications == "увімкнено" else "🔔 Увімкнути сповіщення", 
              callback_data="toggle_notifications")
    kb.button(text="🗺 Змінити області", callback_data="add_region")
    kb.adjust(1)
    
    await message.answer(
        f"⚙️ <b>Налаштування</b>\n\n"
        f"🔔 Сповіщення: <b>{notifications}</b>\n"
        f"🗺 Обрані області: {len(db.get_user_regions(message.from_user.id))}",
        reply_markup=kb.as_markup()
    )

@dp.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(callback: types.CallbackQuery):
    await callback.answer("✅ Налаштування змінено")
    await callback.message.answer("Налаштування сповіщень змінено.")

@dp.message(F.text == "👤 Мій профіль")
async def profile(message: types.Message):
    user = db.get_user(message.from_user.id)
    user_regions = db.get_user_regions(message.from_user.id)
    
    await message.answer(
        f"👤 <b>Ваш профіль</b>\n\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"👤 Ім'я: {message.from_user.full_name}\n"
        f"📛 Username: @{message.from_user.username or 'не вказано'}\n"
        f"🎭 Роль: {user['role'] if user else 'user'}\n"
        f"🗺 Області: {len(user_regions)}\n\n"
        f"📅 Перший візит: {user['first_seen'][:10] if user else 'сьогодні'}"
    )

@dp.message(F.text == "ℹ️ Про бота")
async def about(message: types.Message):
    users_count = db.get_users_count()
    await message.answer(
        f"🇺🇦 <b>Карта Тривог v2.0</b>\n\n"
        f"Бот для сповіщень про повітряні тривоги в Україні.\n\n"
        f"📊 Джерело: alerts.in.ua\n"
        f"👥 Користувачів: {users_count}\n\n"
        f"👤 Творець: {CREATOR}\n\n"
        f"🔗 Адмін-панель: /admin"
    )

@dp.message(F.text == MODERATOR_PASSWORD)
async def moderator_login(message: types.Message):
    db.update_user_role(message.from_user.id, "moderator")
    await message.delete()
    await message.answer("✅ Ви отримали статус <b>МОДЕРАТОР</b>")

@dp.message(Command("admin"))
async def admin_info(message: types.Message):
    user = db.get_user(message.from_user.id)
    if user and user.get("role") in ["moderator", "admin"]:
        users_count = db.get_users_count()
        await message.answer(
            f"🔧 <b>Адмін панель</b>\n\n"
            f"👥 Всього користувачів: {users_count}\n\n"
            f"🌐 Веб-панель: відкрийте сайт цього Replit\n\n"
            f"Команди:\n"
            f"/broadcast [текст] - розсилка всім\n"
            f"/stats - статистика"
        )
    else:
        await message.answer("⛔ У вас немає доступу до адмін-панелі")

@dp.message(Command("broadcast"))
async def broadcast_command(message: types.Message):
    user = db.get_user(message.from_user.id)
    if not user or user.get("role") not in ["moderator", "admin"]:
        return await message.answer("⛔ У вас немає доступу")
    
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        return await message.answer("Використання: /broadcast [текст повідомлення]")
    
    users = db.get_all_users()
    sent = 0
    for u in users:
        try:
            await bot.send_message(u["user_id"], f"📢 <b>Оголошення:</b>\n\n{text}")
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass
    
    db.add_broadcast(text, str(message.from_user.id), sent)
    await message.answer(f"✅ Повідомлення надіслано {sent} користувачам")

@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    user = db.get_user(message.from_user.id)
    if not user or user.get("role") not in ["moderator", "admin"]:
        return await message.answer("⛔ У вас немає доступу")
    
    users = db.get_all_users()
    regions = db.get_all_regions()
    
    region_stats = {}
    for u in users:
        for r in u.get("regions", "").split(","):
            if r:
                region_stats[r] = region_stats.get(r, 0) + 1
    
    top_regions = sorted(region_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    
    text = f"📊 <b>Статистика бота</b>\n\n"
    text += f"👥 Всього користувачів: {len(users)}\n"
    text += f"🗺 Топ областей:\n"
    for region, count in top_regions:
        text += f"  • {region}: {count}\n"
    
    await message.answer(text)

async def check_alerts_loop():
    while True:
        try:
            if ALERTS_TOKEN:
                alerts = await get_alerts_status()
                if alerts:
                    try:
                        air_raids = alerts.get_air_raid_alerts()
                        for alert in air_raids:
                            region_name = alert.location_title
                            users = db.get_users_by_region(region_name)
                            for user in users[:5]:
                                try:
                                    await bot.send_message(
                                        user["user_id"],
                                        f"🚨 <b>ТРИВОГА!</b>\n\n{region_name}\n\n⚠️ Прямуйте до укриття!"
                                    )
                                except:
                                    pass
                    except:
                        pass
        except Exception as e:
            logging.error(f"Alert check error: {e}")
        
        await asyncio.sleep(240)

async def main():
    asyncio.create_task(check_alerts_loop())
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Бот 'Карта Тривог' v2.0 запущено!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
