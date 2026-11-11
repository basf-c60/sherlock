"""Is it dark outside at night? Walks to Baker Street (with or without the
oil lamp), pokes the clock to 9pm, and LOOKs."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
for lamp in (False, True):
    g = booted(); mem = g.m.memory
    cmds = (['TAKE LAMP'] if lamp else []) + ['OPEN YOUR DOOR', 'W', 'D', 'OPEN FRONT DOOR', 'S']
    for c in cmds:
        out = run_with_bps(g, c, [], None, max_slices=3000)
    print('   last move:', text(out)[-90:])
    mem[0x9FE0] = 9; mem[0x9FE2] = ord('p')
    out = run_with_bps(g, 'LOOK', [], None, max_slices=3000)
    print('lamp' if lamp else 'no lamp', '| LOOK at 9pm |', text(out)[-160:])
