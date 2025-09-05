from aiogram.fsm.context import FSMContext
from aiogram import types, F
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from keyboards.default.buttons import branch_crud_button, back_button, branch_edit_button
from states.my_states import BranchEdit, BranchState
from filters.admin_bot import IsBotOrAssistantAdmin
from loader import dp
from database.orm_query import (
    update_branch_transaction_url, transaction_link_exist, get_company_id_by_name,
    select_all_companies, cashier_link_exist, get_branch_by_company_id, get_branch_id_by_name,
    update_branch_name, update_branch_cashiers_url, update_branch_chief_cashiers_url,
    update_branch_pass_url, update_branch_login, update_branch_password, update_branch_check_transaction_url,
    chief_cashier_link_exist,pass_check_link_exist, get_transaction_link_exist, check_transaction_link_exist,
    update_branch_transactions_list_url
)


@dp.message(F.text.in_(["📝 Filial o'zgartirish"]), IsBotOrAssistantAdmin())
async def edit_branch_func(message: types.Message, state: FSMContext, session: AsyncSession):
    companies = await select_all_companies(session)
    if companies:
        await state.set_state(BranchEdit.company)
        keyboard = ReplyKeyboardBuilder()
        for company in companies:
            button = KeyboardButton(text=company.name)
            keyboard.add(button)
        keyboard.adjust(2)
        back_btn = KeyboardButton(text="⬅️ Orqaga")
        keyboard.row(back_btn)
        await message.answer(
            text="Kompaniyani tanlang:",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
    else:
        await state.set_state(BranchState.branch_menu)
        branch_crud_btn = await branch_crud_button()
        await message.answer(
            text="Kompaniyalar yo'q ❗️\nAvval kompaniya qo'shing.",
            reply_markup=branch_crud_btn
        )


@dp.message(BranchEdit.company)
async def select_branch(message: types.Message, state: FSMContext, session: AsyncSession):
    name = message.text.strip()
    company_id = await get_company_id_by_name(session, name)
    branches = await get_branch_by_company_id(session, company_id)
    if branches:
        await state.set_state(BranchEdit.select)
        keyboard = ReplyKeyboardBuilder()
        for branch in branches:
            button = KeyboardButton(text=branch.name)
            keyboard.add(button)
        keyboard.adjust(2)
        back_btn = KeyboardButton(text="⬅️ Orqaga")
        keyboard.row(back_btn)
        await message.answer(
            text="Filialni tanlang:",
            reply_markup=keyboard.as_markup(resize_keyboard=True)
        )
    else:
        await state.set_state(BranchState.branch_menu)
        branch_crud_btn = await branch_crud_button()
        await message.answer(
            text="Filiallar yo'q ❗️\nAvval filial qo'shing.",
            reply_markup=branch_crud_btn
        )


@dp.message(BranchEdit.select)
async def edit_branch_fields(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.set_state(BranchEdit.edit_menu)
    name = message.text.strip()
    branch_id = await get_branch_id_by_name(session, name)
    await state.update_data(branch_id=branch_id)
    branch_edit_btn = await branch_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=branch_edit_btn
    )


@dp.message(BranchEdit.edit_menu, F.text.in_(["🏛 Filial nomi"]), IsBotOrAssistantAdmin())
async def edit_branch_name(message: types.Message, state: FSMContext):
    await state.set_state(BranchEdit.name)
    back_btn = await back_button()
    await message.answer("🏛 Yangi nomi kiriting :", reply_markup=back_btn)


@dp.message(BranchEdit.name, F.text.not_in(["⬅️ Orqaga"]))
async def branch_name_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_name = message.text.strip()
    data = await state.get_data()
    branch_id = data.get("branch_id")

    try:
        updated = await update_branch_name(session, branch_id, new_name)

        if updated:
            await message.answer("✅ Filial nomi yangilandi.")
        else:
            await message.answer("❌ Bunday filial topilmadi.")

    except Exception as e:
        print(f"Error in Update Branch name - {e}")
    await state.set_state(BranchEdit.edit_menu)
    branch_edit_btn = await branch_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=branch_edit_btn)


@dp.message(BranchEdit.edit_menu, F.text.in_(["🔗 Kassir URL"]), IsBotOrAssistantAdmin())
async def edit_cashier_url(message: types.Message, state: FSMContext):
    await state.set_state(BranchEdit.cashier_link)
    back_btn = await back_button()
    await message.answer("🔗 Yangi Kassir URlni kiriting :", reply_markup=back_btn)


