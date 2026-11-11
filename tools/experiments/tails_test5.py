"""Summary branch with a bit-4 waiting statement ($BBFB-$BC17) and with a bit-5 one ($BBD9). 9 November.
The player is re-poked into Lestrade's room before each remark (he wanders off by cab)."""
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source'); sys.path.insert(0,'tools/experiments')
import tails_test as T
from tails_test2 import say
RM=T.RM; ENT=T.ENT
def near(g):
    m=g.m.memory; r=m[ENT[2]['address']+15]; a=RM[r]['address']
    m[0x8CC9]=r; m[0xA00A]=r; m[0xDCFF]=a&255; m[0xDD00]=a>>8; m[0xDD01]=r
if __name__=="__main__":
    print('--- A: a flags-$B4 statement waiting, then the opium-den statement proven')
    g,m=T.setup(False)
    say(g,'TRICIA FENDER KILLED MRS JONES',260); near(g); m[0x9972]|=2
    say(g,'MAJOR FFOULKES VISITED THE OPIUM DEN',520)
    print('--- B: Major innocent waiting, then a plain proven statement elsewhere (bit-5 provable later)')
    g,m=T.setup(False)
    say(g,'MAJOR FFOULKES IS INNOCENT',200); near(g); m[0x9972]|=2; m[0x9968]|=0  # now provable
    say(g,'MRS BROWN KILLED HERSELF',520)
