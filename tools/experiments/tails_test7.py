"""Orders given to Lestrade ('SAY TO LESTRADE "..."') that reach the tail of $B98C (unparsable order, ALL used up,
more sentences after a dropped one). 9 November."""
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source'); sys.path.insert(0,'tools/experiments')
import tails_test as T
from play import run_with_bps, text
B=[0xB98C,0xB9AC,0xB9B1,0xB9B4,0xB9BA,0xB9C7,0xB9CA,0xB9E9,0xB9F2,0xB9F5]
for s in ['WAIT','WAIT AND WAIT','WAIT AND GO NORTH','GO NORTH AND WAIT','TAKE ALL','TAKE ALL AND WAIT','DROP ALL','DROP ALL BUT MONEY','TAKE ALL BUT LAMP','GO BLAH AND WAIT','HELLO AND GOODBYE','GOODBYE AND HELLO','EXAMINE MONEY AND WAIT','GIVE MONEY TO WATSON AND WAIT','GO EAST','GO EAST AND GO EAST']:
    g,m=T.setup(False); hits=[]
    g.run(max_slices=1500); g.clear_output()
    out=run_with_bps(g,'  SAY TO LESTRADE "%s"'%s,B,lambda g,pc:hits.append(pc),max_slices=6000)
    t=text(out); i=t.find('You talk')
    print('%-32s %s | %s'%(s,' '.join('%04X'%h for h in hits),t[i:i+170].replace('\n',' ')))
