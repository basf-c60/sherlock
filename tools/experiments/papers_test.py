"""Which ending comes next if the 3pm and Major endings are out of the way?
Pokes $9D90 (introduced), $9E88 (Major cleared) and, with --murders, both
murder statements proven; then WAITs until the game ends."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
g = booted(); m = g.m.memory
m[0x9D90] = 1; m[0x9E88] = 1
if '--murders' in sys.argv:
    m[0x9976] |= 2; m[0x9984] |= 2
for n in range(900):
    hit = []
    out = run_with_bps(g, 'WAIT', [0x9E4A, 0x9E6C, 0x9E87, 0x9EA4, 0xDFCC], lambda g, pc: hit.append(hex(pc)), max_slices=6000)
    t = text(out)
    if [h for h in hit if h not in ('0x9e6c', '0x9e87')]:
        print('record body reached:', hit, 'at day', m[0x9FE1], m[0x9FE0], chr(m[0x9FE2]))
    if 'PLAY SAVED' in t:
        print('ENDED day', m[0x9FE1], m[0x9FE0], chr(m[0x9FE2]), ':', t[-700:]); break
else:
    print('no ending by day', m[0x9FE1], m[0x9FE0], chr(m[0x9FE2]))
