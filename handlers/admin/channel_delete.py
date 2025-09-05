from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from filters.admin_bot import IsBotOrAssistantAdmin
from loader import dp
from database.orm_query import select_all_channels, delete_channel_by_id
from states.my_states import ChannelDeleteState, ChannelAdd


@dp.message(F.text.in_(["⚠️ Kanal o'chirish", "⚠️ Удалить канал"]), IsBotOrAssistantAdmin())
async def get_all_groups_handler(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.set_state(ChannelDeleteState.category)
    channels = await select_all_channels(session)

    if channels:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        for channel_id, category_id in channels:
            if category_id == 1:
                name = f"🛍 Buyurtmalar {channel_id}"
            else:
                name = f"📤 Reklama-post {channel_id}"
            button = InlineKeyboardButton(
                text=name,
                callback_data=f"del_category:{channel_id}"
            )
            keyboard.inline_keyboard.append([button])
            await state.update_data(category_id=category_id, channel_id=channel_id)
        await message.answer(
            "O'chirmoqchi bo'lgan kanalni tanlang.", reply_markup=keyboard
            )
    else:
        await message.answer(
            "❗️ Kanal ro'yxati bo'sh."
        )


@dp.callback_query(lambda call: call.data.startswith('del_category'), ChannelDeleteState.category)
async def confirm_delete_channel(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(ChannelDeleteState.channel_id)
    data = await state.get_data()
    channel_id = data.get('channel_id')
    category_id = data.get('category_id')
    await state.update_data(channel_id=channel_id)
    if category_id == 1:
        name = f"🛍 Buyurtmalar kanali\n{channel_id}"
    else:
        name = f"📤 Reklama-post kanali\n{channel_id}"
    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🫡 Ha, o'chirish", callback_data=f"channel_confirm_delete:{category_id}"),
                InlineKeyboardButton(text="🙃 Bekor qilish", callback_data="cancelchannel")
            ]
        ]
    )
    await call.message.edit_text(
        f"⚠️ Kanal o'chirishni tasdiqlaysizmi?\n\n{name}", reply_markup=confirm_keyboard
    )
    await call.answer()


@dp.callback_query(lambda call: call.data.startswith('channel_confirm_delete'), ChannelDeleteState.channel_id)
async def delete_channel(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(ChannelAdd.check.state)
    category_id = int(call.data.split(":")[1])
    data = await state.get_data()
    channel_id = data.get('channel_id')
    if category_id == 1:
        name = f"🛍 Buyurtmalar - {channel_id}"
    else:
        name = f"📤 Reklama-post - {channel_id}"
    try:
        await delete_channel_by_id(category_id=category_id, session=session)
        await call.message.edit_text(f"🫡 Kanal muvaffaqiyatli o'chirildi:\n{name}")
    except ValueError:
        await call.message.edit_text("😡 Xato: Kanal ID noto'g'ri formatda.")
    except Exception as e:
        await call.message.edit_text(f"🤯 Xato yuz berdi: {e}")
    await call.answer()


@dp.callback_query(lambda call: call.data == 'cancelchannel')
async def cancel_delete_channel(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(ChannelAdd.channel_menu.state)
    await call.message.edit_text("😁 Kanal o'chirish bekor qilindi.")