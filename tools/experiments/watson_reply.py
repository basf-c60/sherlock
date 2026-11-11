import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
g=booted(); mem=g.m.memory
w=lambda a: mem[a]|mem[a+1]<<8
for c in ['SAY TO WATSON "MRS BROWN KILLED HERSELF"', 'SAY TO WATSON "PHIPPS HAS PLANS"', 'SAY TO WATSON "THE LAMP IS ON"']:
    out=run_with_bps(g,c,[],None,max_slices=5000)
    h=w(0x9FF4); node=' '.join('%02X'%mem[h+k] for k in range(3)) if h else '-'
    print(repr(c), '| $9FF4 head', hex(h), node, '|', text(out)[-170:])
