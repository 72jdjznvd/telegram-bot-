"""
Intent detection layer — runs between shortcuts and keyword pattern matching.

An intent is detected from the *structure* of the message (what the user is
trying to do), not from an exact keyword hit.  Each detector returns a reply
string or None.  The master `detect_intent()` runs them in priority order.

All keyword lists are normalized at import time via az_normalize._nl() so that
incoming text (already az-normalized) matches regardless of whether the user
typed Azerbaijani special chars or their plain Latin equivalents.
fuzzy_has() extends matching to catch ~0.8-ratio near-matches.
"""

import re
import random

from az_normalize import _nl, fuzzy_has, normalize_az


# ── helpers ───────────────────────────────────────────────────────────────────

def _has(text: str, *words) -> bool:
    """Fuzzy-aware presence check.  Delegates to fuzzy_has for 0.8 threshold."""
    return fuzzy_has(text, *words)


# ── Tech: something is not working ────────────────────────────────────────────

_BROKEN_VERBS = _nl([
    "işləmir", "islemir",
    "açılmır", "acilmir",
    "bağlanmır", "baglanmir",
    "qoşulmur", "qosulmur",
    "gəlmir", "gelmir",
    "görünmür", "gorunmur",
    "çalışmır", "calismir",
    "kesildi", "kəsildi",
    "dondu", "donub",
    "yavaşladı", "yavasladi", "yavaşlayıb",
    "düşdü", "duşdu",
    "problem var",
    "xarab oldu", "xarab olub",
    "olmur",
    "sıradan çıxdı", "siradan cixdi",
    "işə salmır", "işə düşmür",
    "açmır", "acmir",
    "girilmir", "giremirəm", "giremirem",
    "yüklenmir", "yüklənmir",
])

_WIFI_WORDS   = _nl(["wifi", "wi-fi", "internet", "şəbəkə", "sebeke",
                      "bağlantı", "baglanti", "modem", "router", "net"])
_TIKTOK_WORDS = _nl(["tiktok", "tik tok"])
_INSTA_WORDS  = _nl(["instagram", "instaqram", "insta", "ig"])
_WA_WORDS     = _nl(["whatsapp", "wp ", "vatsap", "watsap", "whats app"])
_YT_WORDS     = _nl(["youtube", "yutub", "yt "])
_TG_WORDS     = _nl(["telegram"])
_FB_WORDS     = _nl(["facebook", "fb "])
_PHONE_WORDS  = _nl(["telefon", "mobil", "android", "iphone", "samsung",
                      "huawei", "xiaomi", "redmi", "realme"])
_PC_WORDS     = _nl(["kompüter", "komputer", "laptop", "noutbuk",
                      "pc ", "windows", "mac ", "macbook"])
_APP_WORDS    = _nl(["tətbiq", "tetbiq", "proqram", "program", "app",
                      "səhifə", "sehife", "sayt", "site", "platforma"])

_WIFI_FIX = [
    "Modemi söndür, 30 saniyə gözlə, yenidən aç — bu əksər vaxt kömək edir.\n\n"
    "Olmadısa:\n"
    "• Telefonu WiFi-dən ayırıb yenidən qoş\n"
    "• Operator xəttini yoxla — ödəniş məsələsi ola bilər\n"
    "• VPN istifadə edirsənsə, söndür",

    "WiFi bağlantısı üçün:\n"
    "1. Routeri yenidən başlat\n"
    "2. Cihazı şəbəkədən ayır, yenidən qoş\n"
    "3. Kömək etməsə operatora zəng et",
]

_TIKTOK_FIX = [
    "İnternet bağlantını yoxla. Problem davam edərsə tətbiqi yenilə və ya yenidən başlad.",
    "TikTok açılmırsa:\n"
    "• İnternetin olub-olmadığını yoxla\n"
    "• Tətbiqi bağlayıb yenidən aç\n"
    "• Cihazı yenidən başlat\n"
    "• Tətbiqi yenilə ya sil-yenidən quraşdır",
]

_INSTA_FIX = [
    "Instagram açılmırsa: internet bağlantını yoxla, tətbiqi yenidən başlat.\n"
    "Kömək etməsə — silib yenidən quraşdır.\n"
    "Hamıda problem varsa Instagram serverləri çökəndədir — bir az gözlə.",
    "İnstagram problemi:\n"
    "• İnternet bağlı mı? Yoxla\n"
    "• Tətbiqi bağlayıb yenidən aç\n"
    "• Kömək etməsə silib yenidən yüklə",
]

