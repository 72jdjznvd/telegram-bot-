"""Fun commands: /ship, /compliment, /roast, /truth, /dare."""

import random
import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

COMPLIMENTS = [
    "Sən həqiqətən möhtəşəm bir insansan! 🌟",
    "Sənin gülüşün günü işıqlandırır! ☀️",
    "Sən çox ağıllı və bacarıqlısan! 🧠",
    "Sənin varlığın bu qrupu xüsusi edir! ❤️",
    "Sən həmişə başqalarını xoşbəxt edə bilirsən! 😊",
    "Sənin enerjin yoluxucudur — ən yaxşı mənada! ⚡",
    "Sən çox yaradıcı bir insansan! 🎨",
    "Sənin yumoru əladır! 😄",
    "Sən güclü və əzimkarsın! 💪",
    "Sənin qəlbin qızıldandır! 💛",
    "Sən hər zaman düzgün şeyi edirsən! ✨",
    "Sən çox maraqlı bir insansan! 🌺",
    "Sənin sözlərin həmişə düşündürür! 💭",
    "Sən bu dünyanı daha gözəl edirsən! 🌍",
    "Sən həmişə digərləri üçün əlindən gələni edirsən! 🤝",
]

ROASTS = [
    "Sənin üzün o qədər düzdür ki, güzgü sındırır! 😂",
    "Sən o qədər yavaşsan ki, tortun şamlarını üfürmək üçün doğum günün bitir! 🎂",
    "Sənin səsin elə xoşdur ki, quşlar ağacdan düşür! 🐦",
    "Sən o qədər bəxtəvərsən ki, pulsuz bilet alsaydın, at qaçışı ləğv olunardı! 🎟️",
    "Sənin saçın elə düzgündür ki, memarlar sənə qibtə edir! 🏗️",
    "Sən o qədər gec gəlirsən ki, 'tez gəl' deyəndə növbəti həftəni nəzərdə tutursan! ⏰",
    "Sənin hazır cavabların elə tezdir ki, sual bitməzdən əvvəl cavab vermiş olursan — yanlış! 💬",
    "Sən o qədər unudqansansa ki, bu cümləni oxuyandan sonra unudacaqsan! 🧠",
    "Sənin planların elə mükəmməldir ki, heç biri həyata keçmir! 📋",
    "Sən o qədər enerjilənsən ki, yatmaq üçün kofein lazımdır! ☕",
]

TRUTH_QUESTIONS = [
    "Ən çox nəyin üçün peşman olmusan? 🤔",
    "Ən böyük sirrini kim bilir? 🤫",
    "Ömründə ən utanc verici anın hansı idi? 😳",
    "İndiyə kimi söylədiyiniz ən böyük yalan hansı idi? 🤥",
    "Qrupda kimə ən çox qibtə edirsin? 👀",
    "Heç özün haqqında yalan danışmısan? Necə? 🙄",
    "Ən dərin qorxun nədir? 😱",
    "Əgər bir gün görünməz olsaydın, nə edərdin? 🫥",
    "Ömründə ən pis hissiyyat yaşatdığın an hansı idi? 💔",
    "Heç kimə demədiyin bir xüsusiyyətin var mı? 🤐",
    "İndiyə kimi ən böyük iş səhvini et nə idi? 🙈",
    "Çox sevdiyin amma heç vaxt etiraf etmədiyin bir şey varmı? ❤️‍🔥",
    "Heç başqasının telefonuna baxmısan? 📱",
    "Ən sevdiyin insana hansı şeyi heç demə mişsən? 💭",
    "Həyatında ən çox nəyi dəyişmək istərdin? ✨",
]

