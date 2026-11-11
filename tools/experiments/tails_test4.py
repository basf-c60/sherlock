"""Waiting statement proven later: reaches $BBD3 onwards. 9 November (chains as in major_test.py)."""
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source'); sys.path.insert(0,'tools/experiments')
import tails_test as T
from tails_test2 import say
print('--- Major: waiting, then confession poke (bit 1 of $9972), then the opium-den statement')
g,m=T.setup(False)
say(g,'MAJOR FFOULKES IS INNOCENT',330); print('   flags $9968 = %02X'%m[0x9968])
m[0x9972]|=2
say(g,'MAJOR FFOULKES VISITED THE OPIUM DEN',420); print('   flags $9968 = %02X'%m[0x9968])
print('--- plain: opium den statement alone, bit 1 poked, nothing waiting')
g,m=T.setup(False); m[0x9972]|=2
say(g,'MAJOR FFOULKES VISITED THE OPIUM DEN',420); print('   flags $9968 = %02X'%m[0x9968])
print('--- two waiting (Major innocent + Mrs Brown killed herself), then opium den proven')
g,m=T.setup(False)
say(g,'MAJOR FFOULKES IS INNOCENT',200); say(g,'MRS BROWN KILLED HERSELF',200); m[0x9972]|=2
say(g,'MAJOR FFOULKES VISITED THE OPIUM DEN',460)
