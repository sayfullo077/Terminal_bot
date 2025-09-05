from aiogram.fsm.context import FSMContext
from aiogram import types, F
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.default.buttons import back_button, admins_crud_button
from database.orm_query import orm_select_one_branch_id_by_company_id, orm_admin_exist, orm_add_admin
from filters.admin_bot import IsBotOrAssistantAdmin
from states.my_states import AdminState
from loader import dp, bot
import logging


@dp.message(F.text.in_(["📝 Admin qo'shish"]), IsBotOrAssistantAdmin())
async def add_admin_func(message: types.Message, state: FSMContext):
    await state.set_state(AdminState.admin_get)
    back_btn = await back_button()
    await message.answer(
        text="<b>🆔 Admin kiriting: </b>", reply_markup=back_btn
    )


@dp.message(AdminState.admin_get)
async def admin_id_save(message: types.Message, state: FSMContext, session: AsyncSession):
    # Bu yerda tugma matnini tekshiramiz
    if message.text == "⬅️ Orqaga":
        await state.set_state(AdminState.admin_menu)
        admins_crud_btn = await admins_crud_button()
        await message.answer("Kerakli bo'limni tanlang!", reply_markup=admins_crud_btn)
        return

    try:
        admin_id = int(message.text.strip())
    except ValueError:
        await message.answer("<i>❗️ Iltimos, faqat raqam (Telegram ID) kiriting.</i>")
        return

    admins_crud_btn = await admins_crud_button()
    data = await state.get_data()
    company_id = data.get("company_id")
    branch_id = await orm_select_one_branch_id_by_company_id(company_id, session)

    try:
        if await orm_admin_exist(session, admin_id):
            back_btn = await back_button()
            await message.answer("<i>❗️ Bu admin qo'shilgan! Boshqa admin qo'shing!</i>", reply_markup=back_btn)
            return

        chat = await bot.get_chat(int(admin_id))
        full_name = chat.full_name

        await orm_add_admin(session=session, telegram_id=admin_id, full_name=full_name, branch_id=branch_id, company_id=company_id)
        await message.answer("<b>🥳 Admin muvaffaqiyatli qo'shildi !</b>", reply_markup=admins_crud_btn)
        await state.set_state(AdminState.admin_menu) # Yangi holatga o'tish

    except Exception as e:
        logging.exception(e)
        await message.answer("❗️ Admin qo'shishda kutilmagan xatolik yuz berdi.", reply_markup=admins_crud_btn)
        await state.set_state(AdminState.admin_menu) # Yangi holatga o'tish