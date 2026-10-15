import asyncio
import logging
import html
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)

# --- SOZLAMALAR ---
BOT_TOKEN = "8722167175:AAFL8OlVXpi4EVndDJpRDk5rCC_h17lcniM"
CHANNEL_ID = "@songgi_satrlarim_1421"
CHANNEL_URL = "https://t.me/songgi_satrlarim_1421"
CARD_NUMBER = "9860 1606 3439 0605"
CARD_HOLDER = "K.E"
ADMIN_ID = 1438313297  # Sizning Telegram ID raqamingiz

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

users_db = {}
waiting_queue = []

class Registration(StatesGroup):
    gender = State()
    age = State()
    region = State()

class VIPSearch(StatesGroup):
    target_gender = State()

class PaymentState(StatesGroup):
    waiting_receipt = State()

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Suhbatdosh qidirish")],
            [KeyboardButton(text="⭐ VIP Obuna / Tariflar"), KeyboardButton(text="👤 Profilim")]
        ],
        resize_keyboard=True
    )

def get_gender_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="👨 Yigit"), KeyboardButton(text="👩 Qiz")]],
        resize_keyboard=True, one_time_keyboard=True
    )

def get_region_keyboard():
    regions = [
        ["Toshkent", "Andijon"], ["Buxoro", "Farg'ona"],
        ["Jizzax", "Xorazm"], ["Namangan", "Navoiy"],
        ["Qashqadaryo", "Samarqand"], ["Sirdaryo", "Surxondaryo"],
        ["Qoraqalpog'iston"]
    ]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=r) for r in row] for row in regions],
        resize_keyboard=True, one_time_keyboard=True
    )

def get_sub_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="✅ Obunani tasdiqlash", callback_data="check_sub")]
    ])

def get_tariffs_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗓 1 haftalik — 7 000 so'm", callback_data="pay_7000")],
        [InlineKeyboardButton(text="🗓 1 oylik — 20 000 so'm", callback_data="pay_20000")]
    ])

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ["kicked", "left"]:
            return False
        return True
    except Exception as e:
        logging.error(f"Obuna tekshirishda xatolik: {e}")
        return False

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {
            "gender": None, "age": None, "region": None,
            "is_vip": False, "vip_until": None, "partner": None
        }
        await message.answer("Xush kelibsiz! Avval ro'yxatdan o'taylik.\n\nJinsingizni tanlang:", reply_markup=get_gender_keyboard())
        await state.set_state(Registration.gender)
    else:
        await check_and_show_menu(message)

@dp.message(Registration.gender)
async def process_gender(message: types.Message, state: FSMContext):
    if message.text in ["👨 Yigit", "👩 Qiz"]:
        users_db[message.from_user.id]["gender"] = message.text
        await message.answer("Yoshingizni kiriting (masalan: 20):", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Registration.age)
    else:
        await message.answer("Iltimos, tugmalardan birini tanlang.")

@dp.message(Registration.age)
async def process_age(message: types.Message, state: FSMContext):
    if message.text.isdigit() and 10 <= int(message.text) <= 80:
        users_db[message.from_user.id]["age"] = int(message.text)
        await message.answer("Qaysi viloyatdansiz?", reply_markup=get_region_keyboard())
        await state.set_state(Registration.region)
    else:
        await message.answer("Iltimos, yoshingizni raqamda to'g'ri kiriting (10-80 oralig'ida).")

@dp.message(Registration.region)
async def process_region(message: types.Message, state: FSMContext):
    users_db[message.from_user.id]["region"] = message.text
    await state.clear()
    await message.answer("Ro'yxatdan muvaffaqiyatli o'tdingiz!", reply_markup=ReplyKeyboardRemove())
    await check_and_show_menu(message)