@dp.message(BranchEdit.cashier_link, F.text.not_in(["⬅️ Orqaga"]))
async def cashier_url_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_link = message.text.strip()
    data = await state.get_data()
    branch_id = data.get("branch_id")
    back_btn = await back_button()

    try:
        link_exist = await cashier_link_exist(session=session, cashiers_url=new_link)
        if link_exist:
            await message.answer(
                "<i>❗️ Bu link allaqachon mavjud!\nBoshqasini kiriting.</i>",
                reply_markup=back_btn
            )
            return

        updated = await update_branch_cashiers_url(session, branch_id, new_link)
        if updated:
            await message.answer("✅ Filial Kassir URL yangilandi.")
        else:
            await message.answer("❌ Filial topilmadi.")

    except Exception as e:
        print(f"Error in Update Branch URL - {e}")

    await state.set_state(BranchEdit.edit_menu)
    branch_edit_btn = await branch_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=branch_edit_btn
    )


@dp.message(BranchEdit.edit_menu, F.text.in_(["🔗 Bosh kassir URL"]), IsBotOrAssistantAdmin())
async def edit_chief_url(message: types.Message, state: FSMContext):
    await state.set_state(BranchEdit.chief_cashier_link)
    back_btn = await back_button()
    await message.answer("🔗 Yangi Bosh-kassir URLni kiriting :", reply_markup=back_btn)


@dp.message(BranchEdit.chief_cashier_link, F.text.not_in(["⬅️ Orqaga"]))
async def branch_url_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_link = message.text.strip()
    data = await state.get_data()
    branch_id = data.get("branch_id")
    back_btn = await back_button()

    try:
        link_exist = await chief_cashier_link_exist(session=session, chief_cashiers_url=new_link)
        if link_exist:
            await message.answer(
                "<i>❗️ Bu link allaqachon mavjud!\nBoshqasini kiriting.</i>",
                reply_markup=back_btn
            )
            return

        updated = await update_branch_chief_cashiers_url(session, branch_id, new_link)
        if updated:
            await message.answer("✅ Filial Bosh kassir URL yangilandi.")
        else:
            await message.answer("❌ Filial topilmadi.")

    except Exception as e:
        print(f"Error in Update Branch URL - {e}")

    await state.set_state(BranchEdit.edit_menu)
    branch_edit_btn = await branch_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=branch_edit_btn
    )


@dp.message(BranchEdit.edit_menu, F.text.in_(["🔗 Parol check URL"]), IsBotOrAssistantAdmin())
async def edit_pass_check_url(message: types.Message, state: FSMContext):
    await state.set_state(BranchEdit.check_pass_link)
    back_btn = await back_button()
    await message.answer("🔗 Yangi parol tekshiruv URLni kiriting :", reply_markup=back_btn)


@dp.message(BranchEdit.check_pass_link, F.text.not_in(["⬅️ Orqaga"]))
async def check_pass_url_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_link = message.text.strip()
    data = await state.get_data()
    branch_id = data.get("branch_id")
    back_btn = await back_button()

    try:
        link_exist = await pass_check_link_exist(session=session, check_pass_url=new_link)
        if link_exist:
            await message.answer(
                "<i>❗️ Bu link allaqachon mavjud!\nBoshqasini kiriting.</i>",
                reply_markup=back_btn
            )
            return

        updated = await update_branch_pass_url(session, branch_id, new_link)
        if updated:
            await message.answer("✅ Filial Parol tekshirish URL yangilandi.")
        else:
            await message.answer("❌ Filial topilmadi.")

    except Exception as e:
        print(f"Error in Update Branch URL - {e}")

    await state.set_state(BranchEdit.edit_menu)
    branch_edit_btn = await branch_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=branch_edit_btn
    )


@dp.message(BranchEdit.edit_menu, F.text.in_(["🔗 Create Transaksiya URL"]), IsBotOrAssistantAdmin())
async def edit_pass_check_url(message: types.Message, state: FSMContext):
    await state.set_state(BranchEdit.transaction_link)
    back_btn = await back_button()
    await message.answer("🔗 Yangi Transaksiya URLini kiriting :", reply_markup=back_btn)


@dp.message(BranchEdit.transaction_link, F.text.not_in(["⬅️ Orqaga"]))
async def check_transaction_url_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_link = message.text.strip()
    data = await state.get_data()
    branch_id = data.get("branch_id")
    back_btn = await back_button()

    try:
        link_exist = await transaction_link_exist(session=session, transaction_url=new_link)
        if link_exist:
            await message.answer(
                "<i>❗️ Bu link allaqachon mavjud!\nBoshqasini kiriting.</i>",
                reply_markup=back_btn
            )
            return

        updated = await update_branch_transaction_url(session, branch_id, new_link)
        if updated:
            await message.answer("✅ Filial Transaksiya URL yangilandi.")
        else:
            await message.answer("❌ Filial topilmadi.")

    except Exception as e:
        print(f"Error in Update Branch URL - {e}")

    await state.set_state(BranchEdit.edit_menu)
    branch_edit_btn = await branch_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=branch_edit_btn
    )


