import re
import httpx
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram import types, F
from sqlalchemy.ext.asyncio import AsyncSession
from loader import dp
from utils.password_generator import generate_unique_number
from keyboards.inline.buttons import back_button, position_button, check_password_button, cashier_menu_button
from database.orm_query import get_branch_id_by_company_id, select_user, orm_add_user, get_company_id_by_name, get_cashier_by_id, get_company_url_by_id, get_chief_cashier_by_id, get_pass_url_by_id, is_user_active
from states.my_states import UserStart
import logging

logger = logging.getLogger(__name__)


def html_escape(text):
    escape_chars = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}
    return re.sub(r'[&<>"\']', lambda match: escape_chars[match.group(0)], text)


@dp.message(CommandStart())
async def start_bot(message: types.Message, state: FSMContext, session: AsyncSession):
    telegram_id = message.from_user.id
    full_name = html_escape(message.from_user.full_name)
    user = await select_user(telegram_id, session)

    if user is not None:
        await state.set_state(UserStart.start)
        is_active = await is_user_active(telegram_id, session)
        if is_active:
            cashier_menu_btn = await cashier_menu_button()
            await message.answer(
                f"<b>Assalomu alaykum</b> <i>{full_name}</i>.\nMenyuni tanlang", reply_markup=cashier_menu_btn
            )
        else:
            await message.answer("Siz tizimga kirolmaysiz!\nAdmin bilan bog'laning /feedback")
    else:
        await message.answer(
            f"Assalomu alaykum {full_name}\n🏦 Bosh ofis nomini kiriting:"
        )
        await state.set_state(UserStart.is_active)


@dp.message(UserStart.is_active)
async def choose_company(message: types.Message, state: FSMContext, session: AsyncSession):
    telegram_id = message.from_user.id
    user = await select_user(telegram_id, session)
    msg_text = message.text.strip()
    company_id = await get_company_id_by_name(session, name=msg_text)
    company_data = await get_company_url_by_id(session, company_id)
    await state.update_data(company_id=company_id)
    if not company_data:
        await message.answer("❗️ Bunday kompaniya topilmadi")
        return

    branch_url, login, password = company_data

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(branch_url, auth=(login, password))
            response.raise_for_status()
            data = response.json()
        branches = data.get("response", [])

        if not branches:
            await message.answer("❗️ Filiallar topilmadi")
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
        await message.answer("🏛 Filialni tanlang", reply_markup=keyboard)
    except Exception as e:
        print(f"Error on branch URL: {e}")
        await message.answer("❗️ Filiallarni olishda xatolik yuz berdi")
    await state.set_state(UserStart.company)



@dp.callback_query(F.data.startswith("branch_"), UserStart.company)
async def choose_position(call: types.CallbackQuery, state: FSMContext):
    _, raw_id = call.data.split("_", maxsplit=1)
    branch_id = int(raw_id)
    await state.update_data(branch_id=branch_id)
    position_btn = await position_button()
    await call.message.edit_text(
        f"💼 Lavozimni tanlang:",
        reply_markup=position_btn
    )
    await state.set_state(UserStart.branch)


@dp.callback_query(F.data == "cashier", UserStart.branch)
async def select_cashier(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.update_data(user_type="Cashier")
    company_id = (await state.get_data()).get("company_id")
    branch_id = (await state.get_data()).get("branch_id")

    cashier_data = await get_cashier_by_id(session, company_id)

    print(f"Kompaniya ID: {company_id}, BrANCH_id: {branch_id}, {cashier_data}")
    if not cashier_data:
        await call.message.edit_text("❗️ Bunday ma'lumot topilmadi")
        return

    cashiers_url, login, password = cashier_data
    print(f"Kompaniya ID: {company_id}, BRANCH_id: {branch_id}, URL: {cashiers_url}")

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(cashiers_url, params={"branch_id": branch_id}, auth=(login, password))
        response.raise_for_status()
        users = response.json().get("users", [])

    if not users:
        await call.message.edit_text("❗️ Chief Cashier topilmadi")
        return
    await state.update_data(users_from_api=users)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=user["login"],
                    # The correct and secure callback data
                    callback_data=f"select_cashier|{user['user_id']}"
                )
            ]
            for user in users
        ]
    )
    await call.message.answer("Kassirni tanlang 👇", reply_markup=keyboard)
    await state.set_state(UserStart.selected_user)


@dp.callback_query(F.data.startswith("chief_cashier"), UserStart.branch)
async def select_chief_cashier(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.update_data(user_type="ChiefCashier")
    company_id = (await state.get_data()).get("company_id")
    branch_id = (await state.get_data()).get("branch_id")
    cashiers_data = await get_chief_cashier_by_id(session, company_id)
    if not cashiers_data:
        await call.message.edit_text("❗️ Bunday ma'lumot topilmadi")
        return

    chief_cashiers_url, login, password = cashiers_data
    print("Data1: ", cashiers_data)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                chief_cashiers_url,
                params={"branch_id": branch_id},
                auth=(login, password)
            )
            response.raise_for_status()
            result = response.json()

        users = result.get("users", [])

        if not users:
            await call.message.edit_text("❗️ Chief Cashier topilmadi")
            return
        await state.update_data(users_from_api=users)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=user["login"],
                        # The correct and secure callback data
                        callback_data=f"select_cashier|{user['user_id']}"
                    )
                ]
                for user in users
            ]
        )

        await call.message.answer("Chief kassirni tanlang 👇", reply_markup=keyboard)

    except httpx.HTTPStatusError as e:
        await call.message.answer(f"❗️ Server xatosi: {e.response.status_code}")
    except Exception as e:
        print(f"Error on branch URL: {e}")
        await call.message.answer("❗️ Bosh kassirlarni olishda xatolik yuz berdi")
    await state.set_state(UserStart.selected_user)