_WA_FIX = [
    "WhatsApp işləmirdə: internet bağlantını yoxla, tətbiqi yenidən başlat.\n"
    "Bildirimlər gəlmirirsə — tətbiq icazələrini yoxla (Ayarlar → WhatsApp).",
    "WhatsApp problemi üçün:\n"
    "• İnternet bağlantını yoxla\n"
    "• Tətbiqi yenidən başlat\n"
    "• Yeniləmə var-yox yoxla",
]

_YT_FIX = [
    "YouTube açılmırsa: internet sürətini yoxla, tətbiqi yenidən başlat.\n"
    "Hələ də olmursa — Ayarlar → Tətbiqlər → YouTube → Keşi sil.",
    "YouTube problemi:\n"
    "• İnternet bağlantısı yoxla\n"
    "• Tətbiqi bağlayıb yenidən aç\n"
    "• Keş temizle: Ayarlar → YouTube → Keşi sil",
]

_TG_FIX = [
    "Telegram problemi: internet bağlantını yoxla.\n"
    "Proxy ya VPN istifadə edirsənsə, söndür. Tətbiqi yenidən başlat.",
]

_FB_FIX = [
    "Facebook açılmırsa: internet bağlantını yoxla, tətbiqi yenidən başlat. "
    "Olmadısa — silib yenidən yüklə.",
]

_PHONE_FIX = [
    "Telefon problemlərinin çoxu yenidən başlatmaqla həll olur.\n\n"
    "Olmadısa:\n"
    "• Yaddaşı yoxla — dolubsa lazımsız faylları sil\n"
    "• Son yüklənmiş tətbiqləri sil\n"
    "• Uzun sürərsə — servis mərkəzinə apar",
    "Telefonun donub ya yavaşlayıbsa:\n"
    "1. Yenidən başlat\n"
    "2. Lazımsız tətbiqləri bağla\n"
    "3. Yaddaşı boşalt\n"
    "Uzun müddətlirsə zavod sıfırlaması düşünülə bilər",
]

_PC_FIX = [
    "Kompüter problemlərinin 80%-i yenidən başlatmaqla həll olur. Cəhd et.\n"
    "Olmadısa — hansı xəta görünür? Daha ətraflı anlat, kömək edim.",
    "Kompüter / laptop problemi:\n"
    "1. Yenidən başlat\n"
    "2. Yeniləmə gözləyirsə — tamamla\n"
    "3. Antivirusla yoxla\n"
    "4. Olmadısa — xəta mesajını mənə yaz",
]

_APP_FIX = [
    "Tətbiq işləmirdə:\n"
    "1. Bağlayıb yenidən aç\n"
    "2. Cihazı yenidən başlat\n"
    "3. Tətbiqi yenilə\n"
    "4. Sil — yenidən quraşdır",
    "İnternet bağlantını yoxla. Problem davam edərsə tətbiqi yenilə və ya yenidən başlad.",
]


def detect_tech_problem(norm: str) -> str | None:
    """Detects '[thing] not working' and returns specific troubleshooting advice."""
    if not _has(norm, *_BROKEN_VERBS):
        return None
    if _has(norm, *_WIFI_WORDS):   return random.choice(_WIFI_FIX)
    if _has(norm, *_TIKTOK_WORDS): return random.choice(_TIKTOK_FIX)
    if _has(norm, *_INSTA_WORDS):  return random.choice(_INSTA_FIX)
    if _has(norm, *_WA_WORDS):     return random.choice(_WA_FIX)
    if _has(norm, *_YT_WORDS):     return random.choice(_YT_FIX)
    if _has(norm, *_TG_WORDS):     return random.choice(_TG_FIX)
    if _has(norm, *_FB_WORDS):     return random.choice(_FB_FIX)
    if _has(norm, *_PHONE_WORDS):  return random.choice(_PHONE_FIX)
    if _has(norm, *_PC_WORDS):     return random.choice(_PC_FIX)
    if _has(norm, *_APP_WORDS):    return random.choice(_APP_FIX)
    return None


