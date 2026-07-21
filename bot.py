"""Chat Corner Bot — Full Azerbaijani Group Assistant."""

import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ── Modules ───────────────────────────────────────────────────────────────────
from commands import (
    cmd_start, cmd_help, cmd_about,
    cmd_time, cmd_date, cmd_ping,
    cmd_joke, cmd_fact, cmd_quote, cmd_love, cmd_riddle,
)
from moderation import (
    cmd_warn, cmd_mute, cmd_unmute,
    cmd_ban, cmd_unban, cmd_kick, cmd_rules,
)
from games import cmd_dice, cmd_coin, cmd_8ball, cmd_guess, cmd_math, cmd_stop
from fun import cmd_ship, cmd_compliment, cmd_roast, cmd_truth, cmd_dare
from welcome import welcome_handler, goodbye_handler
from antispam import antispam_handler
from chat import handle_message

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN mühit dəyişəni təyin edilməyib. "
            "Replit Secrets bölməsindən əlavə et."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    # ── Group -1: Anti-spam (runs before everything, can stop propagation) ────
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, antispam_handler),
        group=-1,
    )

    # ── Group 0: Welcome / Goodbye ────────────────────────────────────────────
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye_handler))

    # ── Group 0: Utility commands ─────────────────────────────────────────────
    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("help",       cmd_help))
    app.add_handler(CommandHandler("about",      cmd_about))
    app.add_handler(CommandHandler("time",       cmd_time))
    app.add_handler(CommandHandler("date",       cmd_date))
    app.add_handler(CommandHandler("ping",       cmd_ping))

    # ── Group 0: Content commands ─────────────────────────────────────────────
    app.add_handler(CommandHandler("joke",       cmd_joke))
    app.add_handler(CommandHandler("fact",       cmd_fact))
    app.add_handler(CommandHandler("quote",      cmd_quote))
    app.add_handler(CommandHandler("love",       cmd_love))
    app.add_handler(CommandHandler("riddle",     cmd_riddle))

    # ── Group 0: Moderation commands ──────────────────────────────────────────
    app.add_handler(CommandHandler("warn",       cmd_warn))
    app.add_handler(CommandHandler("mute",       cmd_mute))
    app.add_handler(CommandHandler("unmute",     cmd_unmute))
    app.add_handler(CommandHandler("ban",        cmd_ban))
    app.add_handler(CommandHandler("unban",      cmd_unban))
    app.add_handler(CommandHandler("kick",       cmd_kick))
    app.add_handler(CommandHandler("rules",      cmd_rules))

    # ── Group 0: Game commands ────────────────────────────────────────────────
    app.add_handler(CommandHandler("dice",       cmd_dice))
    app.add_handler(CommandHandler("coin",       cmd_coin))
    app.add_handler(CommandHandler(["8ball", "8top"], cmd_8ball))
    app.add_handler(CommandHandler("guess",      cmd_guess))
    app.add_handler(CommandHandler("math",       cmd_math))
    app.add_handler(CommandHandler("stop",       cmd_stop))

    # ── Group 0: Fun commands ─────────────────────────────────────────────────
    app.add_handler(CommandHandler("ship",       cmd_ship))
    app.add_handler(CommandHandler("compliment", cmd_compliment))
    app.add_handler(CommandHandler("roast",      cmd_roast))
    app.add_handler(CommandHandler("truth",      cmd_truth))
    app.add_handler(CommandHandler("dare",       cmd_dare))

    # ── Group 1: Natural language chat (lowest priority) ──────────────────────
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
        group=1,
    )

    logger.info("Chat Corner Bot (Group Edition) is running — waiting for messages…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
