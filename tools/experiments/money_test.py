"""How typed numbers, times and pre-decimal money are read ($DAC6-$DC12)."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
g = booted(); mem = g.m.memory
for c in ('PAY `1 TO WATSON', 'PAY 2/6 TO WATSON', 'PAY 3S TO WATSON', 'PAY 1/- TO WATSON', 'WAIT UNTIL 9:30AM', 'INVENTORY'):
    seen = []
    def hit(g, pc):
        seen.append(f'{g.m.b:02X}{g.m.c:02X}')
    out = run_with_bps(g, c, [0xDB60], hit, max_slices=4000)
    print(repr(c), 'parsed BC =', seen, '|', text(out)[-140:].replace('\n', ' '))
