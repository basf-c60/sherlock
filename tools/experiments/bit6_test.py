import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O
ENT={e['id']:e for e in O.entities()}
def run(poke, cmds):
    g=booted(); mem=g.m.memory
    for c in cmds:
        if poke:
            p=mem[0x9871]|mem[0x9872]<<8   # Watson's script position
            while mem[p]==0: p+=1
            mem[p]|=0x40
        hits=[]
        out=run_with_bps(g,c,[0xCBA7, 0xCBB2],lambda g,pc: hits.append((hex(pc), hex(mem[0xB934]))),max_slices=5000)
        print(('POKED ' if poke else 'plain ')+repr(c), '| watson in', mem[ENT[3]['address']+1], '| guard', hits[:4], '|', text(out)[-160:])
cmds=['SAY TO WATSON "GET OUT"','WAIT','LOOK']
run(False, cmds); run(True, cmds)
