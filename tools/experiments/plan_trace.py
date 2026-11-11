import sys, collections; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import allplans as ap
recs, starts, ins = ap.collect()
from plan import walk as _w
for _s in (0xF3AD, 0xF05C): ins.update(_w([_s]))
g=booted(); mem=g.m.memory
hits=collections.Counter(); bad=collections.Counter(); ops=collections.Counter()
def hit(g,pc):
    hl=g.m.hl; act=mem[0xA036]
    hits[(act,hl)]+=1; ops[mem[hl]&15]+=1
    if hl not in ins: bad[(act,hl)]+=1
cmds=['WAIT']*60 + ['N','N','LOOK','S','WAIT','WAIT']+['WAIT']*40
for i,c in enumerate(cmds):
    out=run_with_bps(g,c,[0xCC9B],hit,max_slices=6000)
    if i%20==0: print(i, text(out)[-200:])
print('distinct instructions fetched', len({h for _,h in hits}), 'total fetches', sum(hits.values()))
print('not in decoded set:', dict(bad))
print('opcodes', dict(ops))
by=collections.defaultdict(set)
for a,h in hits: by[a].add(h)
for a in sorted(by): print('actor',a, len(by[a]), 'instrs, e.g.', ' '.join(f'${x:04X}' for x in sorted(by[a])[:8]))
