"""Anti-spam: flood detection, repeated messages, suspicious links."""

import re
import time
import logging
from collections import defaultdict, deque

from telegram import Update, Chat
from telegram.ext import ContextTypes
from telegram.error import TelegramError

import storage

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
FLOOD_MAX_MESSAGES = 6       # messages
FLOOD_WINDOW_SECS  = 5       # in this many seconds
FLOOD_MUTE_MINS    = 5       # mute duration on flood
REPEAT_MAX         = 3       # same message count to trigger
REPEAT_WINDOW      = 10      # seconds to track repeats
MAX_WARNINGS_SPAM  = 3       # warnings before auto-ban

# ── Suspicious link patterns ──────────────────────────────────────────────────
_LINK_PATTERNS = re.compile(
    r"(t\.me/joinchat|t\.me/\+|bit\.ly|tinyurl\.com|goo\.gl|rb\.gy|ow\.ly|short\.link)",
    re.IGNORECASE,
)

# Bad words list (normalized Azerbaijani profanity triggers)
BAD_WORDS = [
    "sik", "got", "orospu", "fahişə", "lahşa", "piç", "qancıq",
    "amcıq", "kus", "məzəllət", "dəyyus", "şərəfsiz", "murdar",
    "qaltaq", "cəhənnəm", "haram", "it balası",
]

# ── In-memory tracking ────────────────────────────────────────────────────────
# {(chat_id, user_id): deque of timestamps}
_flood_tracker: dict[tuple, deque] = defaultdict(lambda: deque(maxlen=20))

# {(chat_id, user_id): (last_text, count, last_time)}
_repeat_tracker: dict[tuple, tuple] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_suspicious_link(text: str) -> bool:
    return bool(_LINK_PATTERNS.search(text))


def _has_bad_word(text: str) -> bool:
    low = text.lower()
    return any(w in low for w in BAD_WORDS)


def _check_flood(chat_id: int, user_id: int) -> bool:
    key = (chat_id, user_id)
    now = time.time()
    q = _flood_tracker[key]
    q.append(now)
    # Count messages within window
    recent = [t for t in q if now - t <= FLOOD_WINDOW_SECS]
    return len(recent) >= FLOOD_MAX_MESSAGES


def _check_repeat(chat_id: int, user_id: int, text: str) -> bool:
    key = (chat_id, user_id)
    now = time.time()
    prev = _repeat_tracker.get(key)
    if prev:
        last_text, count, last_time = prev
        if text == last_text and now - last_time <= REPEAT_WINDOW:
            count += 1
            _repeat_tracker[key] = (text, count, now)
            return count >= REPEAT_MAX
    _repeat_tracker[key] = (text, 1, now)
    return False


async def _silent_delete(update: Update) -> bool:
    try:
        await update.message.delete()
        return True
    except TelegramError:
        return False


async def _mute_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int,
                     minutes: int) -> None:
    from datetime import datetime, timedelta, timezone
    from telegram import ChatPermissions
    from moderation import MUTED_PERMS
    until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    try:
        await context.bot.restrict_chat_member(chat_id, user_id, MUTED_PERMS, until_date=until)
    except TelegramError:
        pass


async def _warn_or_ban(update: Update, context: ContextTypes.DEFAULT_TYPE,
                       user, reason: str) -> None:
    chat_id = update.message.chat_id
    count = storage.add_warning(chat_id, user.id)

    if count >= MAX_WARNINGS_SPAM:
        try:
            await context.bot.ban_chat_member(chat_id, user.id)
            storage.reset_warnings(chat_id, user.id)
            await update.message.reply_text(
                f"🚫 *{user.full_name}* ban edildi. ({reason})",
                parse_mode="Markdown",
            )
        except TelegramError:
            pass
    else:
        await update.message.reply_text(
            f"⚠️ *{user.full_name}*, {reason}!\n"
            f"Xəbərdarlıq: {count}/{MAX_WARNINGS_SPAM}",
            parse_mode="Markdown",
        )


# ── Main antispam handler ─────────────────────────────────────────────────────

async def antispam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs in group -1, before all other handlers."""
    msg = update.message
    if not msg or not msg.text:
        return
    if msg.chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
        return

    from moderation import is_admin
    user = msg.from_user
    if not user or user.is_bot:
        return
    if await is_admin(context.bot, msg.chat_id, user.id):
        return  # Admins are exempt

    text = msg.text.strip()

    # ── Flood detection ───────────────────────────────────────────────────────
    if _check_flood(msg.chat_id, user.id):
        await _silent_delete(update)
        await _mute_user(context, msg.chat_id, user.id, FLOOD_MUTE_MINS)
        await msg.reply_text(
            f"🌊 *{user.full_name}*, flood etmə! {FLOOD_MUTE_MINS} dəqiqəlik susduruldun.",
            parse_mode="Markdown",
        )
        return

    # ── Repeated message detection ─────────────────────────────────────────────
    if _check_repeat(msg.chat_id, user.id, text):
        await _silent_delete(update)
        await _warn_or_ban(update, context, user, "eyni mesajı təkrarlamaq")
        return

    # ── Suspicious links ───────────────────────────────────────────────────────
    if _is_suspicious_link(text):
        await _silent_delete(update)
        await _warn_or_ban(update, context, user, "şübhəli link göndərmək")
        return

    # ── Bad words ──────────────────────────────────────────────────────────────
    if _has_bad_word(text):
        await _silent_delete(update)
        await _warn_or_ban(update, context, user, "nalayiq söz işlətmək")
        return
