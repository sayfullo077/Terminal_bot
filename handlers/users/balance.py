from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types, F
from loader import dp
from states.my_states import BalanceState
from database.orm_query import select_user, get_terminals_url_by_id
from keyboards.inline.buttons import build_balance_pagination_keyboard
import httpx


@dp.callback_query(F.data.startswith("balance_info"))
async def balance_info(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    telegram_id = call.from_user.id
    user = await select_user(telegram_id, session)

    if not user:
        await call.message.edit_text("❗️ Foydalanuvchi topilmadi")
        return

    user_id = user.user_1c_id
    branch_id = user.branch_id
    company_id = user.company_id

    terminals_data = await get_terminals_url_by_id(session, company_id)
    if not terminals_data:
        await call.message.edit_text("❗️ Kassalar URL topilmadi")
        return

    terminals_url, login, password = terminals_data

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                terminals_url,
                params={"branch_id": branch_id, "user_id": user_id},
                auth=(login, password),
            )
            response.raise_for_status()
            data = response.json()

        all_cash = data.get("cash", [])
        all_terminal = data.get("terminal", [])

        if not (all_cash or all_terminal):
            await call.message.edit_text("❗️ Kassalar topilmadi")
            return

        await state.update_data(all_cash=all_cash, all_terminal=all_terminal, current_page=1)

        # Paginatsiya bilan keyboard yaratish
        keyboard = build_balance_pagination_keyboard(all_cash, all_terminal, page=1, per_page=7)

        await call.message.edit_text("❖ Kassani tanlang:", reply_markup=keyboard)

    except httpx.HTTPStatusError as e:
        await call.message.edit_text(f"❗️ Server xatosi: {e.response.status_code}")
    except httpx.RequestError:
        await call.message.edit_text("❗️ Serverga ulanib bo‘lmadi")
    except Exception as e:
        await call.message.edit_text("❗️ Kassalarni olishda xatolik yuz berdi")
        print(f"Unexpected error: {e}")

    await state.set_state(BalanceState.balance_pagination)


@dp.callback_query(F.data.startswith("balance_page:"), BalanceState.balance_pagination)
async def handle_balance_pagination(call: types.CallbackQuery, state: FSMContext):
    """Balance kassalar paginatsiyasini boshqarish"""
    try:
        page = int(call.data.split(":")[1])
        data = await state.get_data()
        all_cash = data.get("all_cash", [])
        all_terminal = data.get("all_terminal", [])
        
        # Yangi keyboard yaratish
        keyboard = build_balance_pagination_keyboard(all_cash, all_terminal, page=page, per_page=7)
        
        # State ma'lumotlarini yangilash
        await state.update_data(current_page=page)
        
        # Xabarni yangilash
        await call.message.edit_text("❖ Kassani tanlang:", reply_markup=keyboard)
        
    except (ValueError, IndexError):
        await call.answer("❗️ Sahifa raqami noto'g'ri", show_alert=True)
    except Exception as e:
        print(f"Balance pagination error: {e}")
        await call.answer("❗️ Xatolik yuz berdi", show_alert=True)


@dp.callback_query(F.data.startswith(("balance_naqd:", "balance_terminal:")), BalanceState.balance_pagination)
async def balance_cash_detail(call: types.CallbackQuery, state: FSMContext):
    data_parts = call.data.split(":")
    cash_type = data_parts[0]
    cash_id = int(data_parts[1])

    data = await state.get_data()

    if cash_type == "balance_naqd":
        all_cash = data.get("all_cash", [])
        cash_info = next((c for c in all_cash if c["cash_id"] == cash_id), None)
    elif cash_type == "balance_terminal":
        all_terminal = data.get("all_terminal", [])
        cash_info = next((c for c in all_terminal if c["cash_id"] == cash_id), None)
    else:
        await call.message.edit_text("❗️ Noma'lum kassa turi")
        return

    if not cash_info:
        await call.message.edit_text("❗️ Kassa topilmadi")
        return

    back_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◁ Orqaga", callback_data="back")]
        ]
    )

    text = (
        f"❖ Kassa: <b>{cash_info['cash_name']}</b>\n"
        f"﹩ Balans: <b>{cash_info['balance']:,} so'm</b>\n"
        f"№ Kassa ID: <code>{cash_info['cash_id']}</code>"
    )

    await call.message.edit_text(text, reply_markup=back_btn)
    await state.set_state(BalanceState.balance_detail)
