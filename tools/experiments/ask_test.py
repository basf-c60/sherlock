import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT={e['id']:e for e in O.entities()}; RM=RMOD.rooms()
g=booted(); mem=g.m.memory
r=mem[ENT[2]['address']+15]; a=RM[r]['address']
mem[0x8CC9]=r; mem[0xA00A]=r; mem[0xDCFF]=a&255; mem[0xDD00]=a>>8; mem[0xDD01]=r; mem[0x8CBA+1]=0xFF
log=[]
def hit(g,pc):
    log.append((hex(pc), mem[0xA036], ' '.join('%02X'%mem[g.m.ix+k] for k in range(5)) if pc==0xCDBF else ''))
    if pc==0xCE10: log.append(('printed so far', text(g.output())[-60:]))
for c in ['WAIT']:
    out=run_with_bps(g,c,[0xCDBF,0xCE10],hit,max_slices=5000)
    print(text(out)[-400:])
for x in log: print(x)
