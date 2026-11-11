"""Prove MAJOR PERCIVAL FFOULKES IS INNOCENT through its nested statement."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT = {e['id']: e for e in O.entities()}; RM = RMOD.rooms()
g = booted(); mem = g.m.memory
r = mem[ENT[2]['address'] + 15]; a = RM[r]['address']
mem[0x8CC9] = r; mem[0xA00A] = r; mem[0xDCFF] = a & 255; mem[0xDD00] = a >> 8; mem[0xDD01] = r; mem[0x8CBA + 1] = 0xFF
import sys as _s
if '--caught' in _s.argv:      # as if the Major had confessed at the opium den ($F103)
    mem[0x9972] |= 0x02
for c in ('SAY TO LESTRADE "MAJOR FFOULKES IS INNOCENT"',
          'SAY TO LESTRADE "MAJOR FFOULKES VISITED THE OPIUM DEN"',
          'SAY TO LESTRADE "MAJOR FFOULKES IS INNOCENT"',
          'SAY TO LESTRADE "MAJOR FFOULKES IS INNOCENT"'):
    out = run_with_bps(g, ' ' + c, [], None, max_slices=4000)   # a leading space survives a swallowed key
    t = text(out); i = t.find('You talk to') if 'You talk to' in t else t.rfind('>')
    print(f'{c!r}\n   $9968={mem[0x9968]:02X} $996E={mem[0x996E]:02X} $9E88={mem[0x9E88]:02X} | {t[-230:]}')
