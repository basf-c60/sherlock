"""Is the $9993 marker the only thing standing between the player and
MRS JONES KILLED TRICIA FENDER? Marks the rest of the evidence (body,
bookcase, clothes examined; marker $998F), with and without $9993, and
tells Lestrade."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT = {e['id']: e for e in O.entities()}; RM = RMOD.rooms()
for with_9993 in (False, True):
    g = booted(); m = g.m.memory
    r = m[ENT[2]['address'] + 15]; a = RM[r]['address']
    m[0x8CC9] = r; m[0xA00A] = r; m[0xDCFF] = a & 255; m[0xDD00] = a >> 8; m[0xDD01] = r; m[0x8CBA + 1] = 0xFF
    for t in (72, 66, 67):
        m[ENT[t]['address'] + 6] |= 0xC0
    m[0x9992] |= 2
    if with_9993:
        m[0x9996] |= 2
    out = run_with_bps(g, ' SAY TO LESTRADE "MRS JONES KILLED TRICIA FENDER"', [], None, max_slices=4000)
    print('with $9993' if with_9993 else 'without $9993', '| $9984 = %02X |' % m[0x9984], text(out)[-260:])
