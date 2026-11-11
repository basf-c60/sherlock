import sys, collections; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import allplans as ap
P=open('p.bin','rb').read()
recs, starts, ins = ap.collect()
g=booted(); mem=g.m.memory
log=[]
def hit(g,pc):
    log.append((g.m.pc==0xF1F3, mem[0xA036], mem[0xA034], mem[0x9FE0], chr(mem[0x9FE2]) if 32<=mem[0x9FE2]<127 else mem[0x9FE2], last[0]))
last=['']
for i in range(110):
    out=run_with_bps(g,'WAIT',[0xF1D8,0xF1F3],hit,max_slices=6000)
    t=text(out); 
    import re
    m=re.findall(r'(\w{3} \d\d:\d\d[ap]m)', t)
    if m: last[0]=m[-1]
    if 'Perhaps you should' in t: print('game over at', last[0]); break
print('verb 136 successes (actor, arg, $9FE0, $9FE2, clock shown):')
import collections
for x,c in collections.Counter(log).items(): print('  ', x, c)
cov=set()
for a,r in ins.items():
    for k in range(r['size']): cov.add(a+k)
changed=[a for a in sorted(cov) if mem[a]!=P[a-0x5d80]]
print('script bytes changed:', len(changed))
spent=sorted({a for a in changed if mem[a]==0})
starts_changed=sorted({max(x for x in ins if x<=a) for a in changed})
for s in starts_changed: print(f'  ${s:04X} {ins[s]["text"]}  oneshot={ins[s]["oneshot"]}  now', ' '.join('%02X'%mem[s+k] for k in range(ins[s]['size'])))
