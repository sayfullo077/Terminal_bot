from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton


from aiogram import types, F
from sqlalchemy.ext.asyncio import AsyncSession

from loader import dp
from filters.admin_bot import IsBotOrAssistantAdmin
from states.my_states import (
    TransferState
)
from keyboards.default.buttons import (
    branch_crud_button
)
from keyboards.inline.buttons import create_pagination_keyboard
from database.orm_query import (
    select_user, get_transactions_by_company_id
)


@dp.message(F.text.in_(["📋 Sverkalar ro'yxati"]), IsBotOrAssistantAdmin())
async def transaction_list_func(message: types.Message, state: FSMContext, session: AsyncSession):
    telegram_id = message.from_user.id
    user = await select_user(telegram_id, session)

    if not user:
        await message.answer("Foydalanuvchi topilmadi.")
        return

    company_id = user.company_id
    transactions = await get_transactions_by_company_id(session, company_id)

    if not transactions:
        # Paginatsiya uchun bo'sh ro'yxatni saqlash ma'nosiz
        await message.delete()
        await message.answer(
            text="Sverkalar yo'q ❗️\nAvval sverka qo'shing.",
            reply_markup=await branch_crud_button()
        )
        await state.clear()  # Agar oldingi holatlar bo'lsa, tozalash
        return

    # Tranzaksiyalar ro'yxatini va joriy sahifani stateda saqlash
    # Shu ro'yxat keyingi so'rovlar uchun ishlatiladi
    await state.set_data({"transactions": transactions, "page": 0})

    keyboard = create_pagination_keyboard(transactions, 0)

    await message.delete()
    await message.answer(
        text="Sverkani tanlang:",
        reply_markup=keyboard
    )


# Paginatsiya tugmalarini boshqaruvchi handler
@dp.callback_query(F.data.startswith("page:"))
async def paginate_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    transactions = data.get("transactions")

    if not transactions:
        await callback_query.answer("Ma'lumotlar topilmadi.", show_alert=True)
        return

    # Yangi sahifa raqamini olish
    new_page = int(callback_query.data.split(":")[1])

    # Yangi klaviaturani yaratish
    new_keyboard = create_pagination_keyboard(transactions, new_page)

    # Joriy xabarning klaviaturasini o'zgartirish
    await callback_query.message.edit_reply_markup(reply_markup=new_keyboard)

    await state.update_data(page=new_page)
    await callback_query.answer()


# Tranzaksiya detallarini ko'rsatish uchun handler
@dp.callback_query(F.data.startswith("view_transaction:"))
async def view_transaction_details(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    transactions = data.get("transactions")

    if not transactions:
        await callback_query.answer("Ma'lumot topilmadi.", show_alert=True)
        return

    # Callback datadan tranzaksiya ID'sini olish
    transaction_id = int(callback_query.data.split(":")[1])

    # Ro'yxatdan tranzaksiyani topish
    transaction = next((tx for tx in transactions if tx.id == transaction_id), None)

    if transaction:
        # Batafsil ma'lumotni yuborish
        message_text = (
            f"<b>Sverka №{transaction.transaction_id}</b>\n\n"
            f"<b>Summa:</b> {transaction.amount} so'm\n"
            f"<b>Status:</b> {transaction.status_type.value}\n"
            f"<b>Jo'natuvchi:</b> {transaction.sender_terminal_name}\n"
            f"<b>Qabul qiluvchi:</b> {transaction.receiver_terminal_name}\n"
        )
        await callback_query.message.answer(text=message_text, parse_mode='HTML')
        await callback_query.answer()
    else:
        await callback_query.answer("Tranzaksiya topilmadi.", show_alert=True)