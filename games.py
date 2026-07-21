"""Games: /dice, /coin, /8ball, /guess, /math."""

import random
import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# ── Per-chat game state (in memory) ──────────────────────────────────────────
# {chat_id: {"type": "guess"|"math", "answer": int, "attempts": int}}
_game_state: dict[int, dict] = {}

EIGHTBALL_REPLIES = [
    "✅ Bəli, əlbəttə!",
    "✅ Şübhəsiz ki, belədir.",
    "✅ Buna inanmaq olar.",
    "✅ Fikrimcə, bəli.",
    "✅ Hər şey işarə edir ki, bəli.",
    "🌫️ Cavab aydın deyil, yenidən soruş.",
    "🌫️ İndi proqnoz vermək çətindir.",
    "🌫️ Diqqətini cəmlə və yenidən soruş.",
    "🌫️ Hələ deməmək olar.",
    "🌫️ İndi cavab vermək mənim üçün çətindir.",
    "❌ Fikrimcə, xeyr.",
    "❌ Mənbələrim xeyr deyir.",
    "❌ Bunun üzərindən say.",
    "❌ Perspektivlər yaxşı görünmür.",
    "❌ Çox şübhəlidir.",
]


# ── /dice ─────────────────────────────────────────────────────────────────────

async def cmd_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = random.randint(1, 6)
    faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    await update.message.reply_text(
        f"🎲 Zər atıldı: *{faces[result - 1]} {result}*",
        parse_mode="Markdown",
    )


# ── /coin ─────────────────────────────────────────────────────────────────────

async def cmd_coin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = random.choice([("🦅 Yazı", "Yazı"), ("🔵 Kənar", "Kənar")])
    await update.message.reply_text(f"🪙 Sikkə atıldı: *{result[0]}*!", parse_mode="Markdown")


# ── /8ball ────────────────────────────────────────────────────────────────────

async def cmd_8ball(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("🎱 Sual yaz: `/8ball Sabah yağış yağacaq?`", parse_mode="Markdown")
        return
    question = " ".join(context.args)
    reply = random.choice(EIGHTBALL_REPLIES)
    await update.message.reply_text(
        f"🎱 *Sual:* {question}\n\n*Cavab:* {reply}",
        parse_mode="Markdown",
    )


# ── /guess ────────────────────────────────────────────────────────────────────

async def cmd_guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    _game_state[chat_id] = {
        "type": "guess",
        "answer": random.randint(1, 100),
        "attempts": 0,
    }
    await update.message.reply_text(
        "🔢 *Ədad tapmaca oyunu başladı!*\n\n"
        "1 ilə 100 arasında bir ədad düşündüm. Tapabilərsən? 🤔\n"
        "_Oyunu bitirmək üçün /stop yaz._",
        parse_mode="Markdown",
    )


# ── /math ─────────────────────────────────────────────────────────────────────

async def cmd_math(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    ops = ["+", "-", "*"]
    op = random.choice(ops)
    if op == "+":
        a, b = random.randint(1, 100), random.randint(1, 100)
        answer = a + b
        sym = "+"
    elif op == "-":
        a, b = random.randint(10, 100), random.randint(1, 50)
        answer = a - b
        sym = "−"
    else:
        a, b = random.randint(2, 12), random.randint(2, 12)
        answer = a * b
        sym = "×"

    _game_state[chat_id] = {"type": "math", "answer": answer, "attempts": 0}
    await update.message.reply_text(
        f"🧮 *Riyaziyyat sualı:*\n\n`{a} {sym} {b} = ?`\n\n_Cavabı yaz!_",
        parse_mode="Markdown",
    )


# ── /stop ─────────────────────────────────────────────────────────────────────

async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    game = _game_state.pop(chat_id, None)
    if game:
        await update.message.reply_text(
            f"🛑 Oyun dayandırıldı. Cavab: *{game['answer']}* idi.",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("🎮 Aktiv oyun yoxdur.")


# ── Game message interceptor ───────────────────────────────────────────────────

async def handle_game_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Call from the main message handler. Returns True if message was a game input
    and was handled (so the caller should not process it further).
    """
    chat_id = update.effective_chat.id
    game = _game_state.get(chat_id)
    if not game:
        return False

    text = update.message.text.strip()
    if not text.lstrip("-").isdigit():
        return False

    guess = int(text)
    answer = game["answer"]
    game["attempts"] += 1

    if game["type"] == "guess":
        if guess == answer:
            del _game_state[chat_id]
            await update.message.reply_text(
                f"🎉 *Doğru!* Ədad *{answer}* idi!\n"
                f"Cəhd sayı: *{game['attempts']}* 👏",
                parse_mode="Markdown",
            )
        elif game["attempts"] >= 10:
            del _game_state[chat_id]
            await update.message.reply_text(
                f"😔 10 cəhd bitdi. Ədad *{answer}* idi. Növbəti dəfə uğurlar!",
                parse_mode="Markdown",
            )
        elif guess < answer:
            await update.message.reply_text(f"📈 *{guess}* — daha böyük!", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"📉 *{guess}* — daha kiçik!", parse_mode="Markdown")
        return True

    if game["type"] == "math":
        if guess == answer:
            del _game_state[chat_id]
            await update.message.reply_text(
                f"✅ *Düzgün cavab!* {answer} idi! 🎉",
                parse_mode="Markdown",
            )
        else:
            if game["attempts"] >= 3:
                del _game_state[chat_id]
                await update.message.reply_text(
                    f"❌ Düzgün deyil. Cavab *{answer}* idi.",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    f"❌ Düzgün deyil. Yenidən cəhd et! ({game['attempts']}/3)",
                    parse_mode="Markdown",
                )
        return True

    return False
