from aiogram import types, html, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.default.buttons import back_button, admin_button
from states.my_states import ImageAdd
from helper import check_url
from loader import bot, dp
from filters.admin_bot import IsBotOrAssistantAdmin
from database.orm_query import select_all_users, select_user, select_all_order_users


@dp.message(F.text == '📷 Photo', IsBotOrAssistantAdmin())
async def get_format_text(message: types.Message, state: FSMContext):
    await state.set_state(ImageAdd.image)
    back_btn = await back_button()
    await message.answer(
        text=html.bold("Post rasmini yuboring!"),
        reply_markup=back_btn
    )



# @dp.message(ImageAdd.image, IsBotOrAssistantAdmin())
# async def get_text(message: types.Message, session: AsyncSession, state: FSMContext):
#     telegram_id = message.from_user.id
#     user = await select_user(telegram_id, session)
#     language = user.languages
#     back_btn = await back_button(language)
#     if message.content_type == 'photo':
#         photo = message.photo[-1]
#         await message.answer_photo(photo=message.photo[-1].file_id, caption=message.caption)
#         await state.update_data(image=message.photo[-1].file_id)
#         file_info = await bot.get_file(photo.file_id)
#         file_extension = file_info.file_path.split(".")[-1].lower()
#         valid_extensions = ["jpg", "jpeg", "png", "webp"]
#         if file_extension not in valid_extensions:
#             await message.answer(
#                 "Rasm formati noto‘g‘ri! Faqat jpg, jpeg, png, yoki webp formatlari qabul qilinadi." if language == 'uz'
#                 else "Неверный формат изображения! Принимаются только jpg, jpeg, png или webp.", reply_markup=back_btn
#             )
#             return
#         await state.update_data({
#             'photo': message.photo[-1].file_id,
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
#         else:
#             text = "Отправить ссылку в следующем формате:\n" \
#                    "[текст кнопки + ссылка]\n" \
#                    "Пример:\n" \
#                    "[Переводчик+https://t.me/Sayfulloh_Mamatqulov]\n" \
#                    "Чтобы добавить несколько кнопок в одну строку, введите текст на новой строке.\n" \
#                    "Формат:\n" \
#                    "[Первый текст + первая ссылка]\n" \
#                    "[Второй текст + вторая ссылка]"
#
#         get_before_btn = await get_before_button(language)
#         await message.answer(text, reply_markup=get_before_btn)
#         await state.set_state(ImageAdd.url)
#
#     else:
#         await message.answer(html.bold("Post rasmini yuboring!" if language == 'uz' else "Отправьте фотографию поста!"))
#         await state.set_state(ImageAdd.image)
#
#
# @dp.message(F.text.in_(["Davom etish ➡️", "Продолжить ➡️"]), ImageAdd.url, IsBotOrAssistantAdmin())
# async def back(message: types.Message, session: AsyncSession, state: FSMContext):
#     telegram_id = message.from_user.id
#     user = await select_user(telegram_id, session)
#     language = user.languages
#     data = await state.get_data()
#     await message.answer_photo(photo=data['image'], caption=data['caption'])
#     send_btn = await send_button(language)
#     await message.answer("Agar tayyor bo'lsa '📤 Yuborish' tugmasini bosing." if language == 'uz'
#                          else "Когда будете готовы, нажмите «📤 Отправить».", reply_markup=send_btn)
#     await state.set_state(ImageAdd.send)
#
#
# @dp.message(ImageAdd.url, IsBotOrAssistantAdmin())
# async def get_url(message: types.Message, session: AsyncSession, state: FSMContext):
#     telegram_id = message.from_user.id
#     user = await select_user(telegram_id, session)
#     language = user.languages
#     get_before_btn = await get_before_button(language)
#     send_btn = await send_button(language)
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
#         await message.answer_photo(photo=data['photo'], caption=data['caption'], reply_markup=btn.as_markup())
#         await message.answer("Agar tayyor bo'lsa '📤 Yuborish' tugmasini bosing." if language == 'uz'
#                              else "Когда будете готовы, нажмите «📤 Отправить».", reply_markup=send_btn)
#         await state.set_state(ImageAdd.send)
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
#         else:
#             text = "Отправить ссылку в следующем формате:\n" \
#                    "[текст кнопки + ссылка]\n" \
#                    "Пример:\n" \
#                    "[Переводчик+https://t.me/Sayfulloh_Mamatqulov]\n" \
#                    "Чтобы добавить несколько кнопок в одну строку, введите текст на новой строке.\n" \
#                    "Формат:\n" \
#                    "[Первый текст + первая ссылка]\n" \
#                    "[Второй текст + вторая ссылка]"
#         await message.answer(text, reply_markup=get_before_btn)
#         await state.set_state(ImageAdd.url)
#
#
# @dp.message(F.text.in_(["📤 Yuborish", "📤 Отправить"]), ImageAdd.send, IsBotOrAssistantAdmin())
# async def send_add(message: types.Message,  session: AsyncSession, state: FSMContext):
#     await state.set_state(ImageAdd.check)
#     user_id = message.from_user.id
#     user = await select_user(telegram_id=user_id, session=session)
#     language = user.languages
#     text = "Kimlar uchun foto xabarini yubormoqchisiz?" if language == 'uz' else "Кому вы хотите отправить фотосообщение?"
#     send_btn = await ad_send_btn(language)
#     await message.answer(text=text, reply_markup=send_btn)
#
#
# @dp.message(F.text.in_(["Buyurtma berganlar ✅", "Те, кто сделали заказ ✅"]), ImageAdd.check, IsBotOrAssistantAdmin())
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
#                     await bot.send_photo(
#                         photo=data['photo'],
#                         caption=data['caption'],
#                         chat_id=i.user_id,
#                         reply_markup=btn.as_markup(row_width=1)
#                     )
#                     counter += 1
#                 except Exception as e:
#                     print(e)
#             await message.answer(f"Buyurtma bergan {counter}ta obunachiga xabar yuborildi!" if language == 'uz' else
#                                  f"Сообщение отправлено подписчикам {counter}, оформившим заказ!", reply_markup=admin_btn)
#         else:
#             counter = 0
#             for i in users:
#                 try:
#                     await bot.send_photo(photo=data['photo'], caption=data['caption'], chat_id=i.user_id)
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
# @dp.message(F.text.in_(["Buyurtma bermaganlar ❌", "Те, кто не заказывал ❌"]), ImageAdd.check, IsBotOrAssistantAdmin())
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
#                     await bot.send_photo(
#                         photo=data['photo'],
#                         caption=data['caption'],
#                         chat_id=i.user_id,
#                         reply_markup=btn.as_markup(row_width=1)
#                     )
#                     counter += 1
#                 except Exception as e:
#                     print(e)
#             await message.answer(f"Buyurtma bermagan {counter}ta obunachiga xabar yuborildi!" if language == 'uz' else
#                                  f"Сообщение отправлено подписчикам {counter}, которые не оформили заказ!",
#                                  reply_markup=admin_btn)
#         else:
#             counter = 0
#             for i in users:
#                 try:
#                     await bot.send_photo(photo=data['photo'], caption=data['caption'], chat_id=i.user_id)
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
# @dp.message(F.text.in_(["Hamma uchun 👨‍👦‍👦", "Для всех 👨‍👦‍👦"]), ImageAdd.check, IsBotOrAssistantAdmin())
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
#                     await bot.send_photo(
#                         photo=data['photo'],
#                         caption=data['caption'],
#                         chat_id=i.user_id,
#                         reply_markup=btn.as_markup(row_width=1)
#                     )
#                     counter += 1
#                 except Exception as e:
#                     print(e)
#             await message.answer(f"{counter}ta obunachiga xabar yuborildi!" if language == 'uz' else
#                                  f"Сообщение отправлено подписчикам {counter}!", reply_markup=admin_btn)
#         else:
#             counter = 0
#             for i in users:
#                 try:
#                     await bot.send_photo(photo=data['photo'], caption=data['caption'], chat_id=i.user_id)
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
