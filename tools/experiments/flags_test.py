import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O
ENT={e['id']:e for e in O.entities()}
g=booted(); mem=g.m.memory
d=ENT[21]['address']
for c in ['OPEN YOUR DOOR','OPEN YOUR DOOR','CLOSE YOUR DOOR','CLOSE YOUR DOOR','LOCK YOUR DOOR','UNLOCK YOUR DOOR']:
    hits=[]
    out=run_with_bps(g,c,[0xCB7B],lambda g,pc: hits.append(mem[0xCB79]),max_slices=4000)
    print(f'{c!r}: {text(out)[-90:]!r}  door +5=${mem[d+5]:02X}  $CB79={["%02X"%h for h in hits]}')