async def check_and_show_menu(message: types.Message):
    user_id = message.from_user.id
    if await check_subscription(user_id):
        await message.answer("Bosh menyu:", reply_markup=get_main_menu())
    else:
        await message.answer(
            "⚠️ Botdan foydalanish uchun rasmiy kanalimizga obuna bo'lishingiz shart:",
            reply_markup=get_sub_keyboard()
        )

@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(call: CallbackQuery):
    if await check_subscription(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Obuna tasdiqlandi! Bosh menyu:", reply_markup=get_main_menu())
    else:
        await call.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)

@dp.message(F.text == "👤 Profilim")
async def show_profile(message: types.Message):
    u = users_db.get(message.from_user.id, {})
    is_vip = u.get("is_vip")
    vip_until = u.get("vip_until")
    
    if is_vip and vip_until and datetime.now() > vip_until:
        u["is_vip"] = False
        is_vip = False

    status = f"⭐ VIP Obunachi ({vip_until.strftime('%Y-%m-%d')} gacha)" if is_vip else "Oddiy foydalanuvchi"
    text = (f"👤 <b>Sizning profilingiz:</b>\n\n"
            f"• Jins: {u.get('gender')}\n"
            f"• Yosh: {u.get('age')}\n"
            f"• Viloyat: {u.get('region')}\n"
            f"• Maqom: {status}")
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "⭐ VIP Obuna / Tariflar")
async def show_tariffs(message: types.Message):
    text = (f"⭐ <b>VIP Obuna afzalliklari:</b>\n\n"
            f"1. Suhbatdoshning yoshi, viloyati va jinsini ko'rish.\n"
            f"2. Kim bilan tanishishni tanlash (Yigit / Qiz).\n\n"
            f"💰 <b>Tariflar:</b>\n"
            f"• 1 haftalik — 7 000 so'm\n"
            f"• 1 oylik — 20 000 so'm")
    await message.answer(text, reply_markup=get_tariffs_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("pay_"))
async def process_payment_click(call: CallbackQuery, state: FSMContext):
    amount = "7 000" if call.data == "pay_7000" else "20 000"
    text = (f"To'lov summasi: <b>{amount} so'm</b>\n\n"
            f"💳 Karta raqam: <code>{CARD_NUMBER}</code>\n"
            f"👤 Egasining ismi: <b>{CARD_HOLDER}</b>\n\n"
            f"To'lovni amalga oshirgach, to'lov chekini (rasm/skrinshot) ushbu botga yuboring.")
    await call.message.answer(text, parse_mode="HTML")
    await state.set_state(PaymentState.waiting_receipt)