# ── Health: body part + pain verb ─────────────────────────────────────────────

_PAIN_VERBS = _nl([
    "ağrıyır", "agriyir",
    "sancıyır", "sanciiyir",
    "tutub",
    "yanır", "yanir",
    "şişib", "sismib",
    "göynəyir", "goyuneyir",
    "acıyır", "aciiyr",
    "narahat edir",
    "problem var",
])

# Maps list-of-normalized-keywords → reply list
_BODY_MAP = [
    (
        _nl(["qulaq"]),
        ["Keçmiş olsun. Qulaq ağrısı infeksiyadan ola bilər — özünü evdə müalicə etmə, həkimə müraciət et."],
    ),
    (
        _nl(["diş", "dis ", "dişəti"]),
        ["Keçmiş olsun! Diş ağrısı çox şiddətli olur. Ağrıkəsici geçici rahatlıq verir, amma əsl həll yalnız stomatoloqdadır — gecikdirmə."],
    ),
    (
        _nl(["boğaz", "bogaz"]),
        ["Keçmiş olsun! Boğaz ağrısında: isti çay, bal-limon, duz suyuyla garqara. Hərarət varsa həkimə müraciət et."],
    ),
    (
        _nl(["göz", "goz"]),
        ["Keçmiş olsun. Göz ağrısında ekrandan uzaqlaş, gözlərini dincəlt. Qızarma ya iltihab varsa həkimə bax."],
    ),
    (
        _nl(["bel", "arxa", "omurga", "boyun"]),
        ["Keçmiş olsun. Bel ağrısında: düz dur, uzun oturma, isti duz kisəsi qoy. Ağır yük qaldırma. Uzun sürərsə ortoped həkiminə bax."],
    ),
    (
        _nl(["diz", "ayaq", "daban", "baldır"]),
        ["Keçmiş olsun. Ayaq ağrısında istirahət et, yüksəltilmiş mövqedə saxla. Şişsə buz qoy. Uzun sürərsə həkimə bax."],
    ),
    (
        _nl(["çiyin", "bilərzik", "barmaq", " əl "]),
        ["Keçmiş olsun. Yükü azalt, istirahət et. Şişib yanırsa ortopeda müraciət et."],
    ),
    (
        _nl(["qarın", "qarn", "mədə", "mede", "mide"]),
        [
            "Keçmiş olsun. İsti su iç, yüngül ye — düyü, qaynadılmış kartof. Ağrı davam edərsə həkimə bax.",
            "Başın sağ olsun. Qarn ağrısında bir müddət ağır yeməyi kəs, isti çay iç. Yaxşılaşmırsa həkimə get.",
        ],
    ),
    (
        _nl(["baş", "bas "]),
        [
            "Keçmiş olsun. Baş ağrısında: su iç, ekrandan uzaqlaş, alnına soyuq dəsmal qoy. Şiddətlənərsə həkimə bax.",
            "Başın sağ olsun! Pəncərəni aç, bir az təmiz hava al. Susuzluqdan da ola bilər — bol su iç.",
        ],
    ),
]


def detect_health_symptom(norm: str) -> str | None:
    """Detects body-part + pain-verb combos more flexibly than exact keyword matching."""
    if not _has(norm, *_PAIN_VERBS):
        return None
    for body_parts, replies in _BODY_MAP:
        if _has(norm, *body_parts):
            return random.choice(replies)
    return None


# ── Emotional distress ────────────────────────────────────────────────────────

_DISTRESS_WORDS = _nl([
    "ağladım", "agladim", "ağlıyıram", "agliiyiram",
    "sıxılmışam", "sıxılıram",
    "çox yoruldum", "cox yoruldum",
    "dözə bilmirəm", "doze bilmirem",
    "bezmişəm", "bezmisem",
    "kədərliyəm", "kederim var",
    "üzgünəm", "uzgunem",
    "içim yanır", "içim sıxılır",
    "qəlbim ağrıyır",
    "ağlar", "ağlayıram",
    "hüngür", "hungur",
    "dərdim var", "derdim var",
    "çox pis",
])

