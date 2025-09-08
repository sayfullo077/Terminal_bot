from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import types, F
from aiogram.filters import or_f
from loader import dp, bot
from aiogram.types import ContentType
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.password_generator import generate_unique_number
from keyboards.inline.buttons import chief_cashier_menu_button, create_pagination_keyboard, cashier_menu_button, user_confirm_button, cashier_confirm_button
from states.my_states import UserStart, TransactionState
from database.orm_query import (
    select_user, get_pending_transactions_by_company_id, get_company_name_by_id, get_terminals_url_by_id,
    orm_add_transaction, get_user_full_name_by_id, delete_transaction_by_id,
    get_chief_cashier_users, orm_complete_transaction, get_transaction_by_id, get_branch_transaction_url_by_id,
    has_pending_transaction, get_branch_get_transaction_url_by_id, get_branch_confirm_transaction_url_by_id,
)
import decimal
import httpx


@dp.callback_query(F.data.startswith("cash_list"))
async def chief_transaction_list(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    telegram_id = call.from_user.id
    user = await select_user(telegram_id, session)

    if not user:
        await call.message.delete()
        await call.message.answer("❗️ Foydalanuvchi topilmadi")
        return

    company_id = user.company_id
    chief_cashier_menu_btn = await chief_cashier_menu_button()
    transactions = await get_pending_transactions_by_company_id(session, company_id)
    if not transactions:
        await call.message.delete()
        await call.message.answer(
            text="Tasdiqlanadigan sverkalar yo'q ❗",
            reply_markup=chief_cashier_menu_btn
        )
        await state.clear()
        return

    await state.set_data({"transactions": transactions, "page": 0})

    keyboard = create_pagination_keyboard(transactions, 0)

    await call.message.edit_text(
        text="Sverkani tanlang:",
        reply_markup=keyboard
    )
    await state.set_state(TransactionState.pending_chief_cashier)


@dp.callback_query(F.data.startswith("page:"), TransactionState.pending_chief_cashier)
async def paginate_callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(TransactionState.select_cash)
    data = await state.get_data()
    transactions = data.get("transactions")

    if not transactions:
        await callback_query.answer("Ma'lumotlar topilmadi.", show_alert=True)
        return

    new_page = int(callback_query.data.split(":")[1])
    new_keyboard = create_pagination_keyboard(transactions, new_page)
    await callback_query.message.edit_reply_markup(reply_markup=new_keyboard)

    await state.update_data(page=new_page)
    await callback_query.answer()


@dp.callback_query(F.data.startswith("view_transaction:"), TransactionState.select_cash)
async def view_transaction_details(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(TransactionState.confirm)
    data = await state.get_data()
    transactions = data.get("transactions")

    if not transactions:
        await callback_query.answer("Ma'lumot topilmadi.", show_alert=True)
        return

    transaction_id = int(callback_query.data.split(":")[1])
    transaction = next((tx for tx in transactions if tx.id == transaction_id), None)

    if transaction:
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