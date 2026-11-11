"""Check internal verbs 128/129/131 and helpers against live state over ~110 WAITs."""
import sys, collections; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O
ENT={e['id']:e for e in O.entities()}
g=booted(); mem=g.m.memory
def room(i): return mem[ENT[i]['address']+15]
res=collections.Counter(); pend={}
BP={0xE5B5:'131 test', 0xE5BE:'131 ok', 0xE5E3:'129 test', 0xE5FA:'129 ok', 0xE4AA:'128 put', 0xE4AD:'128 after',
    0xF19E:'chance', 0xE604:'130 test', 0xF1A5:'chance ok', 0xE7E2+2:'E7E2', 0xCD24:'signal', 0xCD5C:'await match', 0xCDBF:'ask', 0xCF43:'erase'}
log=[]
def hit(g,pc):
    a,d,i=mem[0xA036],mem[0xA034],mem[0xA035]
    tag=BP[pc]
    if tag=='131 test': pend['131']=(a,d,i,room(d) if d in ENT else None)
    elif tag=='131 ok': res[('131 ok', pend['131'][3]==pend['131'][2])]+=1
    elif tag=='129 test': pend['129']=(a,d,i,room(d) if d in ENT else None, room(i) if i in ENT else None); pend['last']='129'
    elif tag=='129 ok':
        if pend.get('last')=='129': p=pend['129']; res[('129 ok', p[3]==p[4])]+=1
        else: res['130 ok']+=1
        pend['last']=None
    elif tag=='128 put': pend['128']=(a,d,i)
    elif tag=='128 after': p=pend['128']; res[('128 moved to iobj room', room(p[1])==p[2] if p[1] in ENT else None)]+=1; log.append(('put',)+p)
    elif tag=='chance': pend['ch']=(a,d)
    elif tag=='130 test': pend['last']='130'
    elif tag=='chance ok': res['chance ok']+=1
    else:
        res[tag]+=1
        if tag in ('signal','ask','erase','await match'): log.append((tag,a,d,i, ' '.join('%02X'%mem[g.m.ix+k] for k in range(6))))
for k in BP: pass
for n in range(115):
    out=run_with_bps(g,'WAIT',list(BP),hit,max_slices=6000)
    if 'Perhaps you should' in text(out): print('game over at turn', n); break
print(dict(res))
for x in log[:40]: print(x)
