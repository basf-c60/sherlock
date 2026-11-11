"""Ask Mrs Jones and Tricia Fender to tell you about the bloodstained
clothes. A person's own action list (here (TELL ABOUT, shared 22) and
(TELL ABOUT, shared 3)) is used when that person is the one acting ($C933)."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O
ENT = {e['id']: e for e in O.entities()}
for who, name in ((95, 'MRS JONES'), (13, 'TRICIA FENDER')):
    g = booted(); m = g.m.memory
    rec = ENT[who]['address']
    m[rec + 15] = 8; m[rec + 1] = 0xFF
    run_with_bps(g, ' LOOK', [], None, max_slices=3000)
    for c in (f'TELL {name} ABOUT THE BLOODSTAINED CLOTHES',
              f'SAY TO {name} "TELL ME ABOUT THE BLOODSTAINED CLOTHES"', 'WAIT'):
        hits = []
        out = run_with_bps(g, ' ' + c, [0xE18A, 0xE1B4], lambda g, pc: hits.append((hex(pc), m[0xA036], m[0xA035])), max_slices=3000)
        print(name, '|', c, '| shared-action hits (pc, actor, iobj)', hits,
              '| markers $9992 %02X $9996 %02X' % (m[0x9992], m[0x9996]), '|', text(out)[-420:])
