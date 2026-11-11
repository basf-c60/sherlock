import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
g=booted(); mem=g.m.memory
w=lambda a: mem[a]|mem[a+1]<<8
for c in ['WAIT UNTIL 9AM', 'LOOK', 'WAIT UNTIL 10']:
    out=run_with_bps(g,c,[],None,max_slices=20000)
    t=text(out)
    print(repr(c), 'minute', w(0x9FDD), 'player plan verb', mem[0x9863], '|', t[:80], '...', t[-60:])
