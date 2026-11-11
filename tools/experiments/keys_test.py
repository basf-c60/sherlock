"""One-key moves, revisits, the fourth verb word, KILL/BREAK.

Cursor keys on an empty line ($D978): '[' (cursor up as GET-KEY passes
it) = N, $0A = S, $08 = W. A room's long text only on the first visit
($CA9E). GO NORTH; EXAMINE CLOSELY LAMP ('You closely examine...').
BREAK = KILL ('ONLY AN IDIOT WOULD TRY THAT.')."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
g = booted()
def do(c, raw=False):
    g.clear_output()
    if raw:
        g.queue(c); out = text(run_with_bps(g, None, [], None, max_slices=4000))
    else:
        out = text(run_with_bps(g, ' ' + c, [], None, max_slices=4000))
    print(f'{c!r:28}|', out[:170])
do('OPEN PLAIN DOOR')
do('[', raw=True)
do('\x0a', raw=True)
do('\x08', raw=True)
do('GO NORTH')
do('GO SOUTH')
do('EXAMINE CLOSELY LAMP')
do('EXAMINE LAMP CAREFULLY')
do('BREAK WATSON')
do('KILL WATSON')
