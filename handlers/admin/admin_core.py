from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import KeyboardButton

import datetime
import re

from aiogram import types, F
from sqlalchemy.ext.asyncio import AsyncSession

from data.config import ADMINS
from loader import dp, bot
from filters.admin_bot import IsBotOrAssistantAdmin
from states.my_states import (
    TransferState, BranchState,
    AdminState, ChannelState, BotInfoState,
    AdState, CompanyState, UserState
)
from keyboards.default.buttons import (
    branch_crud_button, channel_crud, admins_crud_button, transaction_crud_button,
    admin_button, back_button, add_type, company_crud_button, users_crud_button
)
from database.orm_query import (
    count_users, count_daily_users, get_admin_users_by_company,
    count_weekly_users, count_monthly_users, get_admin_users,
    select_all_companies, get_company_id_by_name
)


def html_escape(text):
    escape_chars = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}
    return re.sub(r'[&<>"\']', lambda match: escape_chars[match.group(0)], text)


@dp.message(Command('admin'))
async def start_admin_panel(message: types.Message, state: FSMContext, session: AsyncSession):
    telegram_id = message.from_user.id
    is_bot_admin = str(telegram_id) in ADMINS
    assistant_admins = await get_admin_users(session)
    admin_ids = [admin_id for admin_id in assistant_admins]
    is_assistant_admin = telegram_id in admin_ids
    admin_btn = await admin_button()
    if is_bot_admin or is_assistant_admin:
        await message.answer("💼 Admin panel", reply_markup=admin_btn)
    else:
        await message.answer("Bu buyruq faqat adminlar uchun mavjud ❗️\n Yordam olish uchun /help buyrug'ini kiriting.")


@dp.message(F.text.in_(["🏦 Kompaniya"]), IsBotOrAssistantAdmin())
async def category_info(message: types.Message, state: FSMContext):
    await state.set_state(CompanyState.main_menu)
    company_crud_btn = await company_crud_button()
    await message.delete()
    await message.answer("Kerakli bo'limni tanlang!", reply_markup=company_crud_btn)


@dp.message(F.text.in_(["🏛 Filial"]), IsBotOrAssistantAdmin())
async def branch_info(message: types.Message, state: FSMContext):
    await state.set_state(BranchState.branch_menu)
    branch_crud_btn = await branch_crud_button()
    await message.answer("Kerakli bo'limni tanlang!", reply_markup=branch_crud_btn)


