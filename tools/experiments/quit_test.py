"""What do QUIT, LOAD and PAUSE do?"""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
for c in ('QUIT', 'LOAD', 'PAUSE', 'NOPRINT'):
    g = booted()
    out = run_with_bps(g, c, [], None, max_slices=3000)
    print(repr(c), '| $A0DA =', g.m.memory[0xA0DA], '|', text(out)[-160:])