_DISTRESS_REPLIES = [
    "Sənin bu hissini başa düşürəm. Bəzən hər şey üst-üstə gəlir. Bir nəfəs al. Danışmaq istəyirsənsə, burdayam.",
    "Bu anlarda yalnız olmaq lazım deyil. Yaxın birinə zəng et, söhbət et. Danışmaq çox rahatladır.",
    "Çətin anlardır bunlar. Amma hər ağır an keçər. Özünə qulluq et — su iç, nəfəs al, bir az yat.",
    "Sənin hisslərinin dəyəri var. Özünü günahlandırma. İndi vacib olan addım-addım gəlməkdir.",
]


def detect_emotional_distress(norm: str) -> str | None:
    if _has(norm, *_DISTRESS_WORDS):
        return random.choice(_DISTRESS_REPLIES)
    return None


# ── Asking for how-to instructions ────────────────────────────────────────────

_HOW_TO_MAP = [
    # wifi setup
    (_nl(["wifi", "wi-fi", "internet", "şəbəkə"]),
     _nl(["qoşmaq", "bağlamaq", "qoşul", "ayarla", "girmək"]),
     ["WiFi qoşmaq üçün: Ayarlar → WiFi → Şəbəkəni seç → Şifrəni daxil et. Görünmürsə, modemi yenidən başlat."]),

    # install app
    (_nl(["tətbiq", "proqram", "app"]),
     _nl(["yüklə", "qur", "indir", "quraşdır"]),
     ["Tətbiq yükləmək üçün Play Store (Android) ya App Store (iPhone) aç, adını yaz, 'Yüklə' düyməsinə bas."]),

    # change password
    (_nl(["şifrə", "parol", "sifre"]),
     _nl(["dəyiş", "sifirl", "unutd", "yenilə", "yaratmaq"]),
     ["Şifrəni dəyişmək: Ayarlar → Hesab → Şifrəni dəyiş bölümünə keç. 'Unutmuşam' seçsən, emailinə kod gələr."]),

    # send money / transfer
    (_nl(["pul", "köçür", "transfer"]),
     _nl(["göndər", "köçür", "necə"]),
     ["Pul köçürmə üçün: bank tətbiqini aç → Köçürmə → Kartı ya hesab nömrəsini daxil et → Məbləği yaz → Təsdiqlə."]),
]


def detect_how_to(norm: str) -> str | None:
    for subjects, actions, replies in _HOW_TO_MAP:
        if _has(norm, *subjects) and _has(norm, *actions):
            return random.choice(replies)
    return None


# ── Follow-up "how are you" directed at bot ───────────────────────────────────

_FOLLOWUP_TRIGGERS = _nl([
    "yaxşı sən", "yaxsi sen",
    "bəs sən", "bes sen",
    "ya sən", "ya sen",
    "sən yaxşısan", "sen yaxsisan",
    "sən necəsən", "sen necesen",
    "sən nə haldasın", "sen ne haldasin",
])

_FOLLOWUP_REPLIES = [
    "Mən də yaxşıyam, təşəkkür edirəm!",
    "Yaxşıyam, sağ ol! Nə gəzir?",
    "Çox şükür, yaxşıyam. Sən necəsən daha?",
    "Mən həmişə qaydasındayam — robot olduğum üçün! Sən yaxşısan?",
    "Yaxşıyam, sağ ol. Başqa nə var?",
]


def detect_followup(norm: str) -> str | None:
    if _has(norm, *_FOLLOWUP_TRIGGERS):
        return random.choice(_FOLLOWUP_REPLIES)
    return None


# ── Asking for recommendations ────────────────────────────────────────────────

_REC_SUBJECTS = {
    normalize_az("film"):     ["Tavsiyə: Forrest Gump, The Shawshank Redemption, Intouchables — klassik hiss drамları. Nə janr sevinirsən?"],
    normalize_az("serial"):   ["Tavsiyə: Breaking Bad, Money Heist, Squid Game — gec yatmağa hazır ol! Nə janr?"],
    normalize_az("kitab"):    ["Azerbaycanca tövsiyə: Mir Cəlal, İlyas Əfəndiyev. Dünya ədəbiyyatından: 1984, Küçük Prens, Alximik."],
    normalize_az("restoran"): ["Bakıda yer axtarırsan? Ərazin hansıdır? Yaxud mətbəx növü — Avropa, Azərbaycan, Asiya?"],
    normalize_az("mahnı"):    ["Əhvalına görə dəyişir. Kədərli üçün yavaş melodiyalar, şən üçün ritmik. Hansı əhvaldasan?"],
    normalize_az("podkast"):  ["Azərbaycanca podkastlardan: müxtəlif mövzularda var. İngilizcə isə — TED Talks, Lex Fridman əladır."],
}

