from loader import dp
from aiogram.types import Message
from aiogram import F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from filters.admin_bot import IsBotOrAssistantAdmin
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton
from states.my_states import (
    BranchState, CompanyState, BotInfoState, TransferState, AdminState, ChannelState, TextAdd, ImageAdd, MusicAdd,
    VideoAdd, AdState, CompanyAdd, CompanyEdit, BranchAdd, BranchEdit, ChannelAdd, ChannelDeleteState, UserState
)
from keyboards.default.buttons import (
    company_crud_button, admin_button, branch_crud_button, channel_crud, add_type, back_button, company_edit_button,
    branch_edit_button, users_crud_button, admins_crud_button
)
from database.orm_query import select_all_companies, get_branch_by_company_id


@dp.message(F.text.in_(["⬅️ Orqaga"]), IsBotOrAssistantAdmin())
async def back_state_main(message: Message, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    text = "Kerakli bo'limni tanlang!"
    back_btn = await back_button()
    if current_state in [
        BranchState.branch_menu,
        CompanyState.main_menu,
        BotInfoState.bot_info,
        TransferState.transfer_menu,
        ChannelState.channel_menu,
        AdState.ad_menu,
        UserState.companies
        ]:
        await state.clear()
        admin_btn = await admin_button()
        await message.answer("💼 Admin panel", reply_markup=admin_btn)

    elif current_state in [
            CompanyAdd.branch_link,
            CompanyState.delete,
            CompanyEdit.list,
        ]:
        await state.set_state(CompanyState.main_menu)
        company_crud_btn = await company_crud_button()
        await message.answer(text=text, reply_markup=company_crud_btn)

    elif current_state in [
            BranchAdd.company,
            BranchState.company,
            BranchEdit.company
        ]:
        await state.set_state(BranchState.branch_menu)
        branch_crud_btn = await branch_crud_button()
        await message.answer(text=text, reply_markup=branch_crud_btn)

    elif current_state in [
            ChannelAdd.category,
            ChannelDeleteState.category
        ]:
        await state.set_state(ChannelState.channel_menu)
        channel_crud_btn = await channel_crud()
        await message.answer(text=text, reply_markup=channel_crud_btn)

    elif current_state in [
            TextAdd.text,
            ImageAdd.image,
            MusicAdd.music,
            VideoAdd.video
        ]:
        await state.set_state(AdState.ad_menu)
        add_type_btn = await add_type()
        await message.answer("Qanday turdagi xabar yubormoqchisiz?", reply_markup=add_type_btn)

    elif current_state == CompanyAdd.terminal_link:
        await state.set_state(CompanyAdd.branch_link)
        await message.answer(
            text="🔗 Filiallar ro'yxatini oluvchi API linkini kiriting",
            reply_markup=back_btn
        )

    elif current_state == CompanyAdd.login:
        await state.set_state(CompanyAdd.terminal_link)
        await message.answer(
            text="🔗 Kassalar ro'yxatini oluvchi API linkini kiriting",
            reply_markup=back_btn
        )

    elif current_state == CompanyAdd.password:
        await state.set_state(CompanyAdd.login)
        await message.answer("🔏 API loginini kiring.", reply_markup=back_btn)

    elif current_state in [
            CompanyEdit.name,
            CompanyEdit.branch_link,
            CompanyEdit.terminal_link,
            CompanyEdit.login,
            CompanyEdit.password
        ]:
        await state.set_state(CompanyEdit.edit_menu)
        company_edit_btn = await company_edit_button()
        await message.answer(
            text="Qaysi qismini tahrirlamoqchisiz?",
            reply_markup=company_edit_btn
        )
    elif current_state == CompanyEdit.edit_menu:
        companies = await select_all_companies(session)
        await state.set_state(CompanyEdit.list)
        keyboard = ReplyKeyboardBuilder()
        for company in companies:
            button = KeyboardButton(text=company.name)
            keyboard.add(button)
        keyboard.adjust(2)
        back_btn = KeyboardButton(text="⬅️ Orqaga")
        keyboard.row(back_btn)
        await message.answer(
            text="Qaysi kompaniyani tahrirlamoqchisiz",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
    elif current_state == BranchAdd.name:
        companies = await select_all_companies(session)
        await state.set_state(BranchAdd.company)
        keyboard = ReplyKeyboardBuilder()
        for company in companies:
            button = KeyboardButton(text=company.name)
            keyboard.add(button)
        keyboard.adjust(2)
        back_btn = KeyboardButton(text="⬅️ Orqaga")
        keyboard.row(back_btn)
        await message.answer(
            text="Kompaniyani tanlang:",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
    elif current_state == BranchAdd.cashier_url:
        await state.set_state(BranchAdd.name)
        await message.answer("🏛 Filial nomini kiriting.", reply_markup=back_btn)

    elif current_state == BranchAdd.chief_cashier_url:
        await state.set_state(BranchAdd.cashier_url)
        await message.answer(
            "🔗 Kassir-URLini kiriting.", reply_markup=back_btn
        )

    elif current_state == BranchAdd.transaction_url:
        await state.set_state(BranchAdd.chief_cashier_url)
        await message.answer(
            "🔗 Bosh-kassir-URLini kiriting.", reply_markup=back_btn
        )

    elif current_state == BranchAdd.check_pass_url:
        await state.set_state(BranchAdd.transaction_url)
        await message.answer(
            "🔗 Parol tekshirish-URLini kiriting.", reply_markup=back_btn
        )

    elif current_state == BranchAdd.login:
        await state.set_state(BranchAdd.check_pass_url)
        await message.answer(
            "🔗 Transaksiya URLini kiriting.", reply_markup=back_btn
        )

    elif current_state == BranchAdd.password:
        await state.set_state(BranchAdd.login)
        await message.answer(
            "🔏 API loginini kiring.", reply_markup=back_btn
        )

    elif current_state == BranchEdit.select:
        companies = await select_all_companies(session)
        await state.set_state(BranchEdit.company)
        keyboard = ReplyKeyboardBuilder()
        for company in companies:
            button = KeyboardButton(text=company.name)
            keyboard.add(button)
        keyboard.adjust(2)
        back_btn = KeyboardButton(text="⬅️ Orqaga")
        keyboard.row(back_btn)
        await message.answer(
            text="Kompaniyani tanlang:",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )

    elif current_state == BranchEdit.edit_menu:
        companies = await select_all_companies(session)
        await state.set_state(BranchEdit.company)
        keyboard = ReplyKeyboardBuilder()
        for company in companies:
            button = KeyboardButton(text=company.name)
            keyboard.add(button)
        keyboard.adjust(2)
        back_btn = KeyboardButton(text="⬅️ Orqaga")
        keyboard.row(back_btn)
        await message.answer(
            text="Kompaniyani tanlang:",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )

    elif current_state in [
        BranchEdit.name,
        BranchEdit.cashier_link,
        BranchEdit.chief_cashier_link,
        BranchEdit.check_pass_link,
        BranchEdit.transaction_link,
        BranchEdit.get_transaction_link,
        BranchEdit.check_transaction_link,
        BranchEdit.login,
        BranchEdit.password
        ]:
        await state.set_state(BranchEdit.edit_menu)
        branch_edit_btn = await branch_edit_button()
        await message.answer(
            text="Qaysi qismini tahrirlamoqchisiz?",
            reply_markup=branch_edit_btn
        )

    elif current_state == UserState.main_menu:
        companies = await select_all_companies(session)
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

    elif current_state == AdminState.admin_menu:
        await state.set_state(UserState.main_menu)
        users_crud_btn = await users_crud_button()
        await message.answer("Kerakli bo'limni tanlang!", reply_markup=users_crud_btn)

    elif current_state == AdminState.admin_get:
        await state.set_state(AdminState.admin_menu)
        admins_crud_btn = await admins_crud_button()
        await message.answer("Kerakli bo'limni tanlang!", reply_markup=admins_crud_btn)