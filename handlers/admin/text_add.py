from aiogram import types, F, html
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.default.buttons import back_button, admin_button
from keyboards.inline.buttons import format_btn, TextFormatCallBack
from states.my_states import TextAdd
from filters.admin_bot import IsBotOrAssistantAdmin
from helper import check_url
from loader import dp, bot
from database.orm_query import select_all_users, select_user, select_all_order_users


@dp.message(F.text == '📝 Text', IsBotOrAssistantAdmin())
async def get_format_text(message: types.Message, state: FSMContext):
    back_btn = await back_button()
    await message.answer(
        text=html.bold("Post textini yuboring."),
        reply_markup=back_btn
    )
    await message.answer(
        "Post sozlamalari:",
        reply_markup=format_btn(format='TEXT')
    )
    await state.set_state(TextAdd.text)


@dp.callback_query(TextFormatCallBack.filter())
async def change_format_text(call: types.CallbackQuery, callback_data: TextFormatCallBack, state: FSMContext):
    format = callback_data.format
    await state.update_data({
        'format': format
    })
    await call.message.edit_reply_markup(reply_markup=format_btn(format='text' if format == 'html' else 'html'))


@dp.message(TextAdd.text, IsBotOrAssistantAdmin())
async def get_text(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        await state.update_data({
            'text': message.text
        })
        text = "Havolani quyidagi formatda yuboring :\n" \
               "[tugma matni + havola]\n" \
               "Misol :\n" \
               "[Tarjimon+https://t.me/Sayfulloh_Mamatqulov]\n" \
               "Bir qatorga bir nechta tugmalar qo'shish uchun yangi qatordan yozing.\n" \
               "Format :\n" \
               "[Birinchi matn + birinchi havola]\n" \
               "[Ikkinchi matn + ikkinchi havola]"

        get_before_btn = await back_button()
        await message.answer(text, reply_markup=get_before_btn)
        await state.set_state(TextAdd.url)

    else:
        await message.answer(html.bold("Post textini yuboring!"))
        await message.answer("Post sozlamalari :", reply_markup=format_btn(format='TEXT'))
        await state.set_state(TextAdd.text)


@dp.message(F.text.in_(["Davom etish ➡️", "Продолжить ➡️"]), TextAdd.url, IsBotOrAssistantAdmin())
async def check_confirm(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await message.answer(text=data['text'])
    send_btn = await back_button()
    await message.answer("Agar tayyor bo'lsa '📤 Yuborish' tugmasini bosing.", reply_markup=send_btn)
    await state.set_state(TextAdd.send)


@dp.message(TextAdd.url, IsBotOrAssistantAdmin())
async def get_url(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.content_type == 'text':
        await message.answer(message.text)
        urls = check_url(text=message.text)
        urls = urls if urls else None
        await state.update_data({
            'buttons': urls
        })
        data = await state.get_data()
        btn = InlineKeyboardBuilder()
        await message.answer(text=data['text'], reply_markup=btn.as_markup())
        send_btn = await back_button()
        await message.answer("Agar tayyor bo'lsa '📤 Yuborish' tugmasini bosing.", reply_markup=send_btn)
        await state.set_state(TextAdd.send)

    else:

        text = "Havolani quyidagi formatda yuboring :\n" \
               "[tugma matni + havola]\n" \
               "Misol :\n" \
               "[Tarjimon+https://t.me/Sayfulloh_Mamatqulov]\n" \
               "Bir qatorga bir nechta tugmalar qo'shish uchun yangi qatordan yozing.\n" \
               "Format :\n" \
               "[Birinchi matn + birinchi havola]\n" \
               "[Ikkinchi matn + ikkinchi havola]"

        get_before_btn = await back_button()
        await message.answer(text, reply_markup=get_before_btn)
        await state.set_state(TextAdd.url)


@dp.message(F.text.in_(["📤 Yuborish", "📤 Отправить"]), TextAdd.send, IsBotOrAssistantAdmin())
async def send_add(message: types.Message,  session: AsyncSession, state: FSMContext):
    await state.set_state(TextAdd.check)
    text = "Kimlar uchun text xabarini yubormoqchisiz?"
    send_btn = await back_button()
    await message.answer(text=text, reply_markup=send_btn)


@dp.message(F.text.in_(["Buyurtma berganlar ✅", "Те, кто сделали заказ ✅"]), TextAdd.check, IsBotOrAssistantAdmin())
async def send_to_order_users(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    users = await select_all_order_users(session)
    admin_btn = await admin_button()
    if users:
        if data.get('buttons', None):
            links = data['buttons'].splitlines()
            btn = InlineKeyboardBuilder()
            for link in links:
                manzil = link[link.rfind('+') + 1:].strip()
                text = link[:link.rfind('+')].strip()
                btn.button(text=text, url=manzil)
            btn.adjust(1)
            counter = 0
            for i in users:
                try:
                    await bot.send_message(text=data['text'], chat_id=i.user_id, reply_markup=btn.as_markup(row_width=1))
                    counter += 1

                except Exception as e:
                    print(e)
            await message.answer(f"Buyurtma bergan {counter}ta obunachiga xabar yuborildi!", reply_markup=admin_btn)
        else:
            text = data['text']
            counter = 0
            for i in users:
                try:
                    await bot.send_message(text=text, chat_id=i.user_id)
                    counter += 1
                except Exception as e:
                    print(e)

            await message.answer(f"Buyurtma bergan {counter}ta obunachiga xabar yuborildi!", reply_markup=admin_btn)
        await state.clear()
    else:
        await message.answer("Buyurtma bergan foydalanuvchilar majud emas !", reply_markup=admin_btn)
        await state.clear()


@dp.message(F.text.in_(["Buyurtma bermaganlar ❌", "Те, кто не заказывал ❌"]), TextAdd.check, IsBotOrAssistantAdmin())
async def send_to_no_order_users(message: types.Message, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    user = await select_user(telegram_id=user_id, session=session)
    language = user.languages
    data = await state.get_data()
    users = ""
    admin_btn = await admin_button()
    if users:
        if data.get('buttons', None):
            links = data['buttons'].splitlines()
            btn = InlineKeyboardBuilder()
            for link in links:
                manzil = link[link.rfind('+') + 1:].strip()
                text = link[:link.rfind('+')].strip()
                btn.button(text=text, url=manzil)
            btn.adjust(1)
            counter = 0
            for i in users:
                try:
                    await bot.send_message(text=data['text'], chat_id=12345, reply_markup=btn.as_markup(row_width=1))
                    counter += 1

                except Exception as e:
                    print(e)
            await message.answer(f"Buyurtma bermagan {counter}ta obunachiga xabar yuborildi!" if language == 'uz' else
                                 f"Сообщение отправлено подписчикам {counter}, которые не оформили заказ!",
                                 reply_markup=admin_btn)
        else:
            text = data['text']
            counter = 0
            for i in users:
                try:
                    await bot.send_message(text=text, chat_id=12345)
                    counter += 1
                except Exception as e:
                    print(e)

            await message.answer(f"Buyurtma bermagan {counter}ta obunachiga xabar yuborildi!" if language == 'uz' else
                                 f"Сообщение отправлено подписчикам {counter}, которые не оформили заказ!",
                                 reply_markup=admin_btn)
        await state.clear()
    else:
        await message.answer("Buyurtma bermagan foydalanuvchilar majud emas !" if language == 'uz' else
                             "Пользователи, не оформившие заказ, недоступны!", reply_markup=admin_btn)
        await state.clear()


@dp.message(F.text.in_(["Hamma uchun 👨‍👦‍👦", "Для всех 👨‍👦‍👦"]), TextAdd.check, IsBotOrAssistantAdmin())
async def send_to_all_users(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    users = await select_all_users(session)
    admin_btn = await admin_button()
    if users:
        if data.get('buttons', None):
            links = data['buttons'].splitlines()
            btn = InlineKeyboardBuilder()
            for link in links:
                manzil = link[link.rfind('+') + 1:].strip()
                text = link[:link.rfind('+')].strip()
                btn.button(text=text, url=manzil)
            btn.adjust(1)
            counter = 0
            for i in users:
                try:
                    await bot.send_message(text=data['text'], chat_id=i.user_id,
                                           reply_markup=btn.as_markup(row_width=1))
                    counter += 1

                except Exception as e:
                    print(e)
            await message.answer(f"{counter}ta obunachiga xabar yuborildi!", reply_markup=admin_btn)
        else:
            text = data['text']
            counter = 0
            for i in users:
                try:
                    await bot.send_message(text=text, chat_id=i.user_id)
                    counter += 1
                except Exception as e:
                    print(e)

            await message.answer(f"{counter}ta obunachiga xabar yuborildi!", reply_markup=admin_btn)
        await state.clear()
    else:
        await message.answer("Foydalanuvchilar majud emas !", reply_markup=admin_btn)
        await state.clear()


