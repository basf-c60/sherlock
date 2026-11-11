"""Dump the token list the game builds from a typed line ($5B81)."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import dictionary as D
ws = {w['offset']: w['word'] for w in D.all_words()}
g = booted(); mem = g.m.memory
snap = {}
def hit(g, pc):
    if 'm' not in snap:
        snap['m'] = bytes(mem[0x5B81:0x5BE1])
run_with_bps(g, 'TAKE THE LAMP, EXAMINE IT. PAY 2/6 TO WATSON', [0xD769 + 4], hit, max_slices=4000)
b = snap.get('m') or bytes(mem[0x5B81:0x5BE1])
i = 0
while i < len(b):
    c = b[i]
    if c in (0xE0, 0xF0, 0x90) or c < 0x80:
        wv = b[i + 1] << 8 | b[i + 2]
        print(f'${c:02X} {wv:04X} {ws.get(wv & 0xFFF, "")}'); i += 3
    else:
        print(f'${c:02X}'); i += 1
    if c == 0xC0: break
