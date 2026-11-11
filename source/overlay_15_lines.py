"""One comment per instruction: the lines that used to share a group comment each get their own.

LINES maps an instruction address to its comment. apply() merges them into the generated game.ctl:
an existing 'C addr' line is replaced, a missing one is added in address order inside its block."""
import re

LINES = {}
try:
    from lines_auto import AUTO
except ImportError:
    AUTO = {}


def L(d):
    LINES.update(d)


def apply(lines):
    out = []
    i = 0
    n = len(lines)
    pending = dict(LINES)
    allv = dict(AUTO)
    allv.update(LINES)
    def flush(block):
        head, subs = [], []
        for ln in block:
            m = re.match(r'^([A-Z]) (\d+)(?:,\d+)?(?: |$)', ln)
            if m and m.group(1) in 'CBTWSUEM' and head:
                subs.append((int(m.group(2)), ln, m.group(1)))
            else:
                head.append(ln)
        if head and re.match(r'^[a-z] (\d+)', head[0]):
            start = int(head[0].split()[1])
            # the block's last address is unknown here: take every pending override whose
            # address lies between this block's start and the next block's start
            return head, subs, start
        return head, subs, None
    # split into blocks
    blocks, cur = [], []
    for ln in lines:
        if re.match(r'^[a-z] \d+', ln) and cur:
            blocks.append(cur); cur = []
        cur.append(ln)
    blocks.append(cur)
    starts = []
    for b in blocks:
        m = re.match(r'^[a-z] (\d+)', b[0])
        starts.append(int(m.group(1)) if m else -1)
    import bisect
    real = [(s, k) for k, s in enumerate(starts) if s >= 0]
    real_starts = [s for s, _ in real]
    per_block = {}
    for addr, text in allv.items():
        j = bisect.bisect_right(real_starts, addr) - 1
        if j >= 0:
            per_block.setdefault(real[j][1], {})[addr] = text
    res = []
    for k, b in enumerate(blocks):
        ov = per_block.get(k)
        if not ov or starts[k] < 0:
            res.extend(b); continue
        head, subs, _ = flush(b)
        subd = {}
        order = []
        for a, ln, kind in subs:
            subd.setdefault(a, []).append(ln)
        for a, text in ov.items():
            subd[a] = [ln for ln in subd.get(a, []) if not ln.startswith('C ')] + ['C %d %s' % (a, text)]
        res.extend(head)
        for a in sorted(subd):
            # sub-blocks (B/T/W) first so their own line stays before the comment of the same address
            res.extend(sorted(subd[a], key=lambda s: s.startswith('C ')))
    return res


# Hand-written comments (they take priority over the generated ones in lines_auto.py).
L({
    # Action record $EF9C: the messenger takes a note from Basil
    0xEF9E: 'Point HL at the message text, "A messenger arrives at the door, takes a note from Basil and disappears down the street." ($75E8)',
    0xEFA1: 'A = 1: the value the output switch needs for the message to appear on screen. (A second entry point: the sibling record at $EFAC joins here with its own HL.)',
    0xEFA3: 'Store it in the output-switch byte ($5C3C), so the print routine really draws the text instead of staying silent',
    0xEFA6: 'Print the message at HL ($A59F)',
    0xEFA9: 'OR $01 makes A non-zero, which clears the zero flag: the plan interpreter reads "not zero" as "the action happened"',
    0xEFAB: 'Return to the plan interpreter',
})
