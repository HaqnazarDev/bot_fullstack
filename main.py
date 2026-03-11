import asyncio
import logging
import os
from openai import AsyncOpenAI
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.markdown import hbold

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# === SOZLAMALAR ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "8247617435:AAGu-EOFrQO8Uss0Y-xnJbh99eBBVMu_FHI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
MODEL = "gpt-4o-mini"
MAX_HISTORY = 20

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

user_histories: dict[int, list[dict]] = {}

SYSTEM_PROMPT = """Sen foydali, aqlli va do'stona AI assistantsan.
Foydalanuvchi bilan o'zbek tilida muloqot qil (agar ular o'zbek tilida yozsa).
Agar boshqa tilda yozsalar, o'sha tilda javob ber.
Qisqa va aniq javoblar ber."""


def get_history(user_id: int) -> list[dict]:
    if user_id not in user_histories:
        user_histories[user_id] = []
    return user_histories[user_id]


def add_message(user_id: int, role: str, content: str):
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY * 2:
        user_histories[user_id] = history[-(MAX_HISTORY * 2):]


async def ask_openai(user_id: int, user_message: str) -> str:
    add_message(user_id, "user", user_message)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(user_id)
    try:
        response = await openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        add_message(user_id, "assistant", reply)
        return reply
    except Exception as e:
        if user_id in user_histories and user_histories[user_id]:
            user_histories[user_id].pop()
        raise e


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_histories[message.from_user.id] = []
    await message.answer(
        f"👋 Salom, {hbold(message.from_user.full_name)}!\n\n"
        f"🤖 Men <b>AI Assistant</b>man, <b>{MODEL}</b> modeli asosida ishlayman.\n\n"
        "💬 Menga istalgan savolingizni bering!\n\n"
        "📌 <b>Komandalar:</b>\n"
        "/start — Yangi suhbat boshlash\n"
        "/clear — Suhbat tarixini tozalash\n"
        "/help — Yordam",
        parse_mode="HTML"
    )


@dp.message(Command("clear"))
async def cmd_clear(message: Message):
    user_histories[message.from_user.id] = []
    await message.answer("🗑 Suhbat tarixi tozalandi! Yangi suhbat boshlashingiz mumkin.")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "Bu bot OpenAI <b>GPT-4o-mini</b> modeli orqali ishlaydi.\n\n"
        "<b>Komandalar:</b>\n"
        "/start — Yangi suhbat (tarix o'chadi)\n"
        "/clear — Suhbat tarixini tozalash\n"
        "/help — Shu yordam xabari\n\n"
        "<b>Xususiyatlar:</b>\n"
        "• Suhbat tarixini eslab qoladi\n"
        f"• Oxirgi {MAX_HISTORY} ta xabar xotirada saqlanadi\n"
        "• O'zbek va boshqa tillarda gaplasha oladi",
        parse_mode="HTML"
    )


@dp.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    user_text = message.text.strip()
    if not user_text:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        reply = await ask_openai(user_id, user_text)
        # HTML parse xatosini oldini olish uchun
        try:
            await message.answer(reply, parse_mode="HTML")
        except Exception:
            await message.answer(reply)

    except Exception as e:
        err_str = str(e).lower()
        if "rate_limit" in err_str or "rate limit" in err_str:
            await message.answer("⏳ So'rovlar juda ko'p. Biroz kuting va qayta urinib ko'ring.")
        elif "quota" in err_str or "insufficient" in err_str:
            await message.answer("❌ OpenAI API limitingiz tugagan. Hisobingizni tekshiring.")
        elif "invalid_api_key" in err_str or "auth" in err_str:
            await message.answer("❌ API kalit noto'g'ri. Bot sozlamalarini tekshiring.")
        else:
            await message.answer("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
            logger.error(f"Xato user {user_id}: {e}")


async def main():
    logger.info(f"Bot ishga tushmoqda... Model: {MODEL}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())