@dp.message(F.text.in_(["🗂 Hisobot"]), IsBotOrAssistantAdmin())
async def transaction_menu(message: types.Message, state: FSMContext, session: AsyncSession):
    companies = await select_all_companies(session)
    if companies:
        await state.set_state(TransferState.company)
        keyboard = ReplyKeyboardBuilder()
        for company in companies:
            button = KeyboardButton(text=company.name)
            keyboard.add(button)
        keyboard.adjust(2)
        back_btn = KeyboardButton(text="⬅️ Orqaga")
        keyboard.row(back_btn)
        await message.delete()
        await message.answer(
            text="Kompaniyani tanlang:",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
    else:
        await state.set_state(TransferState.transfer_menu)
        branch_crud_btn = await branch_crud_button()
        await message.delete()
        await message.answer(
            text="Kompaniyalar yo'q ❗️\nAvval kompaniya qo'shing.",
            reply_markup=branch_crud_btn
        )


@dp.message(TransferState.company)
async def select_transaction_company(message: types.Message, state: FSMContext, session: AsyncSession):
    name = message.text.strip()
    company_id = await get_company_id_by_name(session, name)
    await state.set_state(TransferState.crud_menu)
    await state.update_data(company_name=name, company_id=company_id)
    transaction_crud_btn = await transaction_crud_button()
    await message.answer("Kerakli bo'limni tanlang!", reply_markup=transaction_crud_btn)


@dp.message(F.text.in_(["ℹ️ Bot info"]), IsBotOrAssistantAdmin())
async def get_count_users(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.set_state(BotInfoState.bot_info)
    count_total = await count_users(session)
    daily_new = await count_daily_users(session)
    weekly_new = await count_weekly_users(session)
    monthly_new = await count_monthly_users(session)

    datas = datetime.datetime.now()
    sana = datas.date()
    vaqt = f"{datas.hour}:{datas.minute}:{datas.second}"

    stats_message = (
        f"<b>⏰ Soat: {vaqt}\n</b>"
        f"<b>📆 Sana: {sana}\n\n</b>"
        f"🍦 Kunlik yangi obunachilar: {daily_new}\n"
        f"🍰 Haftalik yangi obunachilar: {weekly_new}\n"
        f"🎂 Oylik yangi obunachilar: {monthly_new}\n\n"
        f"🏄‍ Hozirda botda: {count_total} ta faol obunachi bor."
    )
    back_btn = await back_button()
    await message.answer(stats_message, reply_markup=back_btn)


@dp.message(F.text.in_(["🆎 Reklama yuborish", "🆎 Подать объявление"]), IsBotOrAssistantAdmin())
async def get_add_type(message: types.Message, state: FSMContext):
    await state.set_state(AdState.ad_menu)
    add_type_btn = await add_type()
    await message.answer("Qanday turdagi xabar yubormoqchisiz?", reply_markup=add_type_btn)


@dp.message(F.text.in_(["⚜️ Kanallar"]), IsBotOrAssistantAdmin())
async def channel_info(message: types.Message, state: FSMContext):
    await state.set_state(ChannelState.channel_menu)
    channel_crud_btn = await channel_crud()
    await message.answer("Kerakli bo'limni tanlang!", reply_markup=channel_crud_btn)


@dp.message(F.text.in_(["👨‍💻 Foydalanuvchilar"]), IsBotOrAssistantAdmin())
async def admin_info(message: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    companies = await select_all_companies(session)
    if companies:
        await state.set_state(UserState.companies)
        keyboard = ReplyKeyboardBuilder()
        for company in companies:
            button = KeyboardButton(text=company.name)
            keyboard.add(button)
        keyboard.adjust(2)
        back_btn = KeyboardButton(text="⬅️ Orqaga")
        keyboard.row(back_btn)
        await message.delete()
        await message.answer(
            text="Kompaniyani tanlang:",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
    else:
        branch_crud_btn = await branch_crud_button()
        await message.delete()
        await message.answer(
            text="Kompaniyalar yo'q ❗️\nAvval kompaniya qo'shing.",
            reply_markup=branch_crud_btn
        )


@dp.message(UserState.companies)
async def users_info(message: types.Message, state: FSMContext, session: AsyncSession):
    name = message.text.strip()
    company_id = await get_company_id_by_name(session, name)
    await state.set_state(UserState.main_menu)
    await state.update_data(company_name=name, company_id=company_id)
    users_crud_btn = await users_crud_button()
    await message.answer("Kerakli bo'limni tanlang!", reply_markup=users_crud_btn)


@dp.message(UserState.main_menu, F.text.in_("👨‍💻 Adminlar"), IsBotOrAssistantAdmin())
async def admin_menu(message: types.Message, state: FSMContext):
    data = await state.get_data()
    company_name = data.get("company_name")
    company_id = data.get("company_id")
    await state.set_state(AdminState.admin_menu)
    await state.update_data(company_name=company_name, company_id=company_id)
    admins_crud_btn = await admins_crud_button()
    await message.answer("Kerakli bo'limni tanlang!", reply_markup=admins_crud_btn)


@dp.message(AdminState.admin_menu, F.text.in_("📋 Adminlar ro'yxati"), IsBotOrAssistantAdmin())
async def admin_list(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    company_id = data.get("company_id")
    assistant_admins = await get_admin_users_by_company(session, company_id)

    if not assistant_admins:
        await message.answer("❗️ Hozircha adminlar qo‘shilmagan.")
        return

    buttons = []
    for admin_id in assistant_admins:
        chat = await bot.get_chat(int(admin_id))
        full_name = chat.full_name
        buttons.append([
            InlineKeyboardButton(text=f"👤 Admin ({full_name})", url=f"tg://user?id={admin_id}")
        ])

    reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("👨‍💻 Adminlar ro'yxati:", reply_markup=reply_markup)

