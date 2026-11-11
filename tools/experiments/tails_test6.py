"""$BBFB-$BC17 (bit-4 statement named in the summary). Only the four flags-$B4 statements have bit 4, and each
has an always-true evidence child (you/you seen), so no typed sentence reaches it. POKE: clear bit 7 of the
player's own +6 (never seen) so the child fails, to show the branch runs. 9 November."""
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source'); sys.path.insert(0,'tools/experiments')
import tails_test as T
from tails_test2 import say
from tails_test5 import near
from play import run_with_bps, text
g,m=T.setup(False)
say(g,'TRICIA FENDER KILLED MRS JONES',260); near(g); m[0x9972]|=2
P6=T.ENT[0]['address']+6
hits=[]
def cb(g,pc):
    hits.append(pc); print('   %04X player+6=%02X child flags $99C4=%02X'%(pc,m[P6],m[0x99C4]))
    if pc==0xBB67: m[P6]&=0x7F          # the player is not 'seen' while the case is checked
g.run(max_slices=1500); g.clear_output()
out=run_with_bps(g,'  SAY TO LESTRADE "MAJOR FFOULKES VISITED THE OPIUM DEN"',T.BPS+[0xBC46,0xBC74,0xBC9C],cb,max_slices=6000)
print(' '.join('%04X'%h for h in hits)); print(text(out)[:600])
