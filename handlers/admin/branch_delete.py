from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton
from aiogram import types, F
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from loader import dp
from filters.admin_bot import IsBotOrAssistantAdmin
from keyboards.default.buttons import admin_confirm_button, branch_crud_button
from states.my_states import BranchState
from database.orm_query import select_all_companies, delete_branch_by_name, get_company_id_by_name, get_branch_by_company_id


@dp.message(F.text.in_(["⚠️ Filial o'chirish"]), IsBotOrAssistantAdmin())
async def company_list_func(message: types.Message, state: FSMContext, session: AsyncSession):
    companies = await select_all_companies(session)
    if companies:
        await state.set_state(BranchState.company)
        keyboard = ReplyKeyboardBuilder()
        for company in companies:
            button = KeyboardButton(text=company.name)
            keyboard.add(button)
        keyboard.adjust(2)
        back_btn = KeyboardButton(text="⬅️ Orqaga")
        keyboard.row(back_btn)
        await message.answer(
            text="Kompaniyani tanlang !",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
    else:
        await state.set_state(BranchState.branch_menu)
        branch_crud_btn = await branch_crud_button()
        await message.answer(
            text="Kompaniyalar yo'q ❗️\nAvval kompaniya qo'shing.",
            reply_markup=branch_crud_btn
        )


@dp.message(BranchState.company)
async def select_branch(message: types.Message, state: FSMContext, session: AsyncSession):
    name = message.text.strip()
    company_id = await get_company_id_by_name(session, name)
    branches = await get_branch_by_company_id(session, company_id)
    if branches:
        await state.set_state(BranchState.list)
        keyboard = ReplyKeyboardBuilder()
        for branch in branches:
            button = KeyboardButton(text=branch.name)
            keyboard.add(button)
        keyboard.adjust(2)
        back_btn = KeyboardButton(text="⬅️ Orqaga")
        keyboard.row(back_btn)
        await message.answer(
            text="Filialni tanlang:",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
    else:
        await state.set_state(BranchState.branch_menu)
        branch_crud_btn = await branch_crud_button()
        await message.answer(
            text="Filiallar yo'q ❗️\nAvval filial qo'shing.",
            reply_markup=branch_crud_btn
        )


@dp.message(BranchState.list)
async def delete_branch(message: types.Message, state: FSMContext):
    await state.set_state(BranchState.check)
    name = message.text.strip()
    await state.update_data(name=name)
    confirm_btn = await admin_confirm_button()
    await message.answer(
        text=f"{name}ni o'chirishni tasdiqlaysizmi?",
        reply_markup=confirm_btn
    )


@dp.message(F.text.in_(["✅Ha"]), BranchState.check, IsBotOrAssistantAdmin())
async def confirm_delete_branch(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    name = data.get('name')
    branch_menu_btn = await branch_crud_button()
    try:
        await delete_branch_by_name(session, name)
        await message.answer(
            "✅ Filial o'chirildi.", reply_markup=branch_menu_btn
        )
        await state.set_state(BranchState.branch_menu)

    except Exception as e:
        print(f"Error while saving data: {e}")
        await message.answer(
            "❌ Filial o'chirishda xatolik yuz berdi. Keyinroq urinib ko'ring."
        )


@dp.message(F.text.in_(["❌Yo'q"]), BranchState.check, IsBotOrAssistantAdmin())
async def cancel_delete_branch(message: types.Message, state: FSMContext):
    branch_menu_btn = await branch_crud_button()
    await state.set_state(BranchState.branch_menu)
    await message.answer(
        "❗️ Kompaniya o'chirish bekor qilindi.", reply_markup=branch_menu_btn)