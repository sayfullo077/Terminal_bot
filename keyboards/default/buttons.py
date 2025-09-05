from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database.orm_query import select_user, orm_select_all_branch


camera_button = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📷 Suratga olish", request_contact=False)]
    ],
    resize_keyboard=True
)


async def admin_position_button():
    btn = ReplyKeyboardBuilder()
    btn.button(text="Bosh kassir")
    btn.button(text="Kassir")
    btn.button(text="⬅️ Orqaga")
    btn.adjust(2)
    return btn.as_markup()


async def admin_confirm_button():
    btn = ReplyKeyboardBuilder()
    btn.button(text="✅Ha")
    btn.button(text="❌Yo'q")
    btn.adjust(2)
    return btn.as_markup(resize_keyboard=True)


async def user_confirm_reply_btn():
    btn = ReplyKeyboardBuilder()
    btn.button(text="✅Ha")
    btn.button(text="❌Yo'q")
    btn.adjust(2)
    return btn.as_markup(resize_keyboard=True)


async def admin_button():
    btn = ReplyKeyboardBuilder()
    btn.button(text="🏦 Kompaniya")
    btn.button(text="🏛 Filial")
    btn.button(text="🗂 Hisobot")
    btn.button(text="👨‍💻 Foydalanuvchilar")
    btn.button(text="🆎 Reklama yuborish")
    btn.button(text="ℹ️ Bot info")
    btn.adjust(2)
    return btn.as_markup(resize_keyboard=True, input_placeholder="Kerakli bo'limni tanlang !", on_time_keyboard=True)


async def company_crud_button():
    btn = ReplyKeyboardBuilder()
    btn.button(text="🔖 Kompaniya qo'shish")
    btn.button(text="📝 Kompaniya o'zgartirish")
    btn.button(text="⚠️ Kompaniya o'chirish")
    btn.button(text="⬅️ Orqaga")
    btn.adjust(2)
    return btn.as_markup(resize_keyboard=True)


async def company_edit_button():
    btn = ReplyKeyboardBuilder()
    btn.button(text="🏦 Kompaniya nomi")
    btn.button(text="🔗 Filial URL")
    btn.button(text="🔗 Terminal URL")
    btn.button(text="🔏️ API-login")
    btn.button(text="🔐 API-password")
    btn.button(text="⬅️ Orqaga")
    btn.adjust(2)
    return btn.as_markup(resize_keyboard=True)


async def branch_crud_button():
    btn = ReplyKeyboardBuilder()
    btn.button(text="🔖 Filial qo'shish")
    btn.button(text="📝 Filial o'zgartirish")
    btn.button(text="⚠️ Filial o'chirish")
    btn.button(text="⬅️ Orqaga")
    btn.adjust(2)
    return btn.as_markup(resize_keyboard=True)


async def branch_edit_button():
    btn = ReplyKeyboardBuilder()
    btn.button(text="🏛 Filial nomi")
    btn.button(text="🔗 Kassir URL")
    btn.button(text="🔗 Bosh kassir URL")
    btn.button(text="🔗 Parol check URL")
    btn.button(text="🔗 Create Transaksiya URL")
    btn.button(text="🔗 Get Transactions URL")
    btn.button(text="🔗 Check Transaction URL")
    btn.button(text="🔏️ API-login")
    btn.button(text="🔐 API-password")
    btn.button(text="⬅️ Orqaga")
    btn.adjust(2)
    return btn.as_markup(resize_keyboard=True)


async def transaction_crud_button():
    btn = ReplyKeyboardBuilder()
    btn.button(text="📋 Sverkalar ro'yxati")
    btn.button(text="📅 Bugungi sverka")
    btn.button(text="⚠️ Sverka o'chirish")
    btn.button(text="⬅️ Orqaga")
    btn.adjust(2)
    return btn.as_markup(resize_keyboard=True)


async def add_type():
    btn = ReplyKeyboardBuilder()
    btn.button(text="📝 Text")
    btn.button(text="📷 Photo")
    btn.button(text="🎥 Video")
    btn.button(text="🎵 Music")
    btn.button(text="⬅️ Orqaga")

    btn.adjust(2)
    return btn.as_markup(resize_keyboard=True)


async def users_crud_button():
    btn = ReplyKeyboardBuilder()
    btn.button(text="👨‍💻 Adminlar")
    btn.button(text="🤵‍♂️ Bosh kassirlar")
    btn.button(text="⬅️ Orqaga")
    btn.button(text="👨‍💼 Kassirlar")
    btn.adjust(2)
    return btn.as_markup(resize_keyboard=True)


async def admins_crud_button():
    btn = ReplyKeyboardBuilder()
    btn.button(text="📝 Admin qo'shish")
    btn.button(text="📋 Adminlar ro'yxati")
    btn.button(text="⚠️ Adminlar o'chirish")
    btn.button(text="⬅️ Orqaga")
    btn.adjust(2)
    return btn.as_markup(resize_keyboard=True)


async def channel_crud():
    btn = ReplyKeyboardBuilder()
    btn.button(text="📝 Kanal qo'shish")
    btn.button(text="⚠️ Kanal o'chirish")
    btn.button(text="⬅️ Orqaga")
    btn.adjust(2, 1)
    return btn.as_markup(resize_keyboard=True)


async def back_button():
    btn = ReplyKeyboardBuilder()
    btn.button(text="⬅️ Orqaga")
    return btn.as_markup(resize_keyboard=True)
