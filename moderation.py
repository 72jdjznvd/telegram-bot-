"""Admin-only moderation commands: warn, mute, unmute, ban, unban, kick, rules."""

import logging
from datetime import datetime, timedelta, timezone

from telegram import Update, ChatPermissions, Chat
from telegram.ext import ContextTypes
from telegram.error import TelegramError

import storage

logger = logging.getLogger(__name__)

MAX_WARNINGS = 3

# Fully restricted permissions (mute)
MUTED_PERMS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

async def is_admin(bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except TelegramError:
        return False


async def get_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return (user, error_str). Checks reply-to first, then @mention in args."""
    msg = update.message
    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user, None
    if context.args:
        raw = context.args[0].lstrip("@")
        try:
            chat_member = await context.bot.get_chat_member(msg.chat_id, raw)
            return chat_member.user, None
        except TelegramError:
            pass
    return None, "❌ Hədəf istifadəçini göstər: cavab ver və ya @istifadəçi yaz."


async def _not_admin(update: Update) -> None:
    await update.message.reply_text("⛔ Bu əmr yalnız adminlər üçündür.")


# ── /warn ─────────────────────────────────────────────────────────────────────

async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if msg.chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
        return

    if not await is_admin(context.bot, msg.chat_id, msg.from_user.id):
        await _not_admin(update)
        return

    target, err = await get_target(update, context)
    if err:
        await msg.reply_text(err)
        return

    if target.is_bot:
        await msg.reply_text("🤖 Botlara xəbərdarlıq edilmir.")
        return

    if await is_admin(context.bot, msg.chat_id, target.id):
        await msg.reply_text("⚠️ Adminə xəbərdarlıq edilmir.")
        return

    reason = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else "Səbəb göstərilmədi"
    count = storage.add_warning(msg.chat_id, target.id)

    text = (
        f"⚠️ *{target.full_name}* xəbərdar edildi!\n"
        f"📋 Səbəb: {reason}\n"
        f"🔢 Xəbərdarlıq: {count}/{MAX_WARNINGS}"
    )

    if count >= MAX_WARNINGS:
        try:
            await context.bot.ban_chat_member(msg.chat_id, target.id)
            storage.reset_warnings(msg.chat_id, target.id)
            text += f"\n\n🚫 {count} xəbərdarlıqdan sonra *{target.full_name}* qrupdan çıxarıldı!"
        except TelegramError as e:
            text += f"\n\n❌ Ban edilə bilmədi: {e}"

    await msg.reply_text(text, parse_mode="Markdown")


# ── /mute ─────────────────────────────────────────────────────────────────────

async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if msg.chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
        return

    if not await is_admin(context.bot, msg.chat_id, msg.from_user.id):
        await _not_admin(update)
        return

    target, err = await get_target(update, context)
    if err:
        await msg.reply_text(err)
        return

    if await is_admin(context.bot, msg.chat_id, target.id):
        await msg.reply_text("⚠️ Adminə mute edilmir.")
        return

    # Parse optional duration (minutes), default 60
    duration_min = 60
    for arg in (context.args or []):
        if arg.isdigit():
            duration_min = max(1, min(int(arg), 10080))  # cap at 7 days
            break

    until = datetime.now(timezone.utc) + timedelta(minutes=duration_min)
    try:
        await context.bot.restrict_chat_member(msg.chat_id, target.id, MUTED_PERMS, until_date=until)
        await msg.reply_text(
            f"🔇 *{target.full_name}* {duration_min} dəqiqəlik susduruldu.",
            parse_mode="Markdown",
        )
    except TelegramError as e:
        await msg.reply_text(f"❌ Mute edilə bilmədi: {e}")


# ── /unmute ───────────────────────────────────────────────────────────────────

async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if msg.chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
        return

    if not await is_admin(context.bot, msg.chat_id, msg.from_user.id):
        await _not_admin(update)
        return

    target, err = await get_target(update, context)
    if err:
        await msg.reply_text(err)
        return

    default_perms = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
    )
    try:
        await context.bot.restrict_chat_member(msg.chat_id, target.id, default_perms)
        await msg.reply_text(
            f"🔊 *{target.full_name}* artıq danışa bilər.",
            parse_mode="Markdown",
        )
    except TelegramError as e:
        await msg.reply_text(f"❌ Unmute edilə bilmədi: {e}")


# ── /ban ──────────────────────────────────────────────────────────────────────

async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if msg.chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
        return

    if not await is_admin(context.bot, msg.chat_id, msg.from_user.id):
        await _not_admin(update)
        return

    target, err = await get_target(update, context)
    if err:
        await msg.reply_text(err)
        return

    if await is_admin(context.bot, msg.chat_id, target.id):
        await msg.reply_text("⚠️ Adminə ban edilmir.")
        return

    reason = " ".join(context.args[1:]) if context.args and len(context.args) > 1 else "Səbəb göstərilmədi"
    try:
        await context.bot.ban_chat_member(msg.chat_id, target.id)
        storage.reset_warnings(msg.chat_id, target.id)
        await msg.reply_text(
            f"🚫 *{target.full_name}* qrupdan ban edildi.\n📋 Səbəb: {reason}",
            parse_mode="Markdown",
        )
    except TelegramError as e:
        await msg.reply_text(f"❌ Ban edilə bilmədi: {e}")


# ── /unban ────────────────────────────────────────────────────────────────────

async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if msg.chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
        return

    if not await is_admin(context.bot, msg.chat_id, msg.from_user.id):
        await _not_admin(update)
        return

    target, err = await get_target(update, context)
    if err:
        await msg.reply_text(err)
        return

    try:
        await context.bot.unban_chat_member(msg.chat_id, target.id, only_if_banned=True)
        await msg.reply_text(
            f"✅ *{target.full_name}* qruba qayıda bilər.",
            parse_mode="Markdown",
        )
    except TelegramError as e:
        await msg.reply_text(f"❌ Unban edilə bilmədi: {e}")


# ── /kick ─────────────────────────────────────────────────────────────────────

async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if msg.chat.type not in (Chat.GROUP, Chat.SUPERGROUP):
        return

    if not await is_admin(context.bot, msg.chat_id, msg.from_user.id):
        await _not_admin(update)
        return

    target, err = await get_target(update, context)
    if err:
        await msg.reply_text(err)
        return

    if await is_admin(context.bot, msg.chat_id, target.id):
        await msg.reply_text("⚠️ Adminə kick edilmir.")
        return

    try:
        await context.bot.ban_chat_member(msg.chat_id, target.id)
        await context.bot.unban_chat_member(msg.chat_id, target.id)
        await msg.reply_text(
            f"👢 *{target.full_name}* qrupdan çıxarıldı.",
            parse_mode="Markdown",
        )
    except TelegramError as e:
        await msg.reply_text(f"❌ Kick edilə bilmədi: {e}")


# ── /rules ────────────────────────────────────────────────────────────────────

async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    chat_id = msg.chat_id

    # Admin can set rules: /rules set <text>
    if context.args and context.args[0].lower() == "set":
        if not await is_admin(context.bot, chat_id, msg.from_user.id):
            await _not_admin(update)
            return
        new_rules = " ".join(context.args[1:]).strip()
        if not new_rules:
            await msg.reply_text("❌ Qaydaları yaz: /rules set <mətni>")
            return
        storage.set_rules(chat_id, new_rules)
        await msg.reply_text("✅ Qrup qaydaları yadda saxlanıldı!")
        return

    rules = storage.get_rules(chat_id)
    if rules:
        await msg.reply_text(f"📜 *Qrup Qaydaları:*\n\n{rules}", parse_mode="Markdown")
    else:
        await msg.reply_text(
            "📜 *Ümumi Qrup Qaydaları:*\n\n"
            "1. Bir-birinə hörmətlə yanaşın.\n"
            "2. Spam və reklam qadağandır.\n"
            "3. Küfür və söyüş qadağandır.\n"
            "4. Şəxsi hücumlar qadağandır.\n"
            "5. Adminlərin qərarlarına əməl edin.\n\n"
            "_Adminlər /rules set <mətni> ilə öz qaydalarını yaza bilər._",
            parse_mode="Markdown",
        )
