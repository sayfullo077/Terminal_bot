from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData
from typing import List
from database.models import CardTransaction
from math import ceil


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


async def chief_cashier_menu_button():
    btn = InlineKeyboardBuilder()
    btn.button(text="﹩ Balans", callback_data="balance_info")
    btn.button(text="⎘ Sverkalar ro'yxati", callback_data="cash_list")
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
    total_transactions = len(transactions)
    total_pages = (total_transactions + page_size - 1) // page_size
    start_index = current_page * page_size
    end_index = min(start_index + page_size, total_transactions)
    keyboard = InlineKeyboardBuilder()

    for i in range(start_index, end_index):
        transaction = transactions[i]
        name = f"№ {transaction.transaction_id} | {transaction.amount} so'm"
        callback_data = f"view_transaction:{transaction.id}"
        keyboard.add(InlineKeyboardButton(text=name, callback_data=callback_data))

    keyboard.adjust(1)
    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"page:{current_page - 1}"))

    nav_buttons.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="none"))

    if current_page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Oldinga", callback_data=f"page:{current_page + 1}"))

    if nav_buttons:
        keyboard.row(*nav_buttons)

    return keyboard.as_markup()


def build_cash_pagination_keyboard(all_cash: list, all_terminal: list, page: int = 1, per_page: int = 7):
    all_cashiers = []

    for cash in all_cash:
        cash_name = cash.get("cash_name")
        cash_id = cash.get("cash_id")
        if cash_name and cash_id is not None:
            all_cashiers.append({
                "cash_name": cash_name,
                "cash_id": cash_id,
                "cash_type": "naqd"
            })

    for terminal in all_terminal:
        cash_name = terminal.get("cash_name")
        cash_id = terminal.get("cash_id")
        if cash_name and cash_id is not None:
            all_cashiers.append({
                "cash_name": cash_name,
                "cash_id": cash_id,
                "cash_type": "terminal"
            })
    
    total_items = len(all_cashiers)
    total_pages = ceil(total_items / per_page)

    start = (page - 1) * per_page
    end = start + per_page
    current_page_items = all_cashiers[start:end]
    
    keyboard = []

    for cash in current_page_items:
        cash_name = cash.get("cash_name")
        cash_id = cash.get("cash_id")
        cash_type = cash.get("cash_type")
        
        if cash_type == "naqd":
            text = f"💵 {cash_name}"
            callback_data = f"cash_naqd:{cash_id}"
        else:  # terminal
            text = f"💳 {cash_name}"
            callback_data = f"cash_terminal:{cash_id}"
            
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])

    nav_buttons = []

    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⏮️ Bosh", callback_data="cash_page:1"))

    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"cash_page:{page-1}"))

    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="none"))

    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"cash_page:{page+1}"))

    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Oxirgi ⏭️", callback_data=f"cash_page:{total_pages}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="◁ Orqaga", callback_data="back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def build_balance_pagination_keyboard(all_cash: list, all_terminal: list, page: int = 1, per_page: int = 7):
    """
    Balance uchun kassalar ro'yxatini paginatsiya qilib InlineKeyboard qaytaradi.
    """
    all_cashiers = []

    for cash in all_cash:
        cash_name = cash.get("cash_name")
        cash_id = cash.get("cash_id")
        if cash_name and cash_id is not None:
            all_cashiers.append({
                "cash_name": cash_name,
                "cash_id": cash_id,
                "cash_type": "naqd"
            })

    for terminal in all_terminal:
        cash_name = terminal.get("cash_name")
        cash_id = terminal.get("cash_id")
        if cash_name and cash_id is not None:
            all_cashiers.append({
                "cash_name": cash_name,
                "cash_id": cash_id,
                "cash_type": "terminal"
            })

    total_items = len(all_cashiers)
    total_pages = ceil(total_items / per_page)

    start = (page - 1) * per_page
    end = start + per_page
    current_page_items = all_cashiers[start:end]
    
    keyboard = []

    for cash in current_page_items:
        cash_name = cash.get("cash_name")
        cash_id = cash.get("cash_id")
        cash_type = cash.get("cash_type")
        
        if cash_type == "naqd":
            text = f"💵 {cash_name}"
            callback_data = f"balance_naqd:{cash_id}"
        else:  # terminal
            text = f"💳 {cash_name}"
            callback_data = f"balance_terminal:{cash_id}"
            
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])

    nav_buttons = []

    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⏮️ Bosh", callback_data="balance_page:1"))

    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"balance_page:{page-1}"))

    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="none"))

    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"balance_page:{page+1}"))

    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Oxirgi ⏭️", callback_data=f"balance_page:{total_pages}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="◁ Orqaga", callback_data="back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)