from loader import dp, bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import or_f
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from keyboards.inline.buttons import position_button, back_button, cashier_menu_button
from states.my_states import UserStart, TransactionState
from database.orm_query import select_user, get_company_url_by_id, get_terminals_url_by_id, has_pending_transaction
from .feedback import UserMessageState
import re
import httpx


def html_escape(text):
    escape_chars = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}
    return re.sub(r'[&<>"\']', lambda match: escape_chars[match.group(0)], text)


@dp.callback_query(F.data.startswith("back"), or_f(TransactionState.transfer_comment, TransactionState.transfer_photo, UserMessageState.waiting_for_message, UserStart.cash_detail, TransactionState.comment, UserStart.company, UserStart.start, UserStart.branch, UserStart.password, UserStart.selected_user, UserStart.cashier_menu, TransactionState.transaction_menu, TransactionState.transfer_amount))
async def transaction_func(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    telegram_id = call.from_user.id
    full_name = html_escape(call.from_user.full_name)
    if current_state in [
        UserStart.company,
        UserStart.cashier_menu,
        TransactionState.transaction_menu,
        UserMessageState.waiting_for_message
        ]:
        await state.set_state(UserStart.start)
        user = await select_user(telegram_id, session)
        if user is not None:
            cashier_menu_btn = await cashier_menu_button()
            await call.message.edit_text(
                f"Menyuni tanlang", reply_markup=cashier_menu_btn
            )
        else:
            await call.message.edit_text(
                f"Assalomu alaykum {full_name}\nIltimos Bosh ofis nomini kiriting:"
            )

    elif current_state in [
        UserStart.selected_user,
        UserStart.branch,
        ]:
        data = await state.get_data()
        company_id = data.get("company_id")
        company_data = await get_company_url_by_id(session, company_id)
        if not company_data:
            await call.message.edit_text("❌ Bunday kompaniya topilmadi")
            return

        branch_url, login, password = company_data

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(branch_url, auth=(login, password))
                response.raise_for_status()
                data = response.json()
            branches = data.get("response", [])

            if not branches:
                await call.message.edit_text("❌ Filiallar topilmadi")
                return
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=branch["name"],
                            callback_data=f"branch_{branch['id']}"
                        )
                    ]
                    for branch in branches
                ]
            )
            await call.message.edit_text("🏛 Filialni tanlang", reply_markup=keyboard)
        except Exception as e:
            print(f"Error on branch URL: {e}")
            await call.message.edit_text("❌ Filiallarni olishda xatolik yuz berdi")
        await state.set_state(UserStart.company)

    elif current_state == UserStart.password:
        position_btn = await position_button()
        await call.message.edit_text("Iltimos lavozimni tanlang:", reply_markup=position_btn)
        await state.set_state(UserStart.branch)

    elif current_state == TransactionState.transfer_amount:
        user = await select_user(telegram_id, session)

        if not user:
            await call.message.edit_text("❗️ Foydalanuvchi topilmadi")
            return

        user_id = user.user_1c_id
        branch_id = user.branch_id
        company_id = user.company_id
        full_name = user.full_name

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

            await state.update_data(all_cash=all_cash, all_terminal=all_terminal, branch_id=branch_id,
                                    company_id=company_id, full_name=full_name)

            keyboard_buttons = []

            for cash in all_cash:
                keyboard_buttons.append(
                    [InlineKeyboardButton(
                        text=f"💵 {cash['cash_name']}",
                        callback_data=f"cash_naqd:{cash['cash_id']}"
                    )]
                )

            for terminal in all_terminal:
                keyboard_buttons.append(
                    [InlineKeyboardButton(
                        text=f"💳 {terminal['cash_name']}",
                        callback_data=f"cash_terminal:{terminal['cash_id']}"
                    )]
                )

            keyboard_buttons.append([InlineKeyboardButton(text="◁ Orqaga", callback_data="back")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

            await call.message.edit_text(f"❖ Kassani tanlang:", reply_markup=keyboard)

        except httpx.HTTPStatusError as e:
            await call.message.edit_text(f"❗️ Server xatosi: {e.response.status_code}")
        except httpx.RequestError:
            await call.message.edit_text("❗️ Serverga ulanib bo'lmadi")
        except Exception as e:
            await call.message.edit_text("❗️ Kassalarni olishda xatolik yuz berdi")
            print(f"Unexpected error: {e}")

        await state.set_state(TransactionState.transaction_menu)

    elif current_state == TransactionState.transfer_photo:
        data = await state.get_data()
        source_cash_name = data.get('source_cash_name')
        source_cash_balance = data.get('source_cash_balance')
        source_cash_type = data.get('source_cash_type')
        back_btn = await back_button()

        text = (

            f"❖ Kassa: <b>{source_cash_name}</b>\n\n"
            f"﹩ Balans: <b>{source_cash_balance:,} so'm</b>\n\n"
            f"⑆ Turi: <b>{'Terminal' if source_cash_type == 'cash_terminal' else 'Naqd pul'}</b>\n"
            f"- - - - - - - - - - - - - - - - - - - - - - - -\n\n"
            f"＄<i> Pul miqdorini kiriting?</i>"

        )

        msg = await call.message.edit_text(text, reply_markup=back_btn)
        await state.update_data(last_msg=msg.message_id)
        await state.set_state(TransactionState.transfer_amount)

    elif current_state == TransactionState.comment:
        data = await state.get_data()
        source_cash_name = data.get('source_cash_name')
        source_cash_type = data.get('source_cash_type')
        transfer_amount = data.get('transfer_amount')
        back_btn = await back_button()

        text = (
            f"❖ Kassa: <b>{source_cash_name}</b>\n\n"
            f"＄ Miqdori: <b>{transfer_amount:,} so'm</b>\n\n"
            f"⑆ Turi: <b>{'Terminal' if source_cash_type == 'cash_terminal' else 'Naqd pul'}</b>\n\n"
            f"- - - - - - - - - - - - - - - - - - - - - - - -\n\n"
            f"<i>📸 Chekni rasmga olib yuboring:</i>"
        )

        msg = await call.message.edit_text(text, reply_markup=back_btn)
        await state.update_data(last_msg=msg.message_id)
        await state.set_state(TransactionState.transfer_photo)

    elif current_state == TransactionState.transfer_comment:
        data = await state.get_data()
        last_msg_id = data.get("last_msg")

        if last_msg_id:
            try:
                await bot.edit_message_reply_markup(chat_id=call.chat.id, message_id=last_msg_id, reply_markup=None)
            except:
                pass

        await state.set_state(TransactionState.transfer_photo)
        back_btn = await back_button()
        await call.message.edit_text("Chekni rasmga olib yuboring:", reply_markup=back_btn)

    elif current_state == UserStart.cash_detail:
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

            await state.update_data(all_cash=all_cash, all_terminal=all_terminal)

            keyboard_buttons = []

            for cash in all_cash:
                keyboard_buttons.append(
                    [InlineKeyboardButton(
                        text=f"💵 {cash['cash_name']}",
                        callback_data=f"cash_naqd:{cash['cash_id']}"
                    )]
                )

            for terminal in all_terminal:
                keyboard_buttons.append(
                    [InlineKeyboardButton(
                        text=f"💳 {terminal['cash_name']}",
                        callback_data=f"cash_terminal:{terminal['cash_id']}"
                    )]
                )

            keyboard_buttons.append([InlineKeyboardButton(text="◁ Orqaga", callback_data="back")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

            await call.message.edit_text("❖ Kassani tanlang:", reply_markup=keyboard)

        except httpx.HTTPStatusError as e:
            await call.message.edit_text(f"❗️ Server xatosi: {e.response.status_code}")
        except httpx.RequestError:
            await call.message.edit_text("❗️ Serverga ulanib bo‘lmadi")
        except Exception as e:
            await call.message.edit_text("❗️ Kassalarni olishda xatolik yuz berdi")
            print(f"Unexpected error: {e}")

        await state.set_state(UserStart.cashier_menu)



