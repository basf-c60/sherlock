"""Chains of remarks to Lestrade to reach the summary branch of $BB67 (waiting statements). 9 November."""
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import tails_test as T
BPS=T.BPS+[0xBC46,0xBC74,0xBC9C]
def say(g,s,show=330):
    hits=[]; g.run(max_slices=1500); g.clear_output()
    out=run_with_bps(g,'  SAY TO LESTRADE "%s"'%s,BPS,lambda g,pc:hits.append(pc),max_slices=6000)
    t=text(out); i=t.find('Lestrade')
    print('%-48s %s\n     %s'%(s,' '.join('%04X'%h for h in hits),t[:show].replace('\n',' ')))
def ev(mem,on=True):
    for t in (46,57): T.ENT[t]  # ids
    for t in (46,57): mem[T.ENT[t]['address']+6]|=0xC0
    mem[T.ENT[93]['address']+6]|=0x80
if __name__=='__main__':
    print('--- no sense'); g,m=T.setup(False); say(g,'BASIL KILLED'); say(g,'HELLO AND GOODBYE')
    print('--- A: one waiting statement, then evidence, then a proven remark'); g,m=T.setup(False)
    say(g,'BASIL KILLED MRS BROWN'); ev(m); say(g,'MRS BROWN KILLED HERSELF')
    print('--- B: two waiting statements, then a proven remark'); g,m=T.setup(False)
    say(g,'BASIL KILLED MRS BROWN'); say(g,'BASIL HAS THE PLANS'); say(g,'MRS BROWN KILLED HERSELF')
    print('--- C: waiting statement, a proven remark, no evidence'); g,m=T.setup(False)
    say(g,'BASIL KILLED MRS BROWN'); say(g,'MRS BROWN KILLED HERSELF'); say(g,'WAIT')
