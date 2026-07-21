"""Utility and content commands: /help, /about, /time, /date, /ping, /joke, /fact, /quote, /love, /riddle."""

import random
import logging
from datetime import datetime, timezone, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from data import JOKES, FACTS, MOTIVATIONAL_QUOTES, LOVE_QUOTES, RIDDLES

logger = logging.getLogger(__name__)

BAKU_TZ = timezone(timedelta(hours=4))


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from chat import get_state
    state = get_state(update.effective_chat.id, update.effective_user.id)
    name_part = f", *{state['name']}*" if state.get("name") else ""
    await update.message.reply_text(
        f"Salam{name_part}! 👋 Mən *Chat Corner Bot*-am — qrupun köməkçisi! 🤖\n\n"
        "✅ Azərbaycan dilində söhbət\n"
        "🛡️ Qrup moderasiyası\n"
        "🎮 Oyunlar və əyləncə\n"
        "📢 Xoş gəldin sistemi\n\n"
        "Bütün komandalar üçün /help yaz.",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 *Chat Corner Bot — Tam Bələdçi*\n\n"

        "🛡️ *Moderasiya (yalnız adminlər):*\n"
        "/warn — İstifadəçini xəbərdar et\n"
        "/mute — Susudur (dəqiqə: /mute @ad 30)\n"
        "/unmute — Susdurmağı qaldır\n"
        "/ban — Qrupdan ban et\n"
        "/unban — Banı qaldır\n"
        "/kick — Qrupdan çıxar\n"
        "/rules — Qrup qaydaları (set ilə yazıla bilər)\n\n"

        "🎮 *Oyunlar:*\n"
        "/dice — Zər at 🎲\n"
        "/coin — Sikkə at 🪙\n"
        "/8ball — Sehrli 8-top 🎱\n"
        "/guess — Ədad tap oyunu 🔢\n"
        "/math — Riyaziyyat sualı 🧮\n"
        "/stop — Aktiv oyunu dayandır 🛑\n\n"

        "😄 *Əyləncə:*\n"
        "/ship — Uyğunluq faizi 💘\n"
        "/compliment — Kompliment 🌹\n"
        "/roast — Zarafat 🔥\n"
        "/truth — Həqiqət sualı 🫣\n"
        "/dare — Tapşırıq 😈\n\n"

        "📚 *Məzmun:*\n"
        "/joke — Zarafat 😄\n"
        "/fact — Maraqlı fakt 🧠\n"
        "/quote — Motivasiya 💪\n"
        "/love — Sevgi sitatı ❤️\n"
        "/riddle — Tapmaca 🤔\n\n"

        "⚙️ *Yardımçı:*\n"
        "/time — Bakı saatı 🕐\n"
        "/date — Tarix 📅\n"
        "/ping — Bot gecikmə 📡\n"
        "/about — Bot haqqında ℹ️\n"
        "/help — Bu menyu\n\n"

        "💬 *Söhbət:*\n"
        "• Azərbaycan dilində istənilən şey yaz\n"
        "• `Mənim adım Əlidir` — adını yadda saxlayıram\n"
        "• `Tapmaca`, `Zarafat et`, `Fakt de` — işləyir!",
        parse_mode="Markdown",
    )


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 *Chat Corner Bot haqqında*\n\n"
        "Azərbaycan dilində tam funksiyalı qrup köməkçisi.\n\n"
        "👨‍💻 *Yaradıcı:* İlkin\n"
        "🐍 *Texnologiya:* Python · python-telegram-bot\n\n"
        "📦 *Xüsusiyyətlər:*\n"
        "• 🛡️ Qrup moderasiyası (warn/mute/ban/kick)\n"
        "• 🚫 Anti-spam sistemi\n"
        "• 👋 Xoş gəldin/Veda mesajları\n"
        "• 💬 500+ söhbət şablonu\n"
        "• 🎮 5 oyun\n"
        "• 😄 5 əyləncə komandası\n"
        "• 📚 100 zarafat · 100 fakt · 100 sitat · 100 sevgi · 100 tapmaca\n"
        "• ⚠️ Xəbərdarlıq saxlama sistemi\n"
        "• 🧠 İstifadəçi adı yaddaşı\n\n"
        "Kömək üçün /help yaz! 😊",
        parse_mode="Markdown",
    )


async def cmd_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now(BAKU_TZ)
    await update.message.reply_text(
        f"🕐 *Bakı vaxtı:* `{now.strftime('%H:%M:%S')}`",
        parse_mode="Markdown",
    )


async def cmd_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now(BAKU_TZ)
    months = [
        "Yanvar", "Fevral", "Mart", "Aprel", "May", "İyun",
        "İyul", "Avqust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr",
    ]
    days = ["Bazar ertəsi", "Çərşənbə axşamı", "Çərşənbə",
            "Cümə axşamı", "Cümə", "Şənbə", "Bazar"]
    await update.message.reply_text(
        f"📅 *Bugünkü tarix:*\n\n"
        f"`{days[now.weekday()]}, {now.day} {months[now.month - 1]} {now.year}`",
        parse_mode="Markdown",
    )


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    import time
    start = time.time()
    msg = await update.message.reply_text("📡 Yoxlanılır...")
    latency = round((time.time() - start) * 1000)
    await msg.edit_text(f"🏓 *Pong!* Gecikməsi: `{latency}ms`", parse_mode="Markdown")


async def cmd_joke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("😄 " + random.choice(JOKES))


async def cmd_fact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🧠 *Maraqlı fakt:*\n\n" + random.choice(FACTS),
        parse_mode="Markdown",
    )


async def cmd_quote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "💪 *Motivasiya:*\n\n" + random.choice(MOTIVATIONAL_QUOTES),
        parse_mode="Markdown",
    )


async def cmd_love(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "❤️ *Sevgi sitatı:*\n\n" + random.choice(LOVE_QUOTES),
        parse_mode="Markdown",
    )


async def cmd_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from chat import get_state
    r = random.choice(RIDDLES)
    state = get_state(update.effective_chat.id, update.effective_user.id)
    state["pending_riddle"] = r["a"]
    await update.message.reply_text(
        f"🤔 *Tapmaca:*\n\n{r['q']}\n\n_Cavabı bildin? Yaz:_ `cavab`",
        parse_mode="Markdown",
    )
