from aiogram.fsm.context import FSMContext
from aiogram import types, F
from sqlalchemy.ext.asyncio import AsyncSession
from loader import dp
from filters.admin_bot import IsBotOrAssistantAdmin
from keyboards.default.buttons import back_button, admin_confirm_button, company_crud_button
from states.my_states import CompanyAdd, CompanyState
from database.orm_query import (
    company_branches_link_exist, company_confirm_terminal_link_exist,
    orm_add_company
)
import httpx


@dp.message(F.text.in_(["🔖 Kompaniya qo'shish"]), IsBotOrAssistantAdmin())
async def category_add_func(message: types.Message, state: FSMContext):
    await state.set_state(CompanyAdd.branch_link)
    back_btn = await back_button()
    await message.answer(
        text="🔗 Filiallar ro'yxatini oluvchi API linkini kiriting",
        reply_markup=back_btn
    )


@dp.message(CompanyAdd.branch_link)
async def users_link(message: types.Message, state: FSMContext, session: AsyncSession):
    branch_url = message.text.strip()
    link_exist = await company_branches_link_exist(session, branch_url)
    back_btn = await back_button()
    if link_exist:
        await message.answer(
            "<i>❗️ Bu link oldin saqlangan!\nBoshqa kiriting.</i>",
            reply_markup=back_btn)
        return
    await state.update_data(branch_url=branch_url)
    await state.set_state(CompanyAdd.terminal_link)
    await message.answer(
        text="🔗 Kassalar ro'yxatini oluvchi API linkini kiriting",
        reply_markup=back_btn
    )


@dp.message(CompanyAdd.terminal_link)
async def confirm_transaction_link(message: types.Message, state: FSMContext, session: AsyncSession):
    terminals_url = message.text.strip()
    link_exist = await company_confirm_terminal_link_exist(session, terminals_url)
    back_btn = await back_button()
    if link_exist:
        await message.answer(
            "<i>❗️ Bu link oldin saqlangan!\nBoshqa kiriting.</i>",
            reply_markup=back_btn)
        return
    await state.update_data(terminals_url=terminals_url)
    await state.set_state(CompanyAdd.login)
    await message.answer("🔏 API loginini kiring.", reply_markup=back_btn)


@dp.message(CompanyAdd.login)
async def company_password(message: types.Message, state: FSMContext):
    login = message.text.strip()
    back_btn = await back_button()
    await state.update_data(login=login)
    await state.set_state(CompanyAdd.password)
    await message.answer("🔐 API parolini kiring.", reply_markup=back_btn)


@dp.message(CompanyAdd.password)
async def data_check(message: types.Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    confirm_btn = await admin_confirm_button()
    branch_url = data.get('branch_url')
    login = data.get('login')
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                branch_url,
                auth=(login, password)
            )
            response.raise_for_status()
            json_data = response.json()
            base_name = json_data.get("base_name")
    except Exception as e:
        await message.answer(f"Server xatosi: {e}")

    await state.update_data(password=password, name=base_name)
    text = (
        f"Kategoriya ma'lumotlari:\n"
        f"Kompaniya nomi: {base_name}\n"
        f"Filial URL: {data.get('branch_url')}\n"
        f"Terminal URL: {branch_url}\n"
        f"API login: {login}\n"
        f"API password: {password}\n\n"
        f"Barcha ma'lumotlar to'g'rimi?"
    )

    await message.answer(text=text, reply_markup=confirm_btn)
    await state.set_state(CompanyAdd.check)


@dp.message(F.text.in_(["✅Ha"]), CompanyAdd.check, IsBotOrAssistantAdmin())
async def confirm_company_add(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    company_menu_btn = await company_crud_button()
    try:
        await orm_add_company(session, data)
        await state.clear()
        await message.answer(
            "✅ Kompaniya saqlandi.", reply_markup=company_menu_btn
        )
        await state.set_state(CompanyState.main_menu)

    except Exception as e:
        print(f"Error while saving data: {e}")
        await message.answer(
            "❌ Kompaniya qo'shishda xatolik yuz berdi. Keyinroq urinib ko'ring."
        )


@dp.message(F.text.in_(["❌Yo'q"]), CompanyAdd.check, IsBotOrAssistantAdmin())
async def cancel_company_add(message: types.Message, state: FSMContext):
    company_menu_btn = await company_crud_button()
    await state.clear()
    await message.answer(
        "❗️ Kompaniya qo'shish bekor qilindi.", reply_markup=company_menu_btn)
    await state.set_state(CompanyState.main_menu)