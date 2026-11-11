import sys, collections; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
g=booted(); mem=g.m.memory
for cmd in ['LOOK','WAIT','LOOK','N','TAKE LAMP','WAIT']:
    c=collections.Counter()
    def hit(g,pc): c[(pc, mem[0xA036] if pc!=0xCC37 else g.m.a)]+=1
    out=run_with_bps(g,cmd,[0xB91F,0xCC37,0xCC78],hit,max_slices=6000)
    by=collections.Counter(pc for pc,_ in c.elements())
    print(cmd, {hex(k):v for k,v in by.items()}, 'actors at CC37:', sorted({a for (pc,a) in c if pc==0xCC37})[:30], '|', text(out)[-80:])
