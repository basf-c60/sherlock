import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT={e['id']:e for e in O.entities()}; RM=RMOD.rooms()
for who in ('WATSON','LESTRADE'):
    g=booted(); mem=g.m.memory
    if who=='LESTRADE':
        r=mem[ENT[2]['address']+15]; a=RM[r]['address']
        mem[0x8CC9]=r; mem[0xA00A]=r; mem[0xDCFF]=a&255; mem[0xDD00]=a>>8; mem[0xDD01]=r; mem[0x8CBA+1]=0xFF
        run_with_bps(g,'LOOK',[],None,max_slices=4000)
    for st in ('TRICIA FENDER KILLED MRS JONES','PHIPPS KILLED MRS BROWN','MRS JONES KILLED TRICIA FENDER'):
        out=run_with_bps(g,f'SAY TO {who} "{st}"',[],None,max_slices=5000)
        t=text(out); i=t.rfind('You talk to')
        print(who, repr(st), '| $99C8', '%02X'%mem[0x99C8], '$99D2','%02X'%mem[0x99D2], '$9984','%02X'%mem[0x9984], '|', t[i:i+170])
