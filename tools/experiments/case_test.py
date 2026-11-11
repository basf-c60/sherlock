import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT={e['id']:e for e in O.entities()}; RM=RMOD.rooms()
def setup(evidence):
    g=booted(); mem=g.m.memory
    r=mem[ENT[2]['address']+15]
    a=RM[r]['address']
    mem[0x8CC9]=r; mem[0xA00A]=r; mem[0xDCFF]=a&255; mem[0xDD00]=a>>8; mem[0xDD01]=r
    mem[0x8CBA+1]=0xFF
    if evidence:
        for t in (46,57): mem[ENT[t]['address']+6] |= 0xC0
        for t in (93,): mem[ENT[t]['address']+6] |= 0x80
    return g, mem, r
for ev in (False, True):
    g,mem,r=setup(ev)
    print('--- evidence' if ev else '--- no evidence', 'Lestrade in room', r, RMOD.room_name(RM[r]))
    for c in ['LOOK','SAY TO LESTRADE "MRS BROWN KILLED HERSELF"','WAIT']:
        out=run_with_bps(g,c,[],None,max_slices=5000)
        print(f'{c!r}: flags $9976={mem[0x9976]:02X} | {text(out)[-300:]}')
