import re, sys
sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
cmds=[l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
g=booted(); m=g.m.memory
def run1(c):
    g.clear_output()
    return text(run_with_bps(g,' '+c,[],None,max_slices=6000))
def clk(): return '%s %d:%02d%s r%d'%('MTWTFSS'[m[0x9FE1]%7] if False else m[0x9FE1],m[0x9FE0],m[0x9FDF],chr(m[0x9FE2]),m[0x8CC9])
out=open(sys.argv[2],'w')
last=''; prev=''
for i,c in enumerate(cmds,1):
    mm=re.match(r'\(until (.*?)\) (.*)',c)
    n=1
    if mm:
        n=0
        for _ in range(80):
            n+=1; prev=last; last=run1(mm.group(2))
            if mm.group(1).lower() in last.lower(): break
    else:
        prev=last; last=run1(c)
    out.write('%3d %-50s x%-2d -> %s | %s\n'%(i,c[:50],n,clk(),' '.join(last.split())[:(1200 if i>len(cmds)-4 else 110)])); out.flush()
out.write('\nFINAL REPLY (previous reply + last reply): '+' '.join((prev+' '+last).split())+'\n')
out.write('end flag A0DA=%d\n'%m[0xA0DA]); out.close()
