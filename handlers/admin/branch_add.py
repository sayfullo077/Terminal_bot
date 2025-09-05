from aiogram.fsm.context import FSMContext
from aiogram import types, F
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from keyboards.default.buttons import admin_confirm_button, branch_crud_button, back_button
from states.my_states import BranchAdd, BranchState
from filters.admin_bot import IsBotOrAssistantAdmin
from loader import dp
from database.orm_query import (
    get_company_id_by_name, select_all_companies,
    cashier_link_exist, chief_cashier_link_exist, check_transaction_link_exist,
    orm_add_branch, pass_check_link_exist, transaction_link_exist, get_transaction_link_exist
)


@dp.message(F.text.in_(["🔖 Filial qo'shish"]), IsBotOrAssistantAdmin())
async def add_branch_func(message: types.Message, state: FSMContext, session: AsyncSession):
    companies = await select_all_companies(session)
    if companies:
        await state.set_state(BranchAdd.company)
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
        await state.set_state(BranchState.branch_menu)
        branch_crud_btn = await branch_crud_button()
        await message.delete()
        await message.answer(
            text="Kompaniyalar yo'q ❗️\nAvval kompaniya qo'shing.",
            reply_markup=branch_crud_btn
        )


@dp.message(BranchAdd.company)
async def select_company(message: types.Message, state: FSMContext, session: AsyncSession):
    name = message.text.strip()
    company_id = await get_company_id_by_name(session, name)
    await state.set_state(BranchAdd.name)
    await state.update_data(company_name=name, company_id=company_id)
    back_btn = await back_button()
    await message.answer("🏛 Filial nomini kiriting.", reply_markup=back_btn)


