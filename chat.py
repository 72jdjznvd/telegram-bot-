"""Natural language chat handler — intent detection → keyword patterns → fallback."""

import re
import random
import logging
from collections import deque

from telegram import Update
from telegram.ext import ContextTypes

from patterns import PATTERNS
from data import JOKES, FACTS, MOTIVATIONAL_QUOTES, LOVE_QUOTES, RIDDLES
from intents import detect_intent
from az_normalize import normalize_az, _nl

# Pre-normalize all pattern triggers at load time so they match az-normalized input.
_NORM_PATTERNS = [
    {**pat, "triggers": _nl(pat["triggers"])}
    for pat in PATTERNS
]

logger = logging.getLogger(__name__)

# ── Per-user state: {(chat_id, user_id): {name, history, pending_riddle}} ────
_state: dict[tuple, dict] = {}

FALLBACKS = [
    "Bir az ətraflı izah edə bilərsən?",
    "Bunu tam başa düşmədim, fərqli şəkildə yaza bilərsən?",
    "Hələ bunu bilmirəm, amma öyrənirəm.",
    "Gəl başqa mövzudan danışaq.",
    "Bu sual məni düşündürdü. Daha aydın izah edə bilərsən?",
    "Dürüst deyim, buna hələ cavabım yoxdur.",
    "Hm, anlayıram nə demək istəyirsən, amma bu dəfə cavab verə bilmirəm.",
    "Maraqlı sual. Bunu araşdırmaq lazımdır.",
    "Başqa cür yaza bilərsən, bəlkə daha yaxşı başa düşəm.",
    "Hələ bu mövzuda məlumatım azdır, üzr istəyirəm.",
    "Bu mənim üçün çətin sualdır. Başqa sual ver, kömək edim.",
    "Anlamadım düzünü desəm. Bir daha yaza bilərsən?",
]


def get_state(chat_id: int, user_id: int) -> dict:
    key = (chat_id, user_id)
    if key not in _state:
        _state[key] = {"name": None, "history": deque(maxlen=10)}
    return _state[key]


def normalize(text: str) -> str:
    text = normalize_az(text)          # lowercase + ə→e  ı→i  ö→o  ü→u  ğ→g  ş→s  ç→c
    text = text.strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    return text


def matches(norm_text: str, keywords: list[str]) -> bool:
    return any(kw in norm_text for kw in keywords)


def extract_name(text: str):
    patterns = [
        r"m[əe]nim ad[ıi]m\s+(\S+)",
        r"ad[ıi]m\s+(\S+)",
        r"menim adim\s+(\S+)",
        r"məni\s+(\S+)\s+çağır",
        r"meni\s+(\S+)\s+cagiir",
    ]
    t = normalize(text)
    for p in patterns:
        m = re.search(p, t)
        if m:
            return m.group(1).strip().capitalize()
    return None


def match_pattern(norm_text: str):
    for pat in _NORM_PATTERNS:
        if matches(norm_text, pat["triggers"]):
            return random.choice(pat["replies"])
    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.text:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    text = msg.text.strip()
    norm = normalize(text)

    state = get_state(chat_id, user.id)
    state["history"].append({"role": "user", "text": text})

    # In groups, only respond if bot is mentioned or it's a private chat
    from telegram import Chat
    if update.effective_chat.type in (Chat.GROUP, Chat.SUPERGROUP):
        bot_username = (await context.bot.get_me()).username
        mentioned = (
            f"@{bot_username}".lower() in text.lower()
            or (msg.reply_to_message and msg.reply_to_message.from_user
                and msg.reply_to_message.from_user.id == context.bot.id)
        )
        # Check game input first (always handled regardless of mention)
        from games import handle_game_input
        if await handle_game_input(update, context):
            return
        if not mentioned:
            return
        # Strip bot mention from text before processing
        text = re.sub(rf"@{re.escape(bot_username)}", "", text, flags=re.IGNORECASE).strip()
        norm = normalize(text)
    else:
        # Private chat — still check game input first
        from games import handle_game_input
        if await handle_game_input(update, context):
            return

    # ── Riddle answer ─────────────────────────────────────────────────────────
    if "pending_riddle" in state and matches(norm, ["cavab", "bilmirəm", "bilmirem",
                                                     "nədir", "nedir", "de gorüm", "de görüm"]):
        reply = state.pop("pending_riddle")
        await msg.reply_text(f"💡 Cavab: *{reply}*", parse_mode="Markdown")
        return

    # ── Name: set ─────────────────────────────────────────────────────────────
    extracted = extract_name(text)
    if extracted and "?" not in text:
        state["name"] = extracted
        await msg.reply_text(
            f"Tamam, adını yadda saxladım: *{extracted}* 😊",
            parse_mode="Markdown",
        )
        return

    # ── Name: get ─────────────────────────────────────────────────────────────
    if "?" in text and matches(norm, ["adım nədir", "adim nedir", "adım ne",
                                       "mənim adım", "menim adim"]):
        if state.get("name"):
            await msg.reply_text(
                f"Sənin adın *{state['name']}*dir. 😊",
                parse_mode="Markdown",
            )
        else:
            await msg.reply_text("Hələ adını mənə deməmisən. 'Mənim adım [ad]' yaz, yadda saxlayım! 😊")
        return

    # ── Keyword shortcuts ─────────────────────────────────────────────────────
    if matches(norm, ["zarafat et", "zarafat", "lətifə", "letife"]):
        await msg.reply_text("😄 " + random.choice(JOKES))
        return

    if matches(norm, ["maraqlı fakt", "maraqli fakt", "fakt de", "bir fakt"]):
        await msg.reply_text("🧠 *Maraqlı fakt:*\n\n" + random.choice(FACTS), parse_mode="Markdown")
        return

    if matches(norm, ["motivasiya", "həvəsləndir", "ruhlandır", "sitat"]):
        await msg.reply_text("💪 *Motivasiya:*\n\n" + random.choice(MOTIVATIONAL_QUOTES), parse_mode="Markdown")
        return

    if matches(norm, ["sevgi sitatı", "sevgi sitati", "məhəbbət sitatı", "love quote"]):
        await msg.reply_text("❤️ *Sevgi sitatı:*\n\n" + random.choice(LOVE_QUOTES), parse_mode="Markdown")
        return

    if matches(norm, ["tapmaca", "tapmaça", "bir tapmaca", "bulmaca", "muamma"]):
        r = random.choice(RIDDLES)
        state["pending_riddle"] = r["a"]
        await msg.reply_text(
            f"🤔 *Tapmaca:*\n\n{r['q']}\n\n_Cavabı bildin? Yaz:_ `cavab`",
            parse_mode="Markdown",
        )
        return

    # ── Intent detection (structure-aware, before keyword patterns) ───────────
    reply = detect_intent(norm)

    # ── Keyword pattern matching (fallback when no intent matched) ─────────────
    if reply is None:
        reply = match_pattern(norm)

    # Personalise greetings if name is known
    if reply and state.get("name") and ("Salam!" in reply or "Hey!" in reply):
        reply = reply.replace("Salam!", f"Salam, *{state['name']}*!").replace(
            "Hey!", f"Hey, *{state['name']}*!"
        )

    # ── Fallback ──────────────────────────────────────────────────────────────
    if reply is None:
        reply = random.choice(FALLBACKS)

    await msg.reply_text(
        reply,
        parse_mode="Markdown" if "*" in reply else None,
    )
