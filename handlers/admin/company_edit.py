from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton
from aiogram import types, F
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from loader import dp
from filters.admin_bot import IsBotOrAssistantAdmin
from keyboards.default.buttons import company_crud_button, company_edit_button, back_button
from states.my_states import CompanyEdit, CompanyState
from database.orm_query import select_all_companies, get_company_id_by_name, update_company_name, update_company_branch_link, update_company_terminal_link, update_company_login, update_company_password


@dp.message(F.text.in_(["📝 Kompaniya o'zgartirish"]), IsBotOrAssistantAdmin())
async def company_edit_func(message: types.Message, state: FSMContext, session: AsyncSession):
    companies = await select_all_companies(session)
    if companies:
        await state.set_state(CompanyEdit.list)
        keyboard = ReplyKeyboardBuilder()
        for company in companies:
            button = KeyboardButton(text=company.name)
            keyboard.add(button)
        keyboard.adjust(2)
        back_btn = KeyboardButton(text="⬅️ Orqaga")
        keyboard.row(back_btn)
        await message.delete()
        await message.answer(
            text="Qaysi kompaniyani tahrirlamoqchisiz",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
    else:
        await state.set_state(CompanyState.main_menu)
        company_crud_btn = await company_crud_button()
        await message.delete()
        await message.answer(
            text="Kompaniyalar yo'q ❗️\nAvval kompaniya qo'shing.",
            reply_markup=company_crud_btn
        )


@dp.message(CompanyEdit.list)
async def select_company_list(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.set_state(CompanyEdit.edit_menu)
    name = message.text.strip()
    company_id = await get_company_id_by_name(session, name)
    await state.update_data(company_id=company_id)
    company_edit_btn = await company_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=company_edit_btn
    )


@dp.message(CompanyEdit.edit_menu, F.text.in_(["🏦 Kompaniya nomi"]), IsBotOrAssistantAdmin())
async def edit_company_name(message: types.Message, state: FSMContext):
    await state.set_state(CompanyEdit.name)
    back_btn = await back_button()
    await message.answer("🏦 Yangi nomi kiriting :", reply_markup=back_btn)


@dp.message(CompanyEdit.name, F.text.not_in(["⬅️ Orqaga"]))
async def category_name_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_name = message.text.strip()
    data = await state.get_data()
    company_id = data.get("company_id")

    try:
        updated = await update_company_name(session, company_id, new_name)

        if updated:
            await message.answer("✅ Kompaniya nomi yangilandi.")
        else:
            await message.answer("❌ Bunday kompaniya topilmadi.")

    except Exception as e:
        print(f"Error in Update Company name - {e}")
    await state.set_state(CompanyEdit.edit_menu)
    company_edit_btn = await company_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=company_edit_btn
    )


@dp.message(CompanyEdit.edit_menu, F.text.in_(["🔗 Filial URL"]), IsBotOrAssistantAdmin())
async def edit_branch_url(message: types.Message, state: FSMContext):
    await state.set_state(CompanyEdit.branch_link)
    back_btn = await back_button()
    await message.answer("🔗 Yangi Filial URlini kiriting :", reply_markup=back_btn)


@dp.message(CompanyEdit.branch_link, F.text.not_in(["⬅️ Orqaga"]))
async def category_url_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_link = message.text.strip()
    data = await state.get_data()
    company_id = data.get("company_id")

    try:
        updated = await update_company_branch_link(session, company_id, new_link)

        if updated:
            await message.answer("✅ Kompaniya Filial URL yangilandi.")
        else:
            await message.answer("❌ Bunday URL topilmadi.")

    except Exception as e:
        print(f"Error in Update Company url - {e}")
    await state.set_state(CompanyEdit.edit_menu)
    company_edit_btn = await company_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=company_edit_btn)


@dp.message(CompanyEdit.edit_menu, F.text.in_(["🔗 Terminal URL"]), IsBotOrAssistantAdmin())
async def edit_terminal_url(message: types.Message, state: FSMContext):
    await state.set_state(CompanyEdit.terminal_link)
    back_btn = await back_button()
    await message.answer("🔏 Yangi Terminal URLini kiriting :", reply_markup=back_btn)


@dp.message(CompanyEdit.terminal_link, F.text.not_in(["⬅️ Orqaga"]))
async def terminal_url_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_login = message.text.strip()
    data = await state.get_data()
    company_id = data.get("company_id")

    try:
        updated = await update_company_terminal_link(session, company_id, new_login)

        if updated:
            await message.answer("✅ Terminal URL  yangilandi.")
        else:
            await message.answer("❌ Bunday URL topilmadi.")

    except Exception as e:
        print(f"Error in Update Company login - {e}")
    await state.set_state(CompanyEdit.edit_menu)
    company_edit_btn = await company_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=company_edit_btn)


@dp.message(CompanyEdit.edit_menu, F.text.in_(["🔏️ API-login"]), IsBotOrAssistantAdmin())
async def edit_company_password(message: types.Message, state: FSMContext):
    await state.set_state(CompanyEdit.login)
    back_btn = await back_button()
    await message.answer("🔐 Yangi API-loginni kiriting :", reply_markup=back_btn)


@dp.message(CompanyEdit.login, F.text.not_in(["⬅️ Orqaga"]))
async def category_password_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_password = message.text.strip()
    data = await state.get_data()
    company_id = data.get("company_id")

    try:
        updated = await update_company_login(session, company_id, new_password)

        if updated:
            await message.answer("✅ Kompaniya logini yangilandi.")
        else:
            await message.answer("❌ Bunday login topilmadi.")

    except Exception as e:
        print(f"Error in Update Company login - {e}")
    await state.set_state(CompanyEdit.edit_menu)
    company_edit_btn = await company_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=company_edit_btn)


@dp.message(CompanyEdit.edit_menu, F.text.in_(["🔐 API-password"]), IsBotOrAssistantAdmin())
async def edit_company_password(message: types.Message, state: FSMContext):
    await state.set_state(CompanyEdit.password)
    back_btn = await back_button()
    await message.answer("🔐 Yangi API-parolni kiriting :", reply_markup=back_btn)


@dp.message(CompanyEdit.password, F.text.not_in(["⬅️ Orqaga"]))
async def category_password_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_password = message.text.strip()
    data = await state.get_data()
    company_id = data.get("company_id")

    try:
        updated = await update_company_password(session, company_id, new_password)

        if updated:
            await message.answer("✅ Kompaniya paroli yangilandi.")
        else:
            await message.answer("❌ Bunday paroli topilmadi.")

    except Exception as e:
        print(f"Error in Update Company login - {e}")
    await state.set_state(CompanyEdit.edit_menu)
    company_edit_btn = await company_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=company_edit_btn)