DARE_CHALLENGES = [
    "Növbəti mesajını tamamilə böyük hərflərlə yaz! ✍️",
    "Sevimli bir mahnının sözlərini yaz! 🎵",
    "Özünü 3 sözlə tanıt! 🗣️",
    "Qrupdakı birinin ən yaxşı xüsusiyyətini yaz! 💛",
    "Bir dəqiqəlik saniyə sayma meydan oxuması et! ⏱️",
    "Özünün ən maraqlı həyat faktını paylaş! 📖",
    "Qrupdakı hər kəsə salam yaz! 👋",
    "Azərbaycan dilində uydurma bir şer yaz! 📝",
    "Sevimli yeməyini emoji ilə ifadə et! 🍽️",
    "Bildiyiniz ən uzun sözü yaz! 📚",
    "Özünü fərqli bir meslek kimi tanıt! 👨‍🚀",
    "Uşaqlıqdan xatırladığın ən gülməli anı paylaş! 😂",
    "Bir zarafat uydur! 🎭",
    "Sabah üçün bir hedef aç! 🎯",
    "Qrupdakı birinə 'əla adam' mesajı göndər! 🏆",
]

HEART_SCALE = ["💔", "❤️‍🩹", "🧡", "💛", "💚", "💙", "💜", "❤️", "❤️‍🔥", "💗", "💝"]


async def cmd_ship(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    # /ship Person1 Person2  OR reply to a message
    args = context.args or []

    if msg.reply_to_message and msg.reply_to_message.from_user:
        name1 = msg.from_user.first_name
        name2 = msg.reply_to_message.from_user.first_name
    elif len(args) >= 2:
        name1 = args[0]
        name2 = " ".join(args[1:])
    elif len(args) == 1:
        name1 = msg.from_user.first_name
        name2 = args[0]
    else:
        await msg.reply_text(
            "💘 İstifadə: `/ship Ad1 Ad2` və ya birinin mesajına cavab ver.",
            parse_mode="Markdown",
        )
        return

    pct = random.randint(0, 100)
    bar_filled = round(pct / 10)
    bar = "❤️" * bar_filled + "🤍" * (10 - bar_filled)
    heart = HEART_SCALE[min(bar_filled, len(HEART_SCALE) - 1)]

    if pct < 20:
        verdict = "Heç uyğun deyillər... 💔"
    elif pct < 40:
        verdict = "Aramızda qalsın, uyğunluq azdır. 😅"
    elif pct < 60:
        verdict = "Orta uyğunluq — bir şans verin! 🙂"
    elif pct < 80:
        verdict = "Yaxşı uyğunluq! Davam edin! 😊"
    else:
        verdict = "Mükəmməl cüt! Evlilik vaxtıdır! 💍"

    await msg.reply_text(
        f"{heart} *Ship nəticəsi:*\n\n"
        f"💑 {name1} × {name2}\n"
        f"💞 Uyğunluq: *{pct}%*\n"
        f"{bar}\n\n"
        f"{verdict}",
        parse_mode="Markdown",
    )


async def cmd_compliment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if msg.reply_to_message and msg.reply_to_message.from_user:
        target = msg.reply_to_message.from_user.first_name
    elif context.args:
        target = " ".join(context.args).lstrip("@")
    else:
        target = msg.from_user.first_name

    compliment = random.choice(COMPLIMENTS)
    await msg.reply_text(
        f"🌹 *{target}* üçün:\n\n{compliment}",
        parse_mode="Markdown",
    )


async def cmd_roast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if msg.reply_to_message and msg.reply_to_message.from_user:
        target = msg.reply_to_message.from_user.first_name
    elif context.args:
        target = " ".join(context.args).lstrip("@")
    else:
        target = msg.from_user.first_name

    roast = random.choice(ROASTS)
    await msg.reply_text(
        f"🔥 *{target}* üçün zarafat:\n\n{roast}\n\n_(Zarafatdır, incimə! 😄)_",
        parse_mode="Markdown",
    )


async def cmd_truth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = random.choice(TRUTH_QUESTIONS)
    name = update.message.from_user.first_name
    await update.message.reply_text(
        f"🫣 *{name}*, sənin sualın:\n\n{question}",
        parse_mode="Markdown",
    )


async def cmd_dare(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    challenge = random.choice(DARE_CHALLENGES)
    name = update.message.from_user.first_name
    await update.message.reply_text(
        f"😈 *{name}*, sənin tapşırığın:\n\n{challenge}",
        parse_mode="Markdown",
    )
