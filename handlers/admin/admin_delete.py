from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from aiogram import types, F

from filters.admin_bot import IsBotOrAssistantAdmin
from loader import dp, bot
from states.my_states import AdminState
from database.orm_query import get_admin_users_by_company, orm_delete_admin_by_id
from html import escape


@dp.message(F.text.in_("⚠️ Adminlar o'chirish"), IsBotOrAssistantAdmin())
async def get_all_admins(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    company_id = data.get("company_id")

    try:
        admins = await get_admin_users_by_company(session, company_id)
        if admins:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])

            for admin_id in admins:
                print("Adminlar IDSi: ", admin_id)
                chat = await bot.get_chat(chat_id=admin_id)
                admin_full_name = chat.full_name
                button = InlineKeyboardButton(
                    text=f"🔰 {admin_full_name}",
                    callback_data=f"delete_admin:{admin_id}"
                )
                keyboard.inline_keyboard.append([button])

            await message.answer(
                text="O'chirmoqchi bo'lgan adminingizni tanlang:", reply_markup=keyboard)
        else:
            await message.answer(
                "❗️ Adminlar ro'yxati bo'sh.")

    except Exception as e:
        await message.answer(f"❗️ Xato yuz berdi admin olishda: {e}")


@dp.callback_query(lambda call: call.data.startswith('delete_admin:'))
async def confirm_delete_admin(call: types.CallbackQuery, session: AsyncSession):
    admin_id = call.data.split(":")[1]
    admin_id = str(admin_id)
    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🫡 Ha, o'chirish",
                                     callback_data=f"admin_confirm_delete:{admin_id}"),
                InlineKeyboardButton(text="🙃 Bekor qilish", callback_data="cancel")
            ]
        ]
    )
    await call.message.answer(
        f"⚠️ Adminni o'chirishni tasdiqlaysizmi?\n 🆔 {admin_id}", reply_markup=confirm_keyboard
    )
    await call.answer()


@dp.callback_query(lambda call: call.data.startswith('admin_confirm_delete:'))
async def delete_admin(call: types.CallbackQuery, session: AsyncSession):
    admin_id = int(call.data.split(":")[1])

    try:
        await orm_delete_admin_by_id(session, admin_id)
        message = (
            f"☑️ Admin muvaffaqiyatli o'chirildi:\n🆔 {admin_id}"
        )
    except ValueError as ve:
        message = f" Xato: {ve}"

    except Exception as e:
        message = (
            f"❗️ Xato yuz berdi admin o'chirishda: {e}"
        )
    safe_message = escape(message)
    await call.message.answer(safe_message, parse_mode="HTML")
    await call.answer()


@dp.callback_query(lambda call: call.data == 'cancel')
async def cancel_delete(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.admin_menu)
    await call.message.answer("✖️ Admin o'chirish bekor qilindi.")
