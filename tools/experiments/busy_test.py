import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
g=booted(); mem=g.m.memory
w=lambda a: mem[a]|mem[a+1]<<8
for c in ['LOOK','WAIT','TAKE LAMP','EXAMINE LAMP','WAIT']:
    out=run_with_bps(g,c,[],None,max_slices=4000)
    print(f'{c!r:16} now(9FDD)={w(0x9FDD):4}  you +6/+7={w(0x9866):4}  watson={w(0x9876):4} lestrade={w(0x986E):4} | {text(out)[-40:]!r}')