@dp.message(PaymentState.waiting_receipt, F.photo)
async def process_receipt(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Chekingiz qabul qilindi! Admin tasdiqlashini kuting.", reply_markup=get_main_menu())
    
    username = f"@{call_user_name}" if (call_user_name := message.from_user.username) else "Mavjud emas"
    full_name = html.escape(message.from_user.full_name)
    
    text_to_admin = (f"📥 <b>Yangi to'lov cheki!</b>\n\n"
                     f"• User ID: <code>{message.from_user.id}</code>\n"
                     f"• Username: {username}\n"
                     f"• Ism: {full_name}\n\n"
                     f"<b>Obuna berish uchun ushbu buyruqlardan birini nusxalab, botga yuboring:</b>\n"
                     f"👉 1 haftalik: <code>/vip_7 {message.from_user.id}</code>\n"
                     f"👉 1 oylik: <code>/vip_30 {message.from_user.id}</code>")
    
    try:
        await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=text_to_admin, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Adminga chek yuborishda xatolik: {e}")

@dp.message(Command("vip_7"))
async def give_vip_7(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        if user_id not in users_db:
            users_db[user_id] = {"gender": "Noma'lum", "age": "-", "region": "-", "partner": None}
        
        users_db[user_id]["is_vip"] = True
        users_db[user_id]["vip_until"] = datetime.now() + timedelta(days=7)
        
        await message.answer(f"✅ User <code>{user_id}</code> ga 7 kunlik VIP berildi!", parse_mode="HTML")
        await bot.send_message(user_id, "🎉 Tabriklaymiz! Sizga 7 kunlik VIP obuna berildi!")
    except Exception:
        await message.answer("Xatolik! Buyruq formati: <code>/vip_7 USER_ID</code>", parse_mode="HTML")

@dp.message(Command("vip_30"))
async def give_vip_30(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(message.text.split()[1])
        if user_id not in users_db:
            users_db[user_id] = {"gender": "Noma'lum", "age": "-", "region": "-", "partner": None}
            
        users_db[user_id]["is_vip"] = True
        users_db[user_id]["vip_until"] = datetime.now() + timedelta(days=30)
        
        await message.answer(f"✅ User <code>{user_id}</code> ga 30 kunlik VIP berildi!", parse_mode="HTML")
        await bot.send_message(user_id, "🎉 Tabriklaymiz! Sizga 1 oylik VIP obuna berildi!")
    except Exception:
        await message.answer("Xatolik! Buyruq formati: <code>/vip_30 USER_ID</code>", parse_mode="HTML")

@dp.message(F.text == "🔍 Suhbatdosh qidirish")
async def start_chat_search(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not await check_subscription(user_id):
        await check_and_show_menu(message)
        return

    u = users_db.get(user_id, {})
    if u.get("is_vip"):
        await message.answer("Kim bilan tanishmoqchisiz?", reply_markup=get_gender_keyboard())
        await state.set_state(VIPSearch.target_gender)
    else:
        await find_partner(message, target_gender=None)

@dp.message(VIPSearch.target_gender)
async def process_vip_search(message: types.Message, state: FSMContext):
    await state.clear()
    await find_partner(message, target_gender=message.text)

async def find_partner(message: types.Message, target_gender=None):
    user_id = message.from_user.id
    
    if waiting_queue:
        partner_id = waiting_queue.pop(0)
        users_db[user_id]["partner"] = partner_id
        users_db[partner_id]["partner"] = user_id

        p1_info = users_db[user_id]
        p2_info = users_db[partner_id]

        msg1 = "🔎 Suhbatdosh topildi!"
        msg2 = "🔎 Suhbatdosh topildi!"

        if p1_info.get("is_vip"):
            msg1 += f"\n\n👤 Suhbatdosh: {p2_info['gender']}, {p2_info['age']} yosh, {p2_info['region']}"
        if p2_info.get("is_vip"):
            msg2 += f"\n\n👤 Suhbatdosh: {p1_info['gender']}, {p1_info['age']} yosh, {p1_info['region']}"

        stop_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🛑 Suhbatni tugatish")]], resize_keyboard=True)
        
        await bot.send_message(user_id, msg1, reply_markup=stop_kb)
        await bot.send_message(partner_id, msg2, reply_markup=stop_kb)
    else:
        waiting_queue.append(user_id)
        await message.answer("🔎 Mos suhbatdosh qidirilmoqda... Iltimos kuting.", 
                             reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🛑 Suhbatni tugatish")]], resize_keyboard=True))

@dp.message(F.text == "🛑 Suhbatni tugatish")
async def stop_chat(message: types.Message):
    user_id = message.from_user.id
    partner_id = users_db.get(user_id, {}).get("partner")

    if partner_id:
        await bot.send_message(partner_id, "🛑 Suhbatdosh suhbatni yakunladi.", reply_markup=get_main_menu())
        users_db[partner_id]["partner"] = None

    users_db[user_id]["partner"] = None
    if user_id in waiting_queue:
        waiting_queue.remove(user_id)

    await message.answer("Suhbat yakunlandi.", reply_markup=get_main_menu())

@dp.message()
async def forward_message(message: types.Message):
    partner_id = users_db.get(message.from_user.id, {}).get("partner")
    if partner_id:
        await bot.send_message(partner_id, message.text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())