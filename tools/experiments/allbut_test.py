"""ALL BUT, IN, pronouns, abbreviations, synonyms, '@' and scenery, in Holmes's rooms.

ALL BUT: in the closet with the money dropped, TAKE ALL BUT MONEY takes
the money too. With --trace, breakpoints on $B517-$B541 show IY = $D36A
on entry: the search routine's address, not a parse node (the bug)."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
g = booted(); m = g.m.memory
def do(c):
    g.clear_output(); print(f'{c:34}|', text(run_with_bps(g, ' ' + c, [], None, max_slices=6000))[:200])
for c in ['TAKE WINDOWS', 'EX LAMP', 'EXAMINE LAM', 'EXAMINATION LAMP', 'READ LAMP', 'PICK LAMP', 'I', 'L',
          'PUT LAMP IN SOFA', 'PUT LAMP SOFA', 'TAKE LAMP', 'DROP IT', 'TAKE LAMP BECAUSE EXAMINE LAMP']:
    do(c)
    if c == 'PUT LAMP IN SOFA':
        print('      tokens at $5B81:', bytes(m[0x5B81:0x5B81 + 14]).hex(' '), '(IN -> $E0 $0956, VISITED)')
for c in ['OPEN PLAIN DOOR', 'NORTH']:
    do(c)
g.clear_output(); g.queue('@'); print(f"{'@ (repeat NORTH)':34}|", text(run_with_bps(g, None, [], None, max_slices=4000))[:120])
for c in ['DROP MONEY', 'TAKE ALL BUT MONEY', 'INVENTORY']:
    do(c)
if '--trace' in sys.argv:
    do('DROP ALL')
    seen = []
    def hit(g, pc):
        if len(seen) < 12:
            seen.append(f'${pc:04X} IY=${g.m.iy:04X} candidate={g.m.memory[0xA034]}')
    run_with_bps(g, ' TAKE ALL BUT MONEY', [0xB517, 0xB521, 0xB524], hit, max_slices=6000)
    print('\n'.join(seen))
