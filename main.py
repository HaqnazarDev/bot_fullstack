import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8247617435:AAGu-EOFrQO8Uss0Y-xnJbh99eBBVMu_FHI")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Salom, {hbold(message.from_user.full_name)}!",
        parse_mode="HTML"
    )


@dp.message(F.text)
async def handle_text(message: Message):
    await message.answer(f"👋 Salom, {hbold(message.from_user.full_name)}!", parse_mode="HTML")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