@dp.message(BranchEdit.edit_menu, F.text.in_("🔗 Get Transactions URL"), IsBotOrAssistantAdmin())
async def edit_get_transaction_url(message: types.Message, state: FSMContext):
    await state.set_state(BranchEdit.get_transaction_link)
    back_btn = await back_button()
    await message.answer("🔗 Transaksiyalar ro'yxatini oluvchi yangi API-URLini kiriting :", reply_markup=back_btn)


@dp.message(BranchEdit.get_transaction_link, F.text.not_in(["⬅️ Orqaga"]))
async def check_get_transaction_url_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_link = message.text.strip()
    data = await state.get_data()
    branch_id = data.get("branch_id")
    back_btn = await back_button()

    try:
        link_exist = await get_transaction_link_exist(session=session, get_transaction_url=new_link)
        if link_exist:
            await message.answer(
                "<i>❗️ Bu link allaqachon mavjud!\nBoshqasini kiriting.</i>",
                reply_markup=back_btn
            )
            return

        updated = await update_branch_transactions_list_url(session, branch_id, new_link)
        if updated:
            await message.answer("✅ Filial Transaksiya URL yangilandi.")
        else:
            await message.answer("❌ Filial topilmadi.")

    except Exception as e:
        print(f"Error in Update Branch URL - {e}")

    await state.set_state(BranchEdit.edit_menu)
    branch_edit_btn = await branch_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=branch_edit_btn
    )


@dp.message(BranchEdit.edit_menu, F.text.in_("🔗 Check Transaction URL"), IsBotOrAssistantAdmin())
async def edit_get_transaction_url(message: types.Message, state: FSMContext):
    await state.set_state(BranchEdit.check_transaction_link)
    back_btn = await back_button()
    await message.answer("🔗 Transaksiya tasdqilovchi yangi API-URLini kiriting :", reply_markup=back_btn)


@dp.message(BranchEdit.check_transaction_link, F.text.not_in(["⬅️ Orqaga"]))
async def check_confirm_transaction_url_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_link = message.text.strip()
    data = await state.get_data()
    branch_id = data.get("branch_id")
    back_btn = await back_button()

    try:
        link_exist = await check_transaction_link_exist(session=session, check_transaction_url=new_link)
        if link_exist:
            await message.answer(
                "<i>❗️ Bu link allaqachon mavjud!\nBoshqasini kiriting.</i>",
                reply_markup=back_btn
            )
            return

        updated = await update_branch_check_transaction_url(session, branch_id, new_link)
        if updated:
            await message.answer("✅ Filial Transaksiya URL yangilandi.")
        else:
            await message.answer("❌ Filial topilmadi.")

    except Exception as e:
        print(f"Error in Update Branch URL - {e}")

    await state.set_state(BranchEdit.edit_menu)
    branch_edit_btn = await branch_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=branch_edit_btn
    )


@dp.message(BranchEdit.edit_menu, F.text.in_(["🔏️ API-login"]), IsBotOrAssistantAdmin())
async def edit_branch_login(message: types.Message, state: FSMContext):
    await state.set_state(BranchEdit.login)
    back_btn = await back_button()
    await message.answer("🔏 Yangi API-loginni kiriting :", reply_markup=back_btn)


@dp.message(BranchEdit.login, F.text.not_in(["⬅️ Orqaga"]))
async def branch_login_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_login = message.text.strip()
    data = await state.get_data()
    branch_id = data.get("branch_id")

    try:
        updated = await update_branch_login(session, branch_id, new_login)

        if updated:
            await message.answer("✅ Kompaniya login yangilandi.")
        else:
            await message.answer("❌ Bunday login topilmadi.")

    except Exception as e:
        print(f"Error in Update Branch login - {e}")
    await state.set_state(BranchEdit.edit_menu)
    branch_edit_btn = await branch_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=branch_edit_btn)


@dp.message(BranchEdit.edit_menu, F.text.in_(["🔐 API-password"]), IsBotOrAssistantAdmin())
async def edit_branch_password(message: types.Message, state: FSMContext):
    await state.set_state(BranchEdit.password)
    back_btn = await back_button()
    await message.answer("🔐 Yangi API-parolni kiriting :", reply_markup=back_btn)


@dp.message(BranchEdit.password, F.text.not_in(["⬅️ Orqaga"]))
async def category_password_update(message: types.Message, state: FSMContext, session: AsyncSession):
    new_password = message.text.strip()
    data = await state.get_data()
    branch_id = data.get("branch_id")

    try:
        updated = await update_branch_password(session, branch_id, new_password)

        if updated:
            await message.answer("✅ Kompaniya paroli yangilandi.")
        else:
            await message.answer("❌ Bunday parol topilmadi.")

    except Exception as e:
        print(f"Error in Update Branch login - {e}")
    await state.set_state(BranchEdit.edit_menu)
    branch_edit_btn = await branch_edit_button()
    await message.answer(
        text="Qaysi qismini tahrirlamoqchisiz?",
        reply_markup=branch_edit_btn)