from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import types, F
from aiogram.filters import or_f
from loader import dp, bot
from aiogram.types import ContentType
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.password_generator import generate_unique_number
from keyboards.inline.buttons import back_button, cashier_menu_button, user_confirm_button, cashier_confirm_button
from states.my_states import UserStart, TransactionState
from database.orm_query import (
    select_user, get_company_name_by_id, get_terminals_url_by_id, orm_add_transaction, get_user_full_name_by_id,
    get_chief_cashier_users, orm_complete_transaction, get_transaction_by_id, get_branch_transaction_url_by_id,
    has_pending_transaction, get_branch_get_transaction_url_by_id, get_branch_confirm_transaction_url_by_id,
    delete_transaction_by_id
)
import decimal
import httpx


@dp.callback_query(F.data.startswith("conclusion"))
async def transaction_func(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    telegram_id = call.from_user.id
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
                params={"user_id": user_id},
                auth=(login, password),
            )
            response.raise_for_status()
            data = response.json()

        all_cash = data.get("cash", [])
        all_terminal = data.get("terminal", [])

        if not (all_cash or all_terminal):
            await call.message.edit_text("❗️ Kassalar topilmadi")
            return

        await state.update_data(all_cash=all_cash, all_terminal=all_terminal, branch_id=branch_id, company_id=company_id, full_name=full_name)

        keyboard_buttons = []

        # Safely access dictionary keys using .get()
        for cash in all_cash:
            cash_name = cash.get("cash_name")
            cash_id = cash.get("cash_id")
            if cash_name and cash_id is not None:
                keyboard_buttons.append(
                    [InlineKeyboardButton(
                        text=f"💵 {cash_name}",
                        callback_data=f"cash_naqd:{cash_id}"
                    )]
                )

        for terminal in all_terminal:
            cash_name = terminal.get("cash_name")
            cash_id = terminal.get("cash_id")
            if cash_name and cash_id is not None:
                keyboard_buttons.append(
                    [InlineKeyboardButton(
                        text=f"💳 {cash_name}",
                        callback_data=f"cash_terminal:{cash_id}"
                    )]
                )

        keyboard_buttons.append([InlineKeyboardButton(text="◁ Orqaga", callback_data="back")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await call.message.edit_text(f"❖ Kassani tanlang:", reply_markup=keyboard)

    except httpx.HTTPStatusError as e:
        await call.message.edit_text(f"❗️ Server xatosi: {e.response.status_code}")
    except httpx.RequestError as e:
        await call.message.edit_text("❗️ Serverga ulanib bo'lmadi")
        print(f"HTTPX Request Error: {e}")
    except Exception as e:
        # This will now catch other errors like JSONDecodeError, KeyError, etc.
        await call.message.edit_text("❗️ Kassalarni olishda kutilmagan xatolik yuz berdi")
        print(f"Unexpected error: {e}")

    await state.set_state(TransactionState.transaction_menu)


@dp.callback_query(F.data.startswith(("cash_naqd:", "cash_terminal:")), TransactionState.transaction_menu)
async def cash_detail(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data_parts = call.data.split(":")
    cash_type = data_parts[0]
    cash_id = int(data_parts[1])
    data = await state.get_data()
    telegram_id = call.from_user.id
    await state.update_data(cash_id=cash_id, cash_type=cash_type)
    user = await select_user(telegram_id, session)
    user_id = user.id

    if await has_pending_transaction(session, user_id, cash_id):
        await call.message.answer("❗️ Bu kassa uchun sverka allaqachon bajarilgan yoki tekshirilmoqda.")
        return

    else:
        if cash_type == "cash_naqd":
            all_cash = data.get("all_cash", [])
            cash_info = next((c for c in all_cash if c["cash_id"] == cash_id), None)

        elif cash_type == "cash_terminal":
            all_terminal = data.get("all_terminal", [])
            cash_info = next((c for c in all_terminal if c["cash_id"] == cash_id), None)

        else:
            await call.message.edit_text("❗️ Noma'lum kassa turi")
            return

        if not cash_info:
            await call.message.edit_text("❗ Kassa topilmadi")
            return

        back_btn = await back_button()
        text = (
            f"❖ Kassa: <b>{cash_info['cash_name']}</b>\n\n"
            f"﹩ Balans: <b>{cash_info['balance']:,} so'm</b>\n\n"
            f"⑆ Turi: <b>{'Terminal' if cash_type == 'cash_terminal' else 'Naqd pul'}</b>\n"
            f"- - - - - - - - - - - - - - - - - - - - - - - -\n\n"
            f"＄<i> Pul miqdorini kiriting?</i>"
        )

        msg = await call.message.edit_text(text, reply_markup=back_btn)
        await state.update_data(
            source_cash_id=cash_info['cash_id'],
            source_cash_name=cash_info['cash_name'],
            source_cash_type=cash_type,
            source_cash_balance=cash_info['balance'],
            last_msg=msg.message_id
        )
        await state.set_state(TransactionState.transfer_amount)


@dp.message(TransactionState.transfer_amount)
async def transfer_amount_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    source_cash_type = data.get('source_cash_type')
    source_cash_balance = data.get('source_cash_balance')
    try:
        amount = decimal.Decimal(message.text.strip())

        if amount <= 0:
            await message.answer("❗️ Iltimos, faqat musbat son kiriting")
            return

        elif amount > source_cash_balance:
            await message.answer("❗️ Kassada mablag' yetarli emas")
            return

    except ValueError:
        await message.answer("❗️ Faqat raqam kiritish mumkin")
        return

    await state.update_data(transfer_amount=amount)
    back_btn = await back_button()
    if source_cash_type == 'cash_terminal':
        text = (
            f"❖ Kassa: <b>{data.get('source_cash_name')}</b>\n\n"
            f"＄ Miqdori: <b>{amount:,} so'm</b>\n\n"
            f"⑆ Turi: <b>{'Terminal' if source_cash_type == 'cash_terminal' else 'Naqd pul'}</b>\n"
            f"- - - - - - - - - - - - - - - - - - - - - - - -\n\n"
            f"<i>📸 Chekni rasmga olib yuboring:</i>"
        )

        msg = await message.answer(text, reply_markup=back_btn)
        await state.update_data(last_msg=msg.message_id)
        await state.set_state(TransactionState.transfer_photo)
        
    else:
        text = (
            f"❖ Kassa: <b>{data.get('source_cash_name')}</b>\n\n"
            f"＄ Miqdori: <b>{amount:,} so'm</b>\n\n"
            f"⑆ Turi: <b>{'Terminal' if source_cash_type == 'cash_terminal' else 'Naqd pul'}</b>\n\n"
            f"- - - - - - - - - - - - - - - - - - - - - - - -\n\n"
            f"⏍<i> Izoh qoldiring:</i>"
        )
        
        msg = await message.answer(text, reply_markup=back_btn)
        await state.update_data(last_msg=msg.message_id)
        await state.set_state(TransactionState.transfer_comment)


@dp.message(TransactionState.transfer_photo, F.content_type == ContentType.PHOTO)
async def transfer_photo_input(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    back_btn = await back_button()
    data = await state.get_data()
    last_msg_id = data.get("last_msg")

    if last_msg_id:
        try:
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=last_msg_id, reply_markup=None)
        except:
            pass

    if message.photo:
        await state.update_data(transfer_image=message.photo[-1].file_id)
    else:
        await message.answer("❌ Faqat rasm yuborish mumkin!")
        return

    file_info = await bot.get_file(photo.file_id)
    file_extension = file_info.file_path.split(".")[-1].lower()
    valid_extensions = ["jpg", "jpeg", "png", "webp"]

    if file_extension not in valid_extensions:
        await message.answer(
            "Rasm formati noto'g'ri! Faqat jpg, jpeg, png, yoki webp formatlari qabul qilinadi.", reply_markup=back_btn
        )
        return
        
    await state.set_state(TransactionState.transfer_comment)
    msg = await message.answer(f"⏍<i> Izoh qoldiring:</i>", reply_markup=back_btn)
    await state.update_data(last_msg=msg.message_id)


@dp.message(TransactionState.transfer_comment)
async def transfer_comment_input(message: types.Message, state: FSMContext):
    comment = message.text.strip()
    telegram_id = message.from_user.id
    await state.update_data(transfer_comment=comment, transfer_cashier_telegram_id=telegram_id)
    data = await state.get_data()
    source_cash_name = data.get('source_cash_name')
    source_cash_type = data.get('source_cash_type')
    transfer_amount = data.get('transfer_amount')
    transfer_image = data.get('transfer_image')
    confirm_btn = await user_confirm_button()

    text = (
        f"❖ Kassa: <b>{source_cash_name}</b>\n\n"
        f"＄ Summa: <b>{transfer_amount:,} so'm</b>\n\n"
        f"⑆ Turi: <b>{'Terminal' if source_cash_type == 'cash_terminal' else 'Naqd pul'}</b>\n\n"
        f"⏍ Izoh: <b>{comment}</b>\n\n"
        f"- - - - - - - - - - - - - - - - - - - - - - - -\n\n"
        f"◉<i> Sverkani tasdiqlaysizmi?</i>"
    )

    if transfer_image:
        await bot.send_photo(
            chat_id=telegram_id,
            photo=transfer_image,
            caption=text,
            reply_markup=confirm_btn
        )
    else:
        await bot.send_message(
            chat_id=telegram_id,
            text=text,
            reply_markup=confirm_btn
        )
    await state.set_state(TransactionState.confirm)


@dp.callback_query(F.data.startswith("confirm_data"), TransactionState.confirm)
async def confirm_chief_cashier_check(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(UserStart.start)
    telegram_id = call.from_user.id
    user = await select_user(telegram_id, session)
    user_id = user.id
    db_branch_id = user.branch_id
    user_1c_id = user.user_1c_id
    login = user.login
    password = user.password
    full_name = call.from_user.full_name
    data = await state.get_data()
    transfer_image = data.get('transfer_image')
    company_id = data.get('company_id')
    branch_id = data.get('branch_id')
    transfer_comment = data.get('transfer_comment')
    transfer_amount = data.get('transfer_amount')
    cashier_full_name = data.get('full_name')
    source_cash_name = data.get('source_cash_name')
    source_cash_type = data.get('source_cash_type')
    source_cashier_id = data.get('transfer_cashier_telegram_id')
    source_cash_id = data.get('source_cash_id')
    company_name = await get_company_name_by_id(session, company_id)
    transaction_id = await generate_unique_number()
    print("Generated transaction_id: ", transaction_id)
    cash_type = 'TERMINAL' if source_cash_type == 'cash_terminal' else 'CASH'
    cashier_menu_btn = await cashier_menu_button()

    if not all([company_id, branch_id, company_name, transfer_comment]):
        await call.message.answer("❗️ Ma'lumotlar to'liq emas")
        return

    chief_cashiers = await get_chief_cashier_users(session, company_id)

    if not chief_cashiers:
        await call.message.answer("❗️ Bosh kassirlar topilmadi", reply_markup=cashier_menu_btn)
        return

    await call.message.delete()
    await call.message.answer(
        f"☕︎<i> Tekshirilmoqda\nBosh kassirlar tasdiqlashini kuting</i>", reply_markup=cashier_menu_btn
    )
    try:
        await orm_add_transaction(
            session=session,
            transaction_id=str(transaction_id),
            amount=transfer_amount,
            card_type=cash_type,
            sender_terminal_id=source_cashier_id,
            receiver_terminal_id=telegram_id,
            sender_terminal_name=source_cash_name,
            receiver_terminal_name=full_name,
            user_id=user_id,
            branch_id=branch_id,
            company_id=company_id,
            comment=transfer_comment,
            image=transfer_image,
            cash_id=source_cash_id
        )
    except Exception as e:
        print(f"❗️ Sverka saqlashda xato: {e}")

    print("Branch ID: ", branch_id)
    print("BranchDB ID: ", db_branch_id)

    get_transactions_link = await get_branch_get_transaction_url_by_id(session=session, branch_id=db_branch_id)
    print("Sverka list: ", get_transactions_link)
    if not get_transactions_link:
        await call.message.answer("❗️ API URL topilmadi", reply_markup=cashier_menu_btn)
        return

    await state.set_state(TransactionState.transaction_menu)

    text = f"✔︎ <i>Sverka tasdiqlandi</i>"
    json_data = {
        "cash_id": source_cash_id,
        "cash_name": source_cash_name,
        "image": None,  # Default to None
        "amount": transfer_amount,
        "comment": transfer_comment,
        "transaction_id": transaction_id
    }

    if transfer_image:
        try:
            file_info = await bot.get_file(transfer_image)
            file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
            json_data["image"] = file_url
        except Exception as e:
            print(f"Failed to get Telegram file info: {e}")
            await call.message.answer(
                "❗️ Rasm ma'lumotlarini olishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
            return

    try:
        transaction_url = await get_branch_transaction_url_by_id(session, branch_id)
        if not transaction_url:
            await call.message.answer("❗️ API URL topilmadi", reply_markup=cashier_menu_btn)
            return

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                transaction_url,
                params={"user_id": user_1c_id},
                json=json_data,
                auth=(login, password)
            )

        cashier_menu_btn = await cashier_menu_button()
        if response.status_code == 200:
            await call.message.answer(text + "\n\n<i>1C ga muvaffaqiyatli yuborildi!</i>",
                                      reply_markup=cashier_menu_btn)

            await state.set_state(TransactionState.transaction_menu)

        elif response.status_code == 400:
            await call.message.answer(text + "\n\n✖︎ <i>1C ga yuborishda xatolik yuz berdi</i>",
                                      reply_markup=cashier_menu_btn)

        else:
            await call.message.answer(f"❗️ Server xatosi: {response.status_code}")

    except Exception as e:
        print(f"❗️ Sverka yuborishda xatolik: {e}")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                get_transactions_link,
                auth=(login, password),
            )
            response.raise_for_status()
            data = response.json()

        documents = data.get("documents", [])

        if not documents:
            await call.message.answer("❗️ Sverkalar topilmadi")
            return

        await state.update_data(documents=documents, branch_id=branch_id, company_id=company_id, full_name=full_name)

        keyboard_buttons = []

        for document in documents:
            transaction_id = document['transaction_id']
            doc_id = document["number"]

            print("IDsi: ", transaction_id)
            keyboard_buttons.append(
                [InlineKeyboardButton(
                    text=f"﹩ {document['branchSender']}",
                    callback_data=f"sverka:{transaction_id}|{doc_id}"
                )]
            )

        keyboard_buttons.append([InlineKeyboardButton(text="◁ Orqaga", callback_data="back")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        text = f"❖ Sverkani tanlang:"

        for chief_cashier_id in chief_cashiers:
            await bot.send_message(
                chat_id=chief_cashier_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

    except httpx.HTTPStatusError as e:
        await call.message.answer(f"❗️ Server xatosi: {e.response.status_code}")
    except httpx.RequestError:
        await call.message.answer("❗️ Serverga ulanib bo'lmadi")
    except Exception as e:
        await call.message.answer("❗️ Kassalarni olishda xatolik yuz berdi")
        print(f"Unexpected error: {e}")


@dp.callback_query(F.data.startswith("sverka:"))
async def confirm_chief_cashier_menu(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    telegram_id = call.from_user.id
    parts = call.data.split(':')
    data_parts = parts[1].split('|')
    transaction_id = data_parts[0]
    doc_id = data_parts[1]

    transaction = await get_transaction_by_id(session, transaction_id)
    print("Transfer: ", transaction, transaction_id)
    company_id = transaction.company_id
    branch_id = transaction.branch_id
    source_cash_name = transaction.sender_terminal_name
    transfer_amount = transaction.amount
    transfer_comment = transaction.comment
    source_cash_type = transaction.card_type
    cashier_id = transaction.user_id
    transfer_image = transaction.image
    cashier_full_name = await get_user_full_name_by_id(session, user_id=cashier_id)
    company_name = await get_company_name_by_id(session, company_id)

    text = (
        f"№ Sverka ID: {transaction_id}\n\n"
        f"✤ <b>Kompaniya: </b><i>{company_name}</i>\n\n"
        f"✸ <b>Filial IDq: </b><i>{branch_id}</i>\n\n"
        f"✦ <b>Kassir: </b><i>{cashier_full_name}</i>\n\n"
        f"❖ <b>Kassa: </b><i>{source_cash_name}</i>\n\n"
        f"＄ <b>Pul miqdori:</b><i>{transfer_amount:,} so'm</i>\n\n"
        f"⏍ <b>Izoh: </b><i>{transfer_comment}</i>\n\n"
        f"⑆ <b>Turi: </b><i>{'Terminal' if source_cash_type == 'cash_terminal' else 'Naqd pul'}</i>\n\n"
        f"◉ <i>Bu sverkani tasdiqlaysizmi?</i>"
    )

    cashier_confirm_btn = await cashier_confirm_button(transaction_id, doc_id)
    if transfer_image:
        await bot.send_photo(
            chat_id=telegram_id,
            caption=text,
            photo=transfer_image,
            reply_markup=cashier_confirm_btn,
            parse_mode="HTML"
        )
    else:
        await bot.send_message(
            chat_id=telegram_id,
            text=text,
            reply_markup=cashier_confirm_btn,
            parse_mode="HTML"
        )


@dp.callback_query(F.data.startswith("chief_confirm_"))
async def chief_cashier_confirms_transaction(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = call.data.split('_')
    combined_ids = parts[2]
    id_parts = combined_ids.split('|')
    transaction_id = id_parts[0]
    doc_id = id_parts[1]
    telegram_id = call.from_user.id
    user = await select_user(telegram_id, session)
    login = user.login
    password = user.password
    user_1c_id = user.user_1c_id
    print("Bu transfer id: ", transaction_id)
    await orm_complete_transaction(session, transaction_id)
    transaction = await get_transaction_by_id(session, transaction_id)
    branch_id = transaction.branch_id
    await state.set_state(UserStart.start)
    try:
        transaction_url = await get_branch_confirm_transaction_url_by_id(session, branch_id)
        print("Sverka URL: ", transaction_url)
        text = f"✔︎ <i>Sverka tasdiqlandi</i>"

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                transaction_url,
                params={"user_id": user_1c_id, "doc_id": doc_id},
                auth=(login, password)
            )
        cashier_menu_btn = await cashier_menu_button()
        if response.status_code == 200:
            await call.message.delete()
            await call.message.answer(f"<b>№ {transaction_id}</b> - raqamli sverka tasdiqlandi")
            await call.message.answer(text + "\n\n<i>1C ga muvaffaqiyatli yuborildi!</i>",
                                      reply_markup=cashier_menu_btn)
            sender_terminal_id = transaction.sender_terminal_id
            await bot.send_message(chat_id=sender_terminal_id,
                                   text=f"<b>№ {transaction_id}</b> - raqamli sverka tasdiqlandi")

            await state.set_state(TransactionState.transaction_menu)

        elif response.status_code == 400:
            await call.message.answer(text + "\n\n✖︎ <i>1C ga yuborishda xatolik yuz berdi</i>",
                                      reply_markup=cashier_menu_btn)

        else:
            await call.message.answer(f"❗️ Server xatosi: {response.status_code}")

    except Exception as e:
        print(f"❗️ Sverka yuborishda xatolik: {e}")


@dp.callback_query(F.data.startswith("chief_reject"))
async def chief_cashier_rejects_transaction(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = call.data.split('_')
    combined_ids = parts[2]
    id_parts = combined_ids.split('|')
    transaction_id = id_parts[0]
    try:
        transaction = await get_transaction_by_id(session, transaction_id)
        await delete_transaction_by_id(session, transaction_id)
        if not transaction:
            await call.answer("Tranzaksiya topilmadi. U allaqachon bajarilgan bo'lishi mumkin.", show_alert=True)
            return

        sender_terminal_id = transaction.sender_terminal_id
        await call.message.delete()
        await bot.send_message(chat_id=sender_terminal_id, text=f"<b>№ {transaction_id}</b> - raqamli sverka bekor qilindi")
    except Exception as e:
        print(f"❗️ Sverka o'zgartirishda xatolik: {e}")

    cashier_menu_btn = await cashier_menu_button()
    await call.message.answer("✖︎ Bekor qilindi", reply_markup=cashier_menu_btn)
    await state.set_state(UserStart.start)


@dp.callback_query(F.data.startswith("cancel_data"))
async def cancel_terminal_check(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    cashier_menu_btn = await cashier_menu_button()
    await call.message.delete()
    await call.message.answer(
        "✖︎ Bekor qilindi", reply_markup=cashier_menu_btn
    )
    await state.set_state(UserStart.start)


@dp.message(F.video, TransactionState.transfer_amount)
async def reject_video(message: types.Message):
    await message.answer("❗️ Iltimos, video emas, faqat foto yuboring.")


@dp.message(TransactionState.transfer_amount)
async def reject_other(message: types.Message):
    await message.answer("❗️ Faqat rasm yuborish mumkin.")


@dp.message(F.video, TransactionState.transfer_photo)
async def reject_video_transfer(message: types.Message):
    await message.answer("❗️ Iltimos, video emas, faqat foto yuboring.")


@dp.message(TransactionState.transfer_photo)
async def reject_other_transfer(message: types.Message):
    await message.answer("❗️ Faqat rasm yuborish mumkin.")
