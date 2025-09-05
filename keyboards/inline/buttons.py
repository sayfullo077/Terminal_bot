from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.fsm.context import FSMContext
from typing import List
from database.models import CardTransaction
from aiogram import types


class ChooseLanguageCallback(CallbackData, prefix='ikb01'):
    language: str


button = InlineKeyboardBuilder()
button.button(text="🇺🇿 O'zbek tili", callback_data=ChooseLanguageCallback(language="uz"))
button.button(text="🇷🇺 Русский язык", callback_data=ChooseLanguageCallback(language="ru"))
button.adjust(1)


class TextFormatCallBack(CallbackData, prefix='ikb0001'):
    format: str


def format_btn(format):
    btn = InlineKeyboardBuilder()
    next = "HTML" if format == 'html' else "TEXT"
    btn.button(text=f"Markup format {next}", callback_data=TextFormatCallBack(format=format))
    return btn.as_markup()


page_size = 5


async def branches_button(branches_list: list[dict]):
    kb = InlineKeyboardBuilder()
    for branch in branches_list:
        kb.button(
            text=branch["name"],
            callback_data=f"branch_{branch['id']}"
        )
    kb.button(text="◁ Orqaga", callback_data='back')
    kb.adjust(2)
    return kb.as_markup()


async def admin_confirm_button(telegram_id):
    btn = InlineKeyboardBuilder()
    btn.button(text="✔︎ Tasdiqlash", callback_data=f"admin_confirm_data:{telegram_id}")
    btn.button(text="✖︎ Bekor qilish", callback_data=f"admin_cancel_data:{telegram_id}")
    btn.adjust(2)
    return btn.as_markup()


async def user_confirm_button():
    btn = InlineKeyboardBuilder()
    btn.button(text="✔︎ Ha", callback_data="confirm_data")
    btn.button(text="✖︎ Yo'q", callback_data="cancel_data")
    btn.adjust(2)
    return btn.as_markup()


async def cashier_confirm_button(transaction_id, doc_id):
    btn = InlineKeyboardBuilder()
    btn.button(text="✔︎ Tasdiqlash", callback_data=f"chief_confirm_{transaction_id}|{doc_id}")
    btn.button(text="✖︎ Rad etish", callback_data=f"chief_reject_{transaction_id}|{doc_id}")
    btn.adjust(2)
    return btn.as_markup()


async def cashier_menu_button():
    btn = InlineKeyboardBuilder()
    btn.button(text="﹩ Balans", callback_data="balance_info")
    btn.button(text="⎘ Sverka", callback_data="conclusion")
    btn.adjust(1)
    return btn.as_markup()


async def choose_terminal_button():
    btn = InlineKeyboardBuilder()
    btn.button(text="💳 Uzcard", callback_data="uz_card")
    btn.button(text="💳 Humo", callback_data="humo")
    btn.button(text="◁ Orqaga", callback_data='back')
    btn.adjust(2)
    return btn.as_markup()


async def check_password_button():
    btn = InlineKeyboardBuilder()
    btn.button(text="🔍 Tekshirish", callback_data="check_password")
    btn.adjust(1)
    return btn.as_markup()


async def back_button():
    btn = InlineKeyboardBuilder()
    btn.button(text="◁ Orqaga", callback_data='back')
    btn.adjust(2)
    return btn.as_markup()


async def back_or_skip_button():
    btn = InlineKeyboardBuilder()
    btn.button(text="◁ Orqaga", callback_data='back')
    btn.button(text="➡️ O'tkazib yuborish", callback_data='skip')
    btn.adjust(2)
    return btn.as_markup()


async def position_button():
    btn = InlineKeyboardBuilder()
    btn.button(text="Bosh kassir", callback_data="chief_cashier")
    btn.button(text="Kassir", callback_data="cashier")
    btn.button(text="◁ Orqaga", callback_data='back')
    btn.adjust(2)
    return btn.as_markup()


def create_pagination_keyboard(
        transactions: List[CardTransaction],
        current_page: int,
        page_size: int = 5
):
    """
    Tranzaksiyalar uchun paginatsiyali inline klaviatura yaratadi.
    Tugmalar: [⬅️ Orqaga] [joriy_sahifa/jami_sahifa] [➡️ Oldinga]
    """
    total_transactions = len(transactions)
    total_pages = (total_transactions + page_size - 1) // page_size

    start_index = current_page * page_size
    end_index = min(start_index + page_size, total_transactions)

    keyboard = InlineKeyboardBuilder()

    # Tranzaksiya tugmalarini har biri alohida qatorga joylashtirish
    for i in range(start_index, end_index):
        transaction = transactions[i]
        name = f"№ {transaction.transaction_id} | {transaction.amount} so'm"
        callback_data = f"view_transaction:{transaction.id}"
        keyboard.add(InlineKeyboardButton(text=name, callback_data=callback_data))

    # Tranzaksiya tugmalarini har bir qatorga bittadan qilib taqsimlash
    keyboard.adjust(1)

    # Navigatsiya tugmalari uchun alohida qator yaratish
    nav_buttons = []

    # Birinchi sahifada bo'lmasa, "Orqaga" tugmasini qo'shish
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"page:{current_page - 1}"))

    # Har doim sahifa raqamini ko'rsatish
    nav_buttons.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="none"))

    # Oxirgi sahifada bo'lmasa, "Oldinga" tugmasini qo'shish
    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Oldinga", callback_data=f"page:{current_page + 1}"))

    # Navigatsiya tugmalarini bir qatorga joylashtirish, faqat agar ular mavjud bo'lsa
    if nav_buttons:
        keyboard.row(*nav_buttons)

    return keyboard.as_markup()