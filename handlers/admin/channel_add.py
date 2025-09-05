from aiogram.fsm.context import FSMContext
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from filters.admin_bot import IsBotOrAssistantAdmin
from keyboards.default.buttons import back_button, user_confirm_reply_btn, channel_crud
from states.my_states import ChannelAdd
from database.orm_query import create_or_update_channel
from loader import dp


@dp.message(F.text.in_(["📝 Kanal qo'shish"]), IsBotOrAssistantAdmin())
async def get_add_channel(message: types.Message, state: FSMContext):
    await state.set_state(ChannelAdd.category)
    category = [
        {1: "🛍 Buyurtmalar kanali"}, {2: "📤 Reklama-post kanali"}
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=name,
                callback_data=f"select_category:{category_id}"
            )
        ]
        for item in category
        for category_id, name in item.items()
    ])

    await message.answer(
        "Kanal qo'shish uchun kategoriyani  tanlang.", reply_markup=keyboard
    )


@dp.callback_query(F.data.startswith("select_category"), ChannelAdd.category)
async def channel_id_input(call: CallbackQuery, state: FSMContext):
    await state.set_state(ChannelAdd.channel_id)
    category_id = int(call.data.split(":")[1])
    await state.update_data(category_id=category_id)
    back_btn = await back_button()
    await call.message.answer(
        "Kanal 🆔sini kiriting.", reply_markup=back_btn
    )


@dp.message(ChannelAdd.channel_id)
async def set_channel_check(message: types.Message, state: FSMContext):
    await state.set_state(ChannelAdd.check)
    channel_id = int(message.text.strip())
    await state.update_data(channel_id=channel_id)
    data = await state.get_data()
    category_id = data.get('category_id')
    if category_id == 1:
        category_name = "🛍 Buyurtmalar kanali"
    else:
        category_name = "📤 Reklama-post kanali"

    reply_markup = await user_confirm_reply_btn()

    await message.answer(
        f"📣 {category_name}\n{channel_id}"
    )
    await message.answer("Barcha ma'lumotlar to'g'rimi?", reply_markup=reply_markup)


@dp.message(F.text.in_(["Ha", "Да"]), ChannelAdd.check, IsBotOrAssistantAdmin())
async def submit_channel(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    post_crud_btn = await channel_crud()
    await create_or_update_channel(session, data)
    await state.set_state(ChannelAdd.channel_menu.state)
    await message.answer("✅ Kanal saqlandi.", reply_markup=post_crud_btn)


@dp.message(F.text.in_(["Yo'q", "Нет"]), ChannelAdd.check, IsBotOrAssistantAdmin())
async def cancel_channel(message: types.Message, state: FSMContext):
    post_crud_btn = await channel_crud()
    await state.set_state(ChannelAdd.channel_menu.state)
    await message.answer("❌ Kanal qo'shish bekor qilindi.", reply_markup=post_crud_btn)





