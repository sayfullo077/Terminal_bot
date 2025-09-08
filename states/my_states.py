from aiogram.filters.state import State, StatesGroup


class UserStart(StatesGroup):
    start = State()
    company = State()
    branch = State()
    selected_user = State()
    password = State()
    cashier_menu = State()
    cash_detail = State()
    is_active = State()
    check = State()


class UserState(StatesGroup):
    companies = State()
    main_menu = State()


class TransactionState(StatesGroup):
    transaction_menu = State()
    transfer_photo = State()
    transfer_comment = State()
    transfer_amount = State()
    select_destination = State()
    confirm_transfer = State()
    pending_chief_cashier = State()
    select_cash = State()
    confirm = State()
    cash_pagination = State()


class TextAdd(StatesGroup):
    text = State()
    url = State()
    send = State()
    check = State()


class ImageAdd(StatesGroup):
    image = State()
    url = State()
    send = State()
    check = State()


class VideoAdd(StatesGroup):
    video = State()
    url = State()
    send = State()
    check = State()


class MusicAdd(StatesGroup):
    music = State()
    url = State()
    send = State()
    check = State()


class AdminState(StatesGroup):
    admin_menu = State()
    admin_get = State()
    admin_username = State()
    confirm_admin = State()
    check = State()


class CompanyState(StatesGroup):
    main_menu = State()
    delete = State()
    check = State()


class CompanyAdd(StatesGroup):
    branch_link = State()
    terminal_link = State()
    login = State()
    password = State()
    check = State()


class CompanyEdit(StatesGroup):
    list = State()
    edit_menu = State()
    name = State()
    branch_link = State()
    terminal_link = State()
    login = State()
    password = State()


class ChannelState(StatesGroup):
    channel_menu = State()


class ChannelAdd(StatesGroup):
    category = State()
    channel_id = State()
    check = State()
    channel_menu = State()


class ChannelDeleteState(StatesGroup):
    category = State()
    channel_id = State()
    check = State()


class BotInfoState(StatesGroup):
    bot_info = State()


class AdState(StatesGroup):
    ad_menu = State()


class TransferState(StatesGroup):
    transfer_menu = State()
    company = State()
    crud_menu = State()
    transfer_list = State()


class BranchState(StatesGroup):
    branch_menu = State()
    company = State()
    list = State()
    delete = State()
    check = State()


class BranchAdd(StatesGroup):
    company = State()
    name = State()
    cashier_url = State()
    chief_cashier_url = State()
    check_pass_url = State()
    transaction_url = State()
    get_transaction_url = State()
    check_transaction_url = State()
    login = State()
    password = State()
    check = State()


class BranchEdit(StatesGroup):
    company = State()
    select = State()
    cashier_link = State()
    chief_cashier_link = State()
    check_pass_link = State()
    transaction_link = State()
    get_transaction_link = State()
    check_transaction_link = State()
    edit_menu = State()
    name = State()
    login = State()
    password = State()
    check = State()