from aiogram.filters import Filter
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import types
from data.config import ADMINS
from database.orm_query import get_admin_users


class IsBotOrAssistantAdmin(Filter):
    async def __call__(self, message: types.Message, session: AsyncSession) -> bool:
        telegram_id = message.from_user.id
        is_bot_admin = str(telegram_id) in ADMINS

        assistant_admins = await get_admin_users(session)
        admin_ids = [admin for admin in assistant_admins]
        is_assistant_admin = telegram_id in admin_ids

        return is_bot_admin or is_assistant_admin


# class IsBotAdmin(Filter):
#     async def __call__(self, message:types.Message) ->bool:
#         return str(message.from_user.id) in ADMINS
#
# class IsAssistantAdmin(Filter):
#     async def __call__(self, message: types.Message) -> bool:
#         assistant_admins = await db.select_all_admins()
#         admin_ids = [str(admin['telegram_id']) for admin in assistant_admins]
#         print("Assistant admin:", admin_ids)
#         return str(message.from_user.id) in admin_ids
