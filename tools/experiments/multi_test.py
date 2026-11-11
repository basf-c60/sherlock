import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
g=booted(); mem=g.m.memory
w=lambda a: mem[a]|mem[a+1]<<8
for c in ['TAKE LAMP. EXAMINE LAMP. INVENTORY', 'TAKE PAPER AND EXAMINE IT']:
    n=[0]
    out=run_with_bps(g,c,[0xD715],lambda g,pc: n.__setitem__(0,n[0]+1),max_slices=6000)
    print(repr(c), 'reads of a line:', n[0], 'minute', w(0x9FDD), '|', text(out)[-260:])
