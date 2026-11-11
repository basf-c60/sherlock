import sys, collections; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O
ENT={e['id']:e for e in O.entities()}
g=booted(); mem=g.m.memory
def room(i): return mem[ENT[i]['address']+15] if i in ENT else None
res=collections.Counter(); st={}
def hit(g,pc):
    if pc==0xE5E3: st['exp']=(room(mem[0xA034])==room(mem[0xA035])); st['on']=True
    elif pc==0xE5F0 and st.get('on'):
        z=bool(g.m.f & 0x40); res[('rooms equal',st['exp'],'Z',z)]+=1; st['on']=False
for n in range(84):
    run_with_bps(g,'WAIT',[0xE5E3,0xE5F0],hit,max_slices=6000)
print(dict(res))
