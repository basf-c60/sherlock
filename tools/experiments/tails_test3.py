"""Statements with flag bits 4/5 (waiting, with routine) to reach $BBD3-$BBE4 and $BBFB-$BC17. 9 November."""
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source'); sys.path.insert(0,'tools/experiments')
import tails_test as T
from tails_test2 import say, ev, BPS
for evd in (False, True):
    print('=== evidence' if evd else '=== none')
    for s in ['THE MAJOR IS INNOCENT','MAJOR PERCIVAL FFOULKES IS INNOCENT','TRICIA FENDER IS MRS JONES','TRICIA FENDER HAD PLANS','TRICIA FENDER HAS PLANS','MRS JONES KILLED TRICIA FENDER','THE MAJOR WAS IN THE OPIUM DEN']:
        g,m=T.setup(evd); say(g,s,260)
