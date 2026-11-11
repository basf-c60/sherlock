import sys, collections; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O
ENT={e['id']:e for e in O.entities()}
g=booted(); mem=g.m.memory
def root(i):
    seen=0
    while i in ENT and mem[ENT[i]['address']+1]!=0xFF and seen<10:
        i=mem[ENT[i]['address']+1]; seen+=1
    return ('thing',i) if i in ENT and mem[ENT[i]['address']+1]!=0xFF else (i, mem[ENT[i]['address']+15] if i in ENT else None)
res=collections.Counter(); st={}
def hit(g,pc):
    if pc==0xE604:
        a,d=mem[0xA036],mem[0xA034]
        st['exp']=(d in ENT and a in ENT and root(a)==root(d), d==a); st['on']=True
    elif pc==0xE5F0 and st.get('on'):
        res[('same root',st['exp'][0],'Z',bool(g.m.f&0x40))]+=1; st['on']=False
for n in range(84):
    run_with_bps(g,'WAIT',[0xE604,0xE5F0],hit,max_slices=6000)
print(dict(res))
