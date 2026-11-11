"""Try to reach the untested tails of $BB67 (Lestrade's remark handler) and $B98C. 9 November.
Lestrade's room is poked in as the player's room (as case_test.py does); evidence flags optionally set."""
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT={e['id']:e for e in O.entities()}; RM=RMOD.rooms()
BPS=[0xBB67,0xBBBE,0xBBC9,0xBBD3,0xBBD9,0xBBDE,0xBBE5,0xBBFB,0xBC2F,0xBB87,0xBBC4,0xB9AC,0xB9B4,0xB9CA]
def setup(ev):
    g=booted(); mem=g.m.memory
    r=mem[ENT[2]['address']+15]; a=RM[r]['address']
    mem[0x8CC9]=r; mem[0xA00A]=r; mem[0xDCFF]=a&255; mem[0xDD00]=a>>8; mem[0xDD01]=r
    mem[0x8CBA+1]=0xFF
    if ev:
        for t in (46,57): mem[ENT[t]['address']+6]|=0xC0
        mem[ENT[93]['address']+6]|=0x80
    return g,mem
SENT=sys.argv[1:] or ['BASIL','KILLED','BASIL KILLED','MRS BROWN','BASIL KILLED MRS BROWN AND BASIL HAS THE PLANS','BASIL KILLED MRS BROWN. BASIL HAS THE PLANS','BASIL KILLED MRS BROWN AND TRICIA','HELLO AND GOODBYE','THE THE THE','KILLED KILLED BASIL','MRS BROWN KILLED HERSELF AND BASIL KILLED MRS BROWN','MRS JONES KILLED TRICIA FENDER AND MRS BROWN KILLED HERSELF']
if __name__=="__main__":
  for ev in (False,True):
      print('=== evidence' if ev else '=== no evidence')
      for s in SENT:
          g,mem=setup(ev); hits=[]
          out=run_with_bps(g,'SAY TO LESTRADE "%s"'%s,BPS,lambda g,pc:hits.append(pc),max_slices=6000)
          print('%-60s %s | %s'%(s,' '.join('%04X'%h for h in hits),text(out)[-150:].replace('\n',' ')))
