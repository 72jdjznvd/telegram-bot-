"""Welcome new members and say goodbye to departing ones."""

import random
import logging
import html

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

WELCOME_MESSAGES = [
    "Xoş gəldin, <b>{name}</b>! Qrupa qoşulduğun üçün şadıq. Özünü evdə hiss et! 🎉",
    "<b>{name}</b>, xoş gördük! Söhbət sənin gəlişinlə daha da canlılaşdı.",
    "Salam, <b>{name}</b>! Qrupumuza qoşulduğun üçün sağ ol. Maraqlı söhbətlər gözləyir! 😊",
    "<b>{name}</b> aramıza qatıldı! Xoş gəlmişsən, bu qrup artıq sənin ailəndir.",
    "Hey, <b>{name}</b>! Nə gözəl ki gəldin. Burada hamı dostdur, rahat ol! 🤝",
    "<b>{name}</b> qrupa girdi! Bizimlə olmağın xoşdur. Xoş gəlmişsən!",
    "Salam, <b>{name}</b>! Qrupumuza xoş gəlmişsən. Şübhəsiz ki, burada yaxşı vaxt keçirəcəksən.",
    "<b>{name}</b> ailəmizə qoşuldu! Maraqlı söhbətlər üçün gözləyirik. 😄",
    "Xoş gəldin, <b>{name}</b>! Soru sual ver, söhbət et — burada hamı açıqdır.",
    "<b>{name}</b>, gəlişin xeyirli olsun! Bu qrup artıq sənin evindir.",
]

GOODBYE_MESSAGES = [
    "<b>{name}</b> qrupu tərk etdi. Yaxşı yollar, uğurlar!",
    "<b>{name}</b> bizdən ayrıldı. Gözəl günlər olsun!",
    "<b>{name}</b> getdi. İstəsə hər zaman qayıda bilər.",
    "<b>{name}</b> xudahafizləşdi. Sağlıqla qal!",
    "<b>{name}</b> çıxdı. Yolun açıq olsun!",
    "<b>{name}</b> ayrıldı. Tezliklə görüşərik ümid edirəm.",
]


async def welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fire when new members join the group."""
    msg = update.message
    if not msg or not msg.new_chat_members:
        return

    for member in msg.new_chat_members:
        if member.is_bot:
            continue
        # Safely escape the name for HTML
        name = html.escape(member.full_name or member.username or "Yeni üzv")
        text = random.choice(WELCOME_MESSAGES).format(name=name)
        try:
            await context.bot.send_message(
                chat_id=msg.chat_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning("Welcome message failed: %s", e)


async def goodbye_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fire when a member leaves the group."""
    msg = update.message
    if not msg or not msg.left_chat_member:
        return

    member = msg.left_chat_member
    if member.is_bot:
        return

    name = html.escape(member.full_name or member.username or "Üzv")
    text = random.choice(GOODBYE_MESSAGES).format(name=name)
    try:
        await context.bot.send_message(
            chat_id=msg.chat_id,
            text=text,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning("Goodbye message failed: %s", e)
