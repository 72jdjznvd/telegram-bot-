"""Azerbaijani text normalization and fuzzy-matching utilities.

normalize_az(text)  — lowercase + map Azerbaijani special chars to plain Latin:
    ə→e  ı→i  ö→o  ü→u  ğ→g  ş→s  ç→c

fuzzy_has(text, *words, threshold=0.8) — True if any word appears in text
    either as an exact substring OR fuzzy-matches any word-token in text
    above the SequenceMatcher ratio threshold.

Both helpers expect text that has already been through normalize_az().
"""

from difflib import SequenceMatcher

# Only lowercase special chars needed: we always lowercase before translating.
_AZ_TABLE = str.maketrans("əıöüğşç", "eiougsc")


def normalize_az(text: str) -> str:
    """Lowercase and replace Azerbaijani-specific characters with Latin equivalents."""
    return text.lower().translate(_AZ_TABLE)


def _nl(words: list[str]) -> list[str]:
    """Normalize a keyword list with normalize_az and remove duplicates."""
    seen: set[str] = set()
    result: list[str] = []
    for w in words:
        n = normalize_az(w)
        if n not in seen:
            seen.add(n)
            result.append(n)
    return result


def fuzzy_has(text: str, *words: str, threshold: float = 0.8) -> bool:
    """True if any word in *words is found in text.

    Matching strategy (in order):
    1. Exact substring — handles multi-word phrases and is fast.
    2. Token-level fuzzy — for single-word keywords, check every whitespace
       token in text with SequenceMatcher; accept if ratio >= threshold.
       Short tokens (< 3 chars) are skipped to avoid spurious matches.

    Both text and words must already be az-normalized.
    """
    tokens = text.split()
    for word in words:
        word = word.strip()
        if not word:
            continue
        # Fast exact path (also covers multi-word phrases)
        if word in text:
            return True
        # Fuzzy path — single-word keywords only
        if " " not in word:
            for token in tokens:
                if len(token) >= 3 and SequenceMatcher(None, word, token).ratio() >= threshold:
                    return True
    return False
