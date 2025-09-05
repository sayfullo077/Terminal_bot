from aiogram.filters import Command
from loader import dp
from aiogram import types


@dp.message(Command('help'))
async def help_bot(message: types.Message):
    await message.answer(f"Qanday yordam kerak?\n"
                         f"Asosiy buyruqlar: \n/start ♻️ Botni ishga tushirish\n"
                         f"/admin 🖥 Admin panel\n"
                         f"/feedback ✉️ Adminga xabar yuborish")