@dp.callback_query(F.data.startswith(("select_cashier|", "select_chief_cashier|")), UserStart.selected_user)
async def input_password(call: types.CallbackQuery, state: FSMContext):
    _, user_id = call.data.split("|")
    user_id = int(user_id)
    data = await state.get_data()
    users_from_api = data.get("users_from_api", [])
    selected_user = next((user for user in users_from_api if user["user_id"] == user_id), None)

    if not selected_user:
        await call.message.edit_text("❗️ Foydalanuvchi ma'lumoti topilmadi.")
        return

    await state.update_data(
        data_user_id=selected_user['user_id'],
        data_login=selected_user['login'],
        data_password=selected_user['pass']
    )

    back_btn = await back_button()
    await call.message.edit_text("🔐 Parolni kiriting:", reply_markup=back_btn)
    await state.set_state(UserStart.password)


@dp.message(UserStart.password)
async def check_password(message: types.Message, state: FSMContext, session: AsyncSession):
    password = message.text.strip()
    data = await state.get_data()
    company_id = data.get("company_id")
    data_login = data.get("data_login")
    data_password = data.get("data_password")
    data_user_id = data.get("data_user_id")

    if password == data_password:
        await state.set_state(UserStart.check)
        check_password_btn = await check_password_button()
        device_id = await generate_unique_number()

        pass_url_data = await get_pass_url_by_id(session, company_id)
        if not pass_url_data:
            await message.answer("❗️ Bunday kompaniya topilmadi")
            return

        check_pass_url = pass_url_data[0]
        if not check_pass_url.startswith("http"):
            await message.answer("❗️ Server URL noto‘g‘ri saqlangan, admin bilan bog‘laning.")
            return

        json_data = {
            "UserName": data_login,
            "DeviceID": str(device_id),
            "System": "android",
            "agentID": data_user_id
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    check_pass_url,
                    json=json_data,
                    auth=(data_login, data_password)
                )

            await state.update_data(json_data=json_data, data_url=check_pass_url,)

            if response.status_code == 200:
                result = response.json()
                agents = result.get("agents", [])

                if not agents:
                    await message.answer("❗️ Ma'lumotlar topilmadi")
                    return

                await message.answer("✅ Muvaffaqiyatli tasdiqlandi!")

            elif response.status_code == 400:
                await message.answer("⏳ Foydalanuvchi tasdiqlanmagan. Iltimos, kuting!", reply_markup=check_password_btn)

            else:
                await message.answer(f"❗️ Server xatosi: {response.status_code}")

        except httpx.RequestError as e:
            await message.answer("❗️ Server bilan bog‘lanishda muammo yuz berdi.")
            print(f"Connection error: {e}")

    else:
        await message.answer("Noto'g'ri parol, qayta urinib ko'ring !")


@dp.callback_query(F.data.startswith("check_password"), UserStart.check)
async def check_password_user(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    telegram_id = call.from_user.id
    full_name = html_escape(call.from_user.full_name)
    data = await state.get_data()

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                data["data_url"],
                json=data["json_data"],
                auth=(data["data_login"], data["data_password"])
            )

        if response.status_code == 200:
            try:
                company_id = data["company_id"]
                branch_id = await get_branch_id_by_company_id(session, company_id)
                print("Branch IDSI: ", branch_id)
                user, created = await orm_add_user(
                    session,
                    telegram_id,
                    full_name,
                    user_type=data["user_type"],
                    login=data["data_login"],
                    password=data["data_password"],
                    user_1c_id=data["data_user_id"],
                    company_id=company_id,
                    branch_id=branch_id
                )

                cashier_menu_btn = await cashier_menu_button()
                if created:
                    await call.message.edit_text(
                        f"Assalomu alaykum {full_name}\nBotimizga xush kelibsiz!",
                        reply_markup=cashier_menu_btn,
                        parse_mode="HTML"
                    )
                else:
                    await call.message.edit_text(
                        f"Siz allaqachon ro‘yxatdan o‘tgansiz, {user.full_name} ✅",
                        reply_markup=cashier_menu_btn,
                        parse_mode="HTML"
                    )

            except Exception as e:
                logger.error("Xatolik user qo‘shishda: %s", e)

        elif response.status_code == 400:
            await call.message.delete()
            await call.message.answer(
                "⏳ Foydalanuvchi tasdiqlanmagan. Iltimos, kuting!",
                reply_markup=await check_password_button()
            )

        else:
            logger.error("❗️ Server xatosi: %s", response.status_code)

    except httpx.RequestError as e:
        logger.error("Connection error: %s", e)
