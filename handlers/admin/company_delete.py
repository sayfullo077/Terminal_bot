from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton
from aiogram import types, F
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from loader import dp
from filters.admin_bot import IsBotOrAssistantAdmin
from keyboards.default.buttons import company_crud_button, admin_confirm_button
from states.my_states import CompanyState
from database.orm_query import select_all_companies, delete_company_by_name


@dp.message(F.text.in_(["⚠️ Kompaniya o'chirish"]), IsBotOrAssistantAdmin())
async def company_delete_func(message: types.Message, state: FSMContext, session: AsyncSession):
    companies = await select_all_companies(session)
    if companies:
        await state.set_state(CompanyState.delete)
        keyboard = ReplyKeyboardBuilder()
        for company in companies:
            button = KeyboardButton(text=company.name)
            keyboard.add(button)
        keyboard.adjust(2)
        back_btn = KeyboardButton(text="⬅️ Orqaga")
        keyboard.row(back_btn)
        await message.delete()
        await message.answer(
            text="Qaysi kompaniyani o'chirmoqchisiz",
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


@dp.message(CompanyState.delete)
async def select_company_list(message: types.Message, state: FSMContext):
    await state.set_state(CompanyState.check)
    name = message.text.strip()
    await state.update_data(name=name)
    confirm_btn = await admin_confirm_button()
    await message.answer(
        text=f"{name}ni o'chirishni tasdiqlaysizmi?",
        reply_markup=confirm_btn
    )


@dp.message(F.text.in_(["✅Ha"]), CompanyState.check, IsBotOrAssistantAdmin())
async def confirm_delete(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    name = data.get('name')
    company_menu_btn = await company_crud_button()
    try:
        await delete_company_by_name(session, name)
        await message.answer(
            "✅ Kompaniya o'chirildi.", reply_markup=company_menu_btn
        )
        await state.set_state(CompanyState.main_menu)

    except Exception as e:
        print(f"Error while saving data: {e}")
        await message.answer(
            "❌ Kompaniya o'chirishda xatolik yuz berdi. Keyinroq urinib ko'ring."
        )


@dp.message(F.text.in_(["❌Yo'q"]), CompanyState.check, IsBotOrAssistantAdmin())
async def cancel_delete(message: types.Message, state: FSMContext):
    company_menu_btn = await company_crud_button()
    await state.set_state(CompanyState.main_menu)
    await message.answer(
        "❗️ Kompaniya o'chirish bekor qilindi.", reply_markup=company_menu_btn)