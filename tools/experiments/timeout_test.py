import sys, time; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
g=booted(); mem=g.m.memory
w=lambda a: mem[a]|mem[a+1]<<8
t0=time.time()
print('minute before', w(0x9FDD))
out=run_with_bps(g,'TAK',[],None,max_slices=20000, idle_after=6500)
print('minute after', w(0x9FDD), 'secs', round(time.time()-t0), '|', text(out)[-200:])
