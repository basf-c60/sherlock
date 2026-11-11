"""Re-type the message entries in a .skool file from 'b' (bytes) to 't' (text), so that SkoolKit's
Messages memory-map page lists them. The ctl keeps them as 'b' blocks because a 't' block would
be printed as long DEFM lines and the addresses inside a message (room records point into them)
could no longer be linked. Usage: skool_types.py file.skool"""
import re
import sys

path = sys.argv[1]
entries = open(path).read().split('\n\n')
n = 0
for i, e in enumerate(entries):
    lines = e.split('\n')
    k = next((j for j, l in enumerate(lines) if not l.startswith(';')), None)
    head = [l for l in lines if l.startswith('; ')]
    if k is not None and head and head[0].startswith('; Message') and lines[k][:1] == 'b':
        lines[k] = 't' + lines[k][1:]
        entries[i] = '\n'.join(lines)
        n += 1
open(path, 'w').write('\n\n'.join(entries))
print('message entries re-typed:', n)
