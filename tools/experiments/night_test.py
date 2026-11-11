"""Run the first day and night (with $9D90 poked so the 3pm ending does not
come) and watch Tricia Fender's and Mrs Jones's records."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O
ENT = {e['id']: e for e in O.entities()}
g = booted(); m = g.m.memory
m[0x9D90] = 1
def rec(i):
    a = ENT[i]['address']; return ' '.join('%02X' % m[a + k] for k in (0, 1, 15, 16, 17))
last = None
for n in range(330):
    out = run_with_bps(g, 'WAIT', [0x9E4A, 0x9E6C, 0x9E87, 0x9EA4, 0xDFCC], lambda g, pc: print('  ending record body reached:', hex(pc), 'A=$9E88 is', m[0x9E88]), max_slices=6000)
    t = text(out)
    st = (rec(13), rec(95))
    if st != last:
        print(f'{m[0x9FE1]} {m[0x9FE0]:2}:{m[0x9FDF]:02}{chr(m[0x9FE2])} tricia [{st[0]}] jones [{st[1]}]')
        last = st
    if 'Perhaps you should' in t or 'PLAY SAVED' in t or 'NOT ONLY' in t:
        print('game over at', m[0x9FE1], m[0x9FE0], chr(m[0x9FE2]), ':', t[-900:]); break
print('end', m[0x9FE1], m[0x9FE0], chr(m[0x9FE2]))