@dp.message(BranchAdd.name)
async def cashier_url(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    back_btn = await back_button()
    await message.answer("🔗 Kassir-URLini kiriting.", reply_markup=back_btn)
    await state.set_state(BranchAdd.cashier_url)


@dp.message(BranchAdd.cashier_url)
async def chief_cashier_url(message: types.Message, state: FSMContext, session: AsyncSession):
    cashiers_url = message.text.strip()
    link_exist = await cashier_link_exist(session, cashiers_url)
    if link_exist:
        back_btn = await back_button()
        await message.answer("<i>❗️ Bu link oldin saqlangan!\nBoshqa kiriting.</i>", reply_markup=back_btn)
        return
    await state.update_data(cashiers_url=cashiers_url)
    back_btn = await back_button()
    await message.answer("🔗 Bosh-kassir-URLini kiriting.", reply_markup=back_btn)
    await state.set_state(BranchAdd.chief_cashier_url)


@dp.message(BranchAdd.chief_cashier_url)
async def pass_check_url(message: types.Message, state: FSMContext, session: AsyncSession):
    chief_cashiers_url = message.text.strip()
    link_exist = await chief_cashier_link_exist(session, chief_cashiers_url)
    if link_exist:
        back_btn = await back_button()
        await message.answer("<i>❗️ Bu link oldin saqlangan!\nBoshqa kiriting.</i>", reply_markup=back_btn)
        return
    await state.update_data(chief_cashiers_url=chief_cashiers_url)
    back_btn = await back_button()
    await state.set_state(BranchAdd.check_pass_url)
    await message.answer("🔗 Parol tekshirish-URLini kiriting.", reply_markup=back_btn)


@dp.message(BranchAdd.check_pass_url)
async def transaction_url(message: types.Message, state: FSMContext, session: AsyncSession):
    check_pass_url = message.text.strip()
    link_exist = await pass_check_link_exist(session, check_pass_url)
    if link_exist:
        back_btn = await back_button()
        await message.answer("<i>❗️ Bu link oldin saqlangan!\nBoshqa kiriting.</i>", reply_markup=back_btn)
        return
    await state.update_data(check_pass_url=check_pass_url)
    back_btn = await back_button()
    await state.set_state(BranchAdd.transaction_url)
    await message.answer("🔗 Transaksiya URLini kiriting.", reply_markup=back_btn)


@dp.message(BranchAdd.transaction_url)
async def branch_login(message: types.Message, state: FSMContext, session: AsyncSession):
    transaction_url = message.text.strip()
    link_exist = await transaction_link_exist(session, transaction_url)
    if link_exist:
        back_btn = await back_button()
        await message.answer("<i>❗️ Bu link oldin saqlangan!\nBoshqa kiriting.</i>", reply_markup=back_btn)
        return
    await state.update_data(transaction_url=transaction_url)
    back_btn = await back_button()
    await state.set_state(BranchAdd.get_transaction_url)
    await message.answer("🔗 Transaksiya ro'yxatini oluvchi URLni kiriting.", reply_markup=back_btn)


@dp.message(BranchAdd.get_transaction_url)
async def branch_get_transaction_url(message: types.Message, state: FSMContext, session: AsyncSession):
    get_transaction_url = message.text.strip()
    link_exist = await get_transaction_link_exist(session, get_transaction_url)
    if link_exist:
        back_btn = await back_button()
        await message.answer("<i>❗️ Bu link oldin saqlangan!\nBoshqa kiriting.</i>", reply_markup=back_btn)
        return
    await state.update_data(get_transaction_url=get_transaction_url)
    back_btn = await back_button()
    await state.set_state(BranchAdd.check_transaction_url)
    await message.answer("🔗 Transaksiya tasdiqlovchi URLni kiriting.", reply_markup=back_btn)


@dp.message(BranchAdd.check_transaction_url)
async def branch_login(message: types.Message, state: FSMContext, session: AsyncSession):
    check_transaction_url = message.text.strip()
    link_exist = await check_transaction_link_exist(session, check_transaction_url)
    if link_exist:
        back_btn = await back_button()
        await message.answer("<i>❗️ Bu link oldin saqlangan!\nBoshqa kiriting.</i>", reply_markup=back_btn)
        return
    await state.update_data(check_transaction_url=check_transaction_url)
    await state.set_state(BranchAdd.login)
    back_btn = await back_button()
    await message.answer("🔐 API loginni kiring.", reply_markup=back_btn)


@dp.message(BranchAdd.login)
async def branch_password(message: types.Message, state: FSMContext):
    login = message.text.strip()
    await state.update_data(login=login)
    await state.set_state(BranchAdd.password)
    back_btn = await back_button()
    await message.answer("🔐 API parolini kiring.", reply_markup=back_btn)


@dp.message(BranchAdd.password)
async def data_check(message: types.Message, state: FSMContext):
    password = message.text.strip()
    await state.update_data(password=password)
    data = await state.get_data()
    confirm_btn = await admin_confirm_button()

    text = (
        f"Filial ma'lumotlari:\n"
        f"Kompaniya nomi: {data.get('company_name')}\n"
        f"Filial nomi: {data.get('name')}\n"
        f"Kassir url: {data.get('cashiers_url')}\n"
        f"Bos kassir url: {data.get('chief_cashiers_url')}\n"
        f"Parol tekshirish url: {data.get('check_pass_url')}\n"
        f"Transaksiya url: {data.get('transaction_url')}\n"
        f"Transaksiya list url: {data.get('get_transaction_url')}\n"
        f"Transaksiya check url: {data.get('check_transaction_url')}\n"
        f"API login: {data.get('login')}\n"
        f"API password: {password}\n\n"
        f"Barcha ma'lumotlar to'g'rimi?"
    )

    await message.answer(text=text, reply_markup=confirm_btn)
    await state.set_state(BranchAdd.check)


@dp.message(F.text.in_(["✅Ha"]), BranchAdd.check, IsBotOrAssistantAdmin())
async def confirm_branch_add(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    branch_crud_btn = await branch_crud_button()
    try:
        await orm_add_branch(session, data)
        await message.answer("✅ Filial saqlandi.", reply_markup=branch_crud_btn)
        await state.set_state(BranchState.branch_menu)
    except Exception as e:
        print(f"Error while saving data: {e}")
        await message.answer("❌ Filial qo'shishda xatolik yuz berdi. Keyinroq urinib ko'ring.")


@dp.message(F.text.in_(["❌Yo'q"]), BranchAdd.check, IsBotOrAssistantAdmin())
async def cancel_branch_add(message: types.Message, state: FSMContext):
    branch_crud_btn = await branch_crud_button()
    await state.set_state(BranchState.branch_menu)
    await message.answer("❗️ Filial qo'shish bekor qilindi.", reply_markup=branch_crud_btn)