"""
Decode Sherlock's dictionary, following the game's own expansion code
($A94D -> $A95B/$A990 for the letters, $A92F for the suffix) exactly.

Layout (read from the code, then checked against words confirmed by
play - see dictionary_notes.md):

  $5D80  26 two-byte offsets, one per letter (index = letter AND $1F),
         each relative to $5DBF, giving the first word starting with
         that letter. The first letter itself is never stored.
  word record at $5DBF + offset:
    byte 0   low nibble: suffix number (0-14) into the 4-byte suffix
             table at $A85C; $F = no suffix. High nibble: flags.
    byte 1   bit 7: two extra bytes follow (see `extra`)
             bits 4-6: number of characters to KEEP from the previous
             word in the same letter bucket (front-coding)
             bits 0-3: number of new letters that follow
    [2 extra bytes if byte 1 bit 7]
    letters  5 bits each, big-endian bit stream, value+$60 = ASCII
             (a=1 ... z=26); padded to a whole byte.
  The suffix table's \\x08 entries mean "delete one character first".

Because of the front-coding, words can only be decoded in order from
the start of their letter bucket - which is why calling the expansion
routine on one record in isolation produced garbage early in this
project.
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 0x5D80
P = open(os.path.join(ROOT, 'p.bin'), 'rb').read()


def byte(a):
    return P[a - BASE]


def word16(a):
    return byte(a) | byte(a + 1) << 8


DICT_INDEX = 0x5D80
DICT_BASE = 0x5DBF
SUFFIX_TABLE = 0xA85C


def suffix(n):
    raw = bytes(byte(SUFFIX_TABLE + 4 * n + i) for i in range(4))
    return raw.split(b'\x00')[0]


def apply_suffix(stem, n):
    if n == 0x0F:
        return stem
    s = suffix(n)
    out = stem
    for ch in s:
        if ch == 0x08:
            out = out[:-1]
        else:
            out += chr(ch)
    return out


def letter_starts():
    """{letter: first record address} for letters that have words."""
    out = {}
    for i in range(1, 27):
        off = word16(DICT_INDEX + 2 * i)
        if off:
            out[chr(0x60 + i)] = DICT_BASE + off
    return out


def decode_record(a, prev_tail):
    """Decode one record at a. prev_tail is the previous word's stored
    characters (excluding the implicit first letter). Returns
    (tail, suffix_no, flags0, flags1, extra, next_address)."""
    b0, b1 = byte(a), byte(a + 1)
    p = a + 2
    extra = None
    if b1 & 0x80:
        extra = word16(p)
        p += 2
    keep = (b1 & 0x70) >> 4
    n = b1 & 0x0F
    bits = ''.join(f'{byte(p + i):08b}' for i in range((n * 5 + 7) // 8))
    new = ''.join(chr(0x60 + int(bits[5 * i:5 * i + 5], 2)) for i in range(n))
    p += (n * 5 + 7) // 8
    tail = prev_tail[:keep] + new
    return tail, b0 & 0x0F, b0, b1, extra, p


def bucket_end(i):
    """End of letter bucket i, found the way the game does it ($DA48):
    the next NON-ZERO index entry. Entry 31 is an end-of-dictionary
    marker ($67B7), so the last bucket ('z') ends there too."""
    for j in range(i + 1, 32):
        off = word16(DICT_INDEX + 2 * j)
        if off:
            return DICT_BASE + off
    raise ValueError('no end marker')


def all_words():
    """List of dicts: address, offset, word (stem+suffix, upper case),
    stem, flags, extra. Walks each letter bucket up to its end."""
    words = []
    for i in range(1, 27):
        off = word16(DICT_INDEX + 2 * i)
        if not off:
            continue
        letter = chr(0x60 + i)
        a, end = DICT_BASE + off, bucket_end(i)
        tail = ''
        while a < end:
            tail, sfx, b0, b1, extra, nxt = decode_record(a, tail)
            if nxt > end:          # a trailing pad byte, not a record
                break
            stem = letter + tail
            words.append(dict(address=a, offset=a - DICT_BASE,
                              stem=stem.upper(),
                              word=apply_suffix(stem, sfx).upper(),
                              suffix=sfx, flags0=b0, flags1=b1, extra=extra))
            a = nxt
    return words


DICT_END = 0x67B7


def by_offset():
    return {w['offset']: w for w in all_words()}


if __name__ == '__main__':
    ws = all_words()
    for w in ws:
        ex = f" extra={w['extra']:#06x}" if w['extra'] is not None else ''
        print(f"{w['address']:#06x} off={w['offset']:#05x} "
              f"b0={w['flags0']:02x} {w['word']:14s} (stem {w['stem']}){ex}")
    print(len(ws), 'words')