_REC_VERBS = _nl([
    "tövsiyə et", "tavsiye et", "önerisi", "nə baxım", "nə oxuyum",
    "nə dinləyim", "nə izliyim", "nə yeyim", "haraya gedim",
    "məsləhət ver", "meslehet ver",
])


def detect_recommendation(norm: str) -> str | None:
    if not _has(norm, *_REC_VERBS):
        return None
    for keyword, replies in _REC_SUBJECTS.items():
        if keyword in norm:
            return random.choice(replies)
    return None


# ── Complaint / venting ───────────────────────────────────────────────────────

# Patterns are pre-normalized so they match az-normalized input.
_COMPLAINT_PATTERNS = [
    normalize_az(r"(məni|meni).{0,30}(qəzəbləndir|hirsləndir|bezdir|əsəbləşdir|sinir)"),
    normalize_az(r"(bezib|bezmişəm|bezmisem)"),
    normalize_az(r"nə qədər (pis|eyibli|zəif|utanc|ayıb)"),
]

_COMPLAINT_REPLIES = [
    "Anladım, bu cür durumlar çox sinir pozucu olur. Nə baş verdi?",
    "Haqlısan, bu kimi şeylər insan əsəbini pozur. Açıq danış, dinliyirəm.",
    "Beləsi çox çətin olur. Nə etmək lazımdır sənin fikrincə?",
]


def detect_complaint(norm: str) -> str | None:
    for p in _COMPLAINT_PATTERNS:
        if re.search(p, norm):
            return random.choice(_COMPLAINT_REPLIES)
    return None


# ── Gratitude directed at bot ─────────────────────────────────────────────────

_THANKS_WORDS = _nl([
    "sağ ol", "sag ol", "çox sağ ol", "təşəkkür edirəm", "tesekküür", "tesekkur",
    "əla etdin", "kömək etdin", "sağ olun", "məmnunam",
])

_THANKS_REPLIES = [
    "Nə lazım olsa, burdayam!",
    "Əsas sən sağ ol!",
    "Rica ederəm, hər zaman!",
    "Çox razıyam, sağ ol!",
    "Lazım olsa yenə yaz!",
]


def detect_thanks(norm: str) -> str | None:
    if _has(norm, *_THANKS_WORDS):
        return random.choice(_THANKS_REPLIES)
    return None


# ── Greetings (catches variants the pattern list may miss) ────────────────────

_GREETING_WORDS = _nl([
    "salam", "hey", "helo", "hello", "hi ", "xeyr", "şərəfli axşam",
    "sabahınız", "günortanız", "axşamınız", "gecəniz",
])

_GREETING_REPLIES = [
    "Salam! Nə gəzir?",
    "Salam! Necə gedirsən?",
    "Hey! Nə var, nə gəzir?",
    "Salamlar! Nə edə bilərəm?",
]


def detect_greeting(norm: str) -> str | None:
    # Only match if the full message is very short (likely a pure greeting)
    # or starts with a greeting word to avoid false positives on long messages
    stripped = norm.strip()
    if len(stripped) <= 20 and _has(stripped, *_GREETING_WORDS):
        return random.choice(_GREETING_REPLIES)
    if stripped.startswith(tuple(g for g in _GREETING_WORDS if len(g) > 2)):
        return random.choice(_GREETING_REPLIES)
    return None


# ── Master detector ───────────────────────────────────────────────────────────

def detect_intent(norm: str) -> str | None:
    """
    Run all detectors in priority order.
    Returns a reply string, or None if nothing matched.
    The caller falls through to keyword pattern matching when None is returned.
    """
    return (
        detect_followup(norm)
        or detect_thanks(norm)
        or detect_tech_problem(norm)
        or detect_health_symptom(norm)
        or detect_emotional_distress(norm)
        or detect_how_to(norm)
        or detect_recommendation(norm)
        or detect_complaint(norm)
        or detect_greeting(norm)
    )
