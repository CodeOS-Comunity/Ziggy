"""Ziggy AI backend — engine.

Pure Python, zero dependencies. Given a prompt, walk the ordered rule set
in models.py and return the reply (str), or None when there is nothing to
say. "__CLEAR__" is a control reply handled by the renderer.

The word/exact matchers are literal ports of match_word()/match_exact()
from the old in-kernel C engine so behaviour stays identical.
"""

try:
    from . import models
except ImportError:  # running as a plain script (python3 engine.py)
    import models


def _match_word(input_text, word):
    """Port of the C match_word(): case-insensitive word match where the
    word must be followed by a boundary char (end, space, '?', '!', '.',
    ',', ':')."""
    i = 0
    length = len(input_text)
    while i < length:
        a, b = i, 0
        while a < length and b < len(word):
            ac = input_text[a]
            bc = word[b]
            if "A" <= ac <= "Z":
                ac = chr(ord(ac) + 32)
            if "A" <= bc <= "Z":
                bc = chr(ord(bc) + 32)
            if ac != bc:
                break
            a += 1
            b += 1
        if b == len(word):
            nxt = input_text[a] if a < length else "\0"
            return nxt in ("\0", " ", "?", "!", ".", ",", ":")
        i += 1
    return False


def _contains(input_text, word):
    return _match_word(input_text, word)


def _exact(input_text, cmd):
    """Port of the C match_exact(): case-insensitive command prefix match
    ending at a boundary char (end, space, '!', '?')."""
    a, b = 0, 0
    ilen, clen = len(input_text), len(cmd)
    while a < ilen and b < clen:
        ic = input_text[a]
        cc = cmd[b]
        if "A" <= ic <= "Z":
            ic = chr(ord(ic) + 32)
        if "A" <= cc <= "Z":
            cc = chr(ord(cc) + 32)
        if ic != cc:
            return False
        a += 1
        b += 1
    if b != clen:
        return False
    return a >= ilen or input_text[a] in (" ", "!", "?")


def response(prompt):
    """Return the AI reply for `prompt` (str), or None for 'no answer'."""
    text = prompt.strip()
    if not text:
        return None

    for rule in models.RULES:
        kind = rule[0]
        if kind == "exact":
            _, cmd, reply = rule
            if _exact(text, cmd):
                return reply
        elif kind == "and":
            _, words, reply = rule
            if all(_contains(text, w) for w in words):
                return reply
        elif kind == "or":
            _, words, reply = rule
            if any(_contains(text, w) for w in words):
                return reply
        elif kind == "notand":
            _, words, not_words, reply = rule
            if all(_contains(text, w) for w in words) and \
               not any(_contains(text, w) for w in not_words):
                return reply
    return models.DEFAULT_RESPONSE