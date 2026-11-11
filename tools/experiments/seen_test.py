import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O
ENT={e['id']:e for e in O.entities()}
g=booted(); mem=g.m.memory
def f6(i): return mem[ENT[i]['address']+6]
ids=[22,23,24,3,25,26,21,50]
print('start', {i:f'{f6(i):02X}' for i in ids})
for c in ['LOOK','EXAMINE LAMP','EXAMINE CLOSELY LAMP','EXAMINE WATSON','TAKE LAMP']:
    run_with_bps(g,c,[],None,max_slices=4000)
    print(f'{c:22}', {i:f'{f6(i):02X}' for i in ids})
print({i:O.display_name(ENT[i]) for i in ids})
