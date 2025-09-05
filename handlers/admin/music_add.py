from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types, html, F
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.default.buttons import back_button
from states.my_states import MusicAdd
from filters.admin_bot import IsBotOrAssistantAdmin
from helper import check_url
from loader import dp


@dp.message(F.text == '🎵 Music', IsBotOrAssistantAdmin())
async def get_format_music(message: types.Message, state: FSMContext):
    back_btn = await back_button()

    await message.answer(
        text=html.bold("Post musiqasini yuboring."),
        reply_markup=back_btn
    )
    await state.set_state(MusicAdd.music)
#
#
# @dp.message(MusicAdd.music, IsBotOrAssistantAdmin())
# async def get_music(message: types.Message, session: AsyncSession, state: FSMContext):
#     telegram_id = message.from_user.id
#     user = await select_user(telegram_id, session)
#     language = user.languages
#     get_before_btn = await get_before_button(language)
#     if message.content_type == 'audio':
#         await message.answer_audio(audio=message.audio.file_id, caption=message.caption)
#         await state.update_data({
#             'audio': message.audio.file_id,
#             'caption': message.caption
#         })
#         if language == 'uz':
#             text = "Havolani quyidagi formatda yuboring :\n" \
#                    "[tugma matni + havola]\n" \
#                    "Misol :\n" \
#                    "[Tarjimon+https://t.me/Sayfulloh_Mamatqulov]\n" \
#                    "Bir qatorga bir nechta tugmalar qo'shish uchun yangi qatordan yozing.\n" \
#                    "Format :\n" \
#                    "[Birinchi matn + birinchi havola]\n" \
#                    "[Ikkinchi matn + ikkinchi havola]"
#
#         else:
#             text = "Отправьте ссылку в следующем формате: \n" \
#                    "[текст кнопки + ссылка]\n" \
#                    "Пример:\n" \
#                    "[Переводчик+https://t.me/Sayfulloh_Mamatqulov]\n" \
#                    "Чтобы добавить несколько кнопок в одну строку, введите текст на новой строке.\n" \
#                    "Формат:\n" \
#                    "[Первый текст + первая ссылка]\n" \
#                    "[Второй текст + вторая ссылка]"
#
#         await message.answer(text, reply_markup=get_before_btn)
#         await state.set_state(MusicAdd.url)
#
#     else:
#         await message.answer(html.bold("Post musiqasini yuboring." if language == 'uz' else "Отправить пост с музыкой"))
#         await state.set_state(MusicAdd.music)
#
#
# @dp.message(F.text.in_(["Davom etish ➡️", "Продолжить ➡️"]), MusicAdd.url, IsBotOrAssistantAdmin())
# async def skip_text(message: types.Message, session: AsyncSession, state: FSMContext):
#     telegram_id = message.from_user.id
#     user = await select_user(telegram_id, session)
#     language = user.languages
#     send_btn = await send_button(language)
#     data = await state.get_data()
#     await message.answer_audio(audio=data['audio'], caption=data['caption'])
#     await message.answer("Agar tayyor bo'lsa '📤 Yuborish' tugmasini bosing." if language == 'uz' else
#                          "Когда будете готовы, нажмите «📤 Отправить».", reply_markup=send_btn)
#     await state.set_state(MusicAdd.send)
#
#
# @dp.message(MusicAdd.url, IsBotOrAssistantAdmin())
# async def get_url(message: types.Message, session: AsyncSession, state: FSMContext):
#     telegram_id = message.from_user.id
#     user = await select_user(telegram_id, session)
#     language = user.languages
#     send_btn = await send_button(language)
#     get_before_btn = await get_before_button(language)
#     if message.content_type == 'text':
#         await message.answer(message.text)
#         urls = check_url(text=message.text)
#         urls = urls if urls else None
#         await state.update_data({
#             'buttons': urls
#         })
#         data = await state.get_data()
#         links = urls.splitlines()
#         btn = InlineKeyboardBuilder()
#         for link in links:
#             manzil = link[link.rfind('+') + 1:].strip()
#             text = link[:link.rfind('+')].strip()
#             btn.button(text=text, url=manzil)
#         btn.adjust(1)
#         await message.answer_audio(audio=data['audio'], caption=data['caption'], reply_markup=btn.as_markup())
#         await message.answer("Agar tayyor bo'lsa '📤 Yuborish' tugmasini bosing." if language == 'uz'
#                              else "Когда будете готовы, нажмите «📤 Отправить».", reply_markup=send_btn)
#         await state.set_state(MusicAdd.send)
#
#     else:
#         if language == 'uz':
#             text = "Havolani quyidagi formatda yuboring :\n" \
#                    "[tugma matni + havola]\n" \
#                    "Misol :\n" \
#                    "[Tarjimon+https://t.me/Sayfulloh_Mamatqulov]\n" \
#                    "Bir qatorga bir nechta tugmalar qo'shish uchun yangi qatordan yozing.\n" \
#                    "Format :\n" \
#                    "[Birinchi matn + birinchi havola]\n" \
#                    "[Ikkinchi matn + ikkinchi havola]"
#
#         else:
#             text = "Отправьте ссылку в следующем формате: \n" \
#                    "[текст кнопки + ссылка]\n" \
#                    "Пример:\n" \
#                    "[Переводчик+https://t.me/Sayfulloh_Mamatqulov]\n" \
#                    "Чтобы добавить несколько кнопок в одну строку, введите текст на новой строке.\n" \
#                    "Формат:\n" \
#                    "[Первый текст + первая ссылка]\n" \
#                    "[Второй текст + вторая ссылка]"
#
#         await message.answer(text, reply_markup=get_before_btn)
#         await state.set_state(MusicAdd.url)
#
#
# @dp.message(F.text.in_(["📤 Yuborish", "📤 Отправить"]), MusicAdd.send, IsBotOrAssistantAdmin())
# async def send_add(message: types.Message,  session: AsyncSession, state: FSMContext):
#     await state.set_state(MusicAdd.check)
#     user_id = message.from_user.id
#     user = await select_user(telegram_id=user_id, session=session)
#     language = user.languages
#     text = "Kimlar uchun musiqa xabarini yubormoqchisiz?" if language == 'uz' else "Кому вы хотите отправить музыкальное сообщение?"
#     send_btn = await ad_send_btn(language)
#     await message.answer(text=text, reply_markup=send_btn)
#
#
# @dp.message(F.text.in_(["Buyurtma berganlar ✅", "Те, кто сделали заказ ✅"]), MusicAdd.check, IsBotOrAssistantAdmin())
# async def send_to_order_users(message: types.Message, session: AsyncSession, state: FSMContext):
#     user_id = message.from_user.id
#     user = await select_user(telegram_id=user_id, session=session)
#     language = user.languages
#     data = await state.get_data()
#     users = await select_all_order_users(session)
#     admin_btn = await admin_button(language)
#     if users:
#         if data.get('buttons', None):
#             links = data['buttons'].splitlines()
#             btn = InlineKeyboardBuilder()
#             for link in links:
#                 manzil = link[link.rfind('+') + 1:].strip()
#                 text = link[:link.rfind('+')].strip()
#                 btn.button(text=text, url=manzil)
#             btn.adjust(1)
#             counter = 0
#             for i in users:
#                 try:
#                     await bot.send_audio(audio=data['audio'], caption=data['caption'], chat_id=i.user_id,
#                                          reply_markup=btn.as_markup(row_width=1))
#                     counter += 1
#
#                 except Exception as e:
#                     print(e)
#             await message.answer(f"Buyurtma bergan {counter}ta obunachiga xabar yuborildi!" if language == 'uz' else
#                                  f"Сообщение отправлено подписчикам {counter}, оформившим заказ!", reply_markup=admin_btn)
#         else:
#             counter = 0
#             for i in users:
#                 try:
#                     await bot.send_audio(audio=data['audio'], caption=data['caption'], chat_id=i.user_id)
#                     counter += 1
#                 except Exception as e:
#                     print(e)
#
#             await message.answer(f"Buyurtma bergan {counter}ta obunachiga xabar yuborildi!" if language == 'uz' else
#                                  f"Сообщение отправлено подписчикам {counter}, оформившим заказ!", reply_markup=admin_btn)
#         await state.clear()
#     else:
#         await state.clear()
#         await message.answer("Buyurtma bergan foydalanuvchilar majud emas !" if language == 'uz' else
#                              "Пользователей, оформивших заказ, не существует!", reply_markup=admin_btn)
#
#
# @dp.message(F.text.in_(["Buyurtma bermaganlar ❌", "Те, кто не заказывал ❌"]), MusicAdd.check, IsBotOrAssistantAdmin())
# async def send_to_no_order_users(message: types.Message, session: AsyncSession, state: FSMContext):
#     user_id = message.from_user.id
#     user = await select_user(telegram_id=user_id, session=session)
#     language = user.languages
#     data = await state.get_data()
#     users = await select_all_no_order_users(session)
#     admin_btn = await admin_button(language)
#     if users:
#         if data.get('buttons', None):
#             links = data['buttons'].splitlines()
#             btn = InlineKeyboardBuilder()
#             for link in links:
#                 manzil = link[link.rfind('+') + 1:].strip()
#                 text = link[:link.rfind('+')].strip()
#                 btn.button(text=text, url=manzil)
#             btn.adjust(1)
#             counter = 0
#             for i in users:
#                 try:
#                     await bot.send_audio(audio=data['audio'], caption=data['caption'], chat_id=i.user_id,
#                                          reply_markup=btn.as_markup(row_width=1))
#                     counter += 1
#
#                 except Exception as e:
#                     print(e)
#             await message.answer(f"Buyurtma bermagan {counter}ta obunachiga xabar yuborildi!" if language == 'uz' else
#                                  f"Сообщение отправлено подписчикам {counter}, которые не оформили заказ!",
#                                  reply_markup=admin_btn)
#         else:
#             counter = 0
#             for i in users:
#                 try:
#                     await bot.send_audio(audio=data['audio'], caption=data['caption'], chat_id=i.user_id)
#                     counter += 1
#                 except Exception as e:
#                     print(e)
#
#             await message.answer(f"Buyurtma bermagan {counter}ta obunachiga xabar yuborildi!" if language == 'uz' else
#                                  f"Сообщение отправлено подписчикам {counter}, которые не оформили заказ!",
#                                  reply_markup=admin_btn)
#         await state.clear()
#     else:
#         await message.answer("Buyurtma bermagan foydalanuvchilar majud emas !" if language == 'uz' else
#                              "Пользователи, не оформившие заказ, недоступны!", reply_markup=admin_btn)
#         await state.clear()
#
#
# @dp.message(F.text.in_(["Hamma uchun 👨‍👦‍👦", "Для всех 👨‍👦‍👦"]), MusicAdd.check, IsBotOrAssistantAdmin())
# async def send_to_all_users(message: types.Message, session: AsyncSession, state: FSMContext):
#     user_id = message.from_user.id
#     user = await select_user(telegram_id=user_id, session=session)
#     language = user.languages
#     data = await state.get_data()
#     users = await select_all_users(session)
#     admin_btn = await admin_button(language)
#     if users:
#         if data.get('buttons', None):
#             links = data['buttons'].splitlines()
#             btn = InlineKeyboardBuilder()
#             for link in links:
#                 manzil = link[link.rfind('+') + 1:].strip()
#                 text = link[:link.rfind('+')].strip()
#                 btn.button(text=text, url=manzil)
#             btn.adjust(1)
#             counter = 0
#             for i in users:
#                 try:
#                     await bot.send_audio(audio=data['audio'], caption=data['caption'], chat_id=i.user_id,
#                                          reply_markup=btn.as_markup(row_width=1))
#                     counter += 1
#
#                 except Exception as e:
#                     print(e)
#             await message.answer(f"{counter}ta obunachiga xabar yuborildi!" if language == 'uz' else
#                                  f"Сообщение отправлено подписчикам {counter}!", reply_markup=admin_btn)
#         else:
#             counter = 0
#             for i in users:
#                 try:
#                     await bot.send_audio(audio=data['audio'], caption=data['caption'], chat_id=i.user_id)
#                     counter += 1
#                 except Exception as e:
#                     print(e)
#
#             await message.answer(f"{counter}ta obunachiga xabar yuborildi!" if language == 'uz' else
#                                  f"Сообщение отправлено подписчикам {counter}!", reply_markup=admin_btn)
#         await state.clear()
#     else:
#         await message.answer("Foydalanuvchilar majud emas !" if language == 'uz' else
#                              "Нет доступных пользователей !", reply_markup=admin_btn)
#         await state.clear()
