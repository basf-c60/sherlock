"""Tricia Fender is Mrs Jones in disguise: ask Tricia about the bloodstained clothes (both put in the player room), then ask Mrs Jones about her alibi. Shows $998F, $9993 and the actor table change.  python3 tools/experiments/jones_marker_test.py"""
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O
ENT={e['id']:e for e in O.entities()}
g=booted(); m=g.m.memory
pr=m[0xA00A]
for t in (13,67):
    a=ENT[t]['address']; m[a+1]=0xFF; m[a+15]=pr
ids=lambda:[m[0x9860+8*i] for i in range(24)]
hits=[]
def on(g,pc): hits.append(hex(pc))
cmds=[' SAY TO TRICIA "TELL ME ABOUT BLOODSTAINED CLOTHES"',' SAY TO MRS JONES "TELL ME ABOUT YOUR ALIBI"',' SAY TO MRS JONES "TELL ME ABOUT WHAT HAPPENED"']
for cmd in cmds:
    hits.clear(); g.clear_output()
    out=run_with_bps(g,cmd,[0xE1B4,0xE1CB,0xE03A,0xE188,0xE18A,0xE199],on,max_slices=4000)
    print(cmd,'|',hits,'|',text(out)[-300:])
    print('   9993=%02X 998F=%02X'%(m[0x9996],m[0x9992]),'13 in table',13 in ids(),'95 in table',95 in ids())
