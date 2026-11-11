import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
g0=booted(); snap=bytes(g0.m.memory)
def say(cmds):
    g=g0; g.m.set_memory_block(0,snap); g.clear_output()
    for c in cmds:
        g.clear_output(); out=run_with_bps(g,c,[],None,max_slices=3000)
        print(f'  {c!r:28} -> {text(out)[:150]}')
for case in [['TAKE PLAIN DOOR'],['TAKE WATSON'],['DROP LAMP'],['TAKE LAMP','DROP LAMP'],
             ['TALK TO LAMP'],['TALK TO WATSON'],['GO THROUGH LAMP'],['GO THROUGH PLAIN DOOR'],
             ['FOLLOW WATSON'],['FOLLOW LAMP'],['WAIT UNTIL 5'],['WAIT UNTIL 9:00'],
             ['PAY 5 TO WATSON'],['TAKE DISGUISE'],['EXAMINE DISGUISE'],['GIVE LAMP TO WATSON'],
             ['TAKE LAMP','GIVE LAMP TO LAMP'],['TAKE LAMP','TAKE LAMP']]:
    print(case); say(case)
