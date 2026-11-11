#!/usr/bin/env python3
# NOTE: it must read a skool built with source/lines_auto.py empty (AUTO = {}), else it finds nothing to do.
"""Generate one comment per instruction for every code line that has none of its own.

Reads game.skool, writes source/lines_auto.py (a dict address -> text) that overlay_15_lines merges.
Phrases each instruction in English, naming routines and variables from the disassembly itself, and
turns a conditional jump into the condition that the previous instruction set up."""
import re, sys, collections

SK = '/home/claude/sherlock/game.skool'
OUT = '/home/claude/sherlock/source/lines_auto.py'

ROM = {0x5C3C: 'the output-switch byte (TV_FLAG)', 0x5C3A: 'the error byte (ERR_NR)',
       0x5C78: 'the frame counter (FRAMES)', 0x5C08: 'the last key pressed (LAST_K)',
       0x5C0B: 'the tape header workspace', 0x5C42: 'the BASIC workspace', 0x5C3B: 'FLAGS',
       0x04C2: 'the ROM tape-save routine', 0x0556: 'the ROM tape-load routine',
       0x22AA: 'the ROM pixel-address routine', 0x0010: 'the ROM print-character routine',
       0x0D6B: 'the ROM clear-screen routine', 0x1601: 'the ROM open-channel routine',
       0x0F12: 'the ROM editor entry', 0x028E: 'the ROM keyboard scan', 0x1F3A: 'the ROM BREAK test'}

REG16 = ('BC', 'DE', 'HL', 'IX', 'IY', 'SP', 'AF')
BITNAMES5 = {7: 'revealed', 6: 'person', 5: 'open', 4: 'on', 3: 'contents visible', 2: 'full',
             1: 'only in the deep stream', 0: 'locked'}
BITNAMES6 = {7: 'seen', 6: 'examined', 5: 'countable'}
BITNAMES4 = {7: 'needs light'}
FIELDS = {0: 'number', 1: 'holder', 2: 'size', 3: 'weight', 4: 'type', 5: 'flags', 6: 'flags 2',
          7: 'noun low', 8: 'noun high', 9: 'adjective low', 10: 'adjective high', 15: 'rooms'}


def h(n, w=None):
    return '$%04X' % n if (w == 4 or n > 255) else '$%02X' % n


def unmacro(t):
    t = re.sub(r'#LINK\([^)]*\)\(([^)]*)\)', r'\1', t)
    t = re.sub(r'#R(\$[0-9A-F]{4})\(([^)]*)\)', r'\2', t)
    return re.sub(r'#R(\$[0-9A-F]{4})', r'\1', t)


def parse():
    lines = open(SK).read().split('\n')
    rows = []          # (addr, ins, comment, kind, title_index)
    blocks = []        # (start, title, desc)
    title = ''
    desc = []
    cur = None
    for i, l in enumerate(lines):
        if l.startswith(';'):
            if not cur:
                desc.append(unmacro(l[2:]) if len(l) > 1 else '')
            continue
        if not l.strip():
            desc = []
            continue
        m = re.match(r'^([ *a-z])\$([0-9A-F]{4}) (.*)$', l)
        if not m:
            continue
        mark = m.group(1)
        a = int(m.group(2), 16)
        body = m.group(3)
        if ';' in body:
            ins, cm = body.split(';', 1)
        else:
            ins, cm = body, ''
        ins = ins.strip()
        if mark in 'bcwstu':
            t = desc[0] if desc else ''
            blocks.append((a, t, ' '.join(desc), mark))
            desc = []
        rows.append((a, ins, unmacro(cm.strip()), mark, len(blocks) - 1))
    return rows, blocks


rows, blocks = parse()
block_starts = [b[0] for b in blocks]
import bisect


def block_of(a):
    j = bisect.bisect_right(block_starts, a) - 1
    return blocks[j] if j >= 0 else None


def short(t, n=58):
    t = re.sub(r'\s+', ' ', t).strip().rstrip('.')
    t = re.sub(r'^(Routine|Entry point|Action record|Plan script|Sub-script): ?', lambda m: m.group(0), t)
    if len(t) > n:
        t = t[:n].rsplit(' ', 1)[0] + '...'
    return t


# symbols: variables named by "$XXXX: the ..." comments, and "$XXXX (the ...)" mentions
SYM = {}
for a, ins, cm, mark, bi in rows:
    m = re.match(r'^\$([0-9A-F]{4}): (.*)$', cm)
    if m:
        SYM.setdefault(int(m.group(1), 16), m.group(2))
for b in blocks:
    for m in re.finditer(r'\$([0-9A-F]{4}) \((the [^)]{4,60})\)', b[2]):
        SYM.setdefault(int(m.group(1), 16), m.group(2))
# continuation of wrapped "$XXXX: the ..." comments
for i, (a, ins, cm, mark, bi) in enumerate(rows):
    m = re.match(r'^\$([0-9A-F]{4}): (.*)$', cm)
    if m and i + 1 < len(rows) and rows[i + 1][1] == '' and rows[i + 1][2]:
        pass
SYM = {k: re.sub(r'\s*\(.*$', '', v).rstrip(',;:') for k, v in SYM.items()}
SYM = {k: v for k, v in SYM.items() if len(v) < 60}
CODE_ADDRS = {a for a, ins, cm, mark, bi in rows if ins and not ins.startswith('DEF')}


def name(a, kind='mem'):
    """A phrase for the address a."""
    if a in ROM:
        return ROM[a] + ' (%s)' % h(a, 4)
    if a in SYM and SYM[a].lower() not in ('unused', 'not identified'):
        return SYM[a] + ' (%s)' % h(a, 4)
    b = block_of(a)
    if b and a >= 0x5D00:
        if a == b[0] and b[1].startswith('Message: '):
            return 'the message %s (%s)' % (short(b[1][9:], 50), h(a, 4))
        if a == b[0] and b[1]:
            return '"%s" (%s)' % (short(b[1], 50), h(a, 4))
        if b[1] and b[3] in 'cb':
            if b[3] == 'c':
                return '%s in "%s"' % (h(a, 4), short(b[1], 44))
            return '%s in "%s"' % (h(a, 4), short(b[1], 44))
    return h(a, 4)


def rname(a):
    """A routine called or jumped to."""
    if a in ROM:
        return ROM[a] + ' (%s)' % h(a, 4)
    b = block_of(a)
    if b and b[3] == 'c' and b[0] == a and b[1]:
        return 'the routine "%s" (%s)' % (short(b[1], 54), h(a, 4))
    if b and b[3] == 'c' and b[1]:
        return '%s (inside "%s")' % (h(a, 4), short(b[1], 44))
    return h(a, 4)


# jump targets, for resetting what we know about registers
TARGETS = set()
for a, ins, cm, mark, bi in rows:
    m = re.match(r'^(?:JR|JP|DJNZ|CALL)(?: [A-Z]+,)? ?\$([0-9A-F]{4})$', ins)
    if m:
        TARGETS.add(int(m.group(1), 16))

COND = {'Z': 'zero', 'NZ': 'not zero', 'C': 'carry', 'NC': 'no carry', 'PE': 'parity even',
        'PO': 'parity odd', 'P': 'positive', 'M': 'negative'}

FLAGRE = re.compile(r'^(CP|AND|OR|XOR|SUB|ADD A|ADC A|SBC A|BIT|INC|DEC|SCF|CCF|NEG|RRCA|RLCA|SBC HL|ADD HL|SRL|SLA|RL|RR|SRA)\b')


GENERIC = {'Z': 'the zero flag is set', 'NZ': 'the zero flag is clear', 'C': 'the carry flag is set',
           'NC': 'the carry flag is clear', 'P': 'the last result was positive (sign flag clear)',
           'M': 'the last result was negative (sign flag set)', 'PE': 'the parity/overflow flag is set',
           'PO': 'the parity/overflow flag is clear'}


def cond_phrase(prev, cc, ctx):
    """Describe a condition code given the instruction that set the flags."""
    p = prev or ''
    m = re.match(r'^CP (.*)$', p)
    if m:
        what = operand(m.group(1), ctx, imm=True)
        return {'Z': 'A equals %s' % what, 'NZ': 'A differs from %s' % what,
                'C': 'A is below %s' % what, 'NC': 'A is %s or more' % what}.get(cc)
    m = re.match(r'^BIT (\d),(.*)$', p)
    if m:
        bit = int(m.group(1))
        tgt = m.group(2)
        nm = bitname(bit, tgt)
        what = 'bit %d of %s' % (bit, regdesc(tgt, ctx)) + (' (%s)' % nm if nm else '')
        return {'Z': '%s is clear' % what, 'NZ': '%s is set' % what}.get(cc)
    if p in ('AND A', 'OR A'):
        return {'Z': 'A is zero', 'NZ': 'A is not zero', 'C': 'carry is set', 'NC': 'carry is clear'}.get(cc)
    m = re.match(r'^AND \$([0-9A-F]{2})$', p)
    if m and cc in ('Z', 'NZ'):
        bits = [b for b in range(8) if int(m.group(1), 16) >> b & 1]
        if len(bits) == 1:
            return {'Z': 'bit %d of A was clear' % bits[0], 'NZ': 'bit %d of A was set' % bits[0]}[cc]
        bl = ' or '.join(map(str, bits))
        return {'Z': 'bits %s of A were all clear' % bl.replace(' or ', ', '), 'NZ': 'any of bits %s of A was set' % bl.replace(' or ', ', ')}[cc]
    m = re.match(r'^(AND|OR|XOR) (.*)$', p)
    if m:
        if m.group(1) == 'AND':
            return {'Z': 'none of those bits of A are set', 'NZ': 'one of those bits of A is set'}.get(cc)
        return {'Z': 'the result is zero', 'NZ': 'the result is not zero'}.get(cc)
    if p == 'OR H' or p == 'OR L':
        return {'Z': 'HL is zero', 'NZ': 'HL is not zero'}.get(cc)
    m = re.match(r'^(INC|DEC) (.*)$', p)
    if m and cc in ('Z', 'NZ'):
        t = regdesc(m.group(2), ctx)
        return {'Z': '%s has become zero' % t, 'NZ': '%s is not zero' % t}.get(cc)
    m = re.match(r'^(SUB|SBC A,|SBC HL,)\s?(.*)$', p)
    if m:
        return {'Z': 'the two values are equal', 'NZ': 'the two values differ',
                'C': 'it went below zero (carry)', 'NC': 'it did not go below zero'}.get(cc)
    if p == 'SCF':
        return {'C': 'carry is set (always)'}.get(cc)
    if re.match(r'^ADD (HL|IX|IY),', p):
        return {'C': 'the addition overflowed (carry)', 'NC': 'the addition did not overflow'}.get(cc)
    if p.startswith('ADD') or p.startswith('ADC'):
        return {'Z': 'the result is zero', 'NZ': 'the result is not zero', 'C': 'it overflowed (carry)',
                'NC': 'it did not overflow'}.get(cc)
    return None


def bitname(bit, tgt):
    m = re.match(r'^\((IX|IY)([+-]\d+)\)$', tgt.replace('$', ''), re.I)
    return None


def regdesc(t, ctx):
    t = t.strip()
    m = re.match(r'^\((I[XY])([+-])\$([0-9A-F]{2})\)$', t)
    if m:
        d = int(m.group(3), 16)
        if m.group(2) == '-':
            d = -d
        return field(m.group(1), d, ctx)
    if t == '(HL)':
        hl = ctx.get('HL')
        if hl is not None:
            return 'the byte at %s' % name(hl)
        return 'the byte HL points at'
    if t == '(DE)':
        return 'the byte DE points at'
    return t


def field(ix, d, ctx):
    if ctx.get('_thing') and d in FIELDS:
        return "the %s byte (%+d) of the thing record at %s" % (FIELDS[d], d, ix)
    return 'byte %+d of the record at %s' % (d, ix) if d else 'the first byte of the record at %s' % ix


def operand(t, ctx, imm=False):
    t = t.strip()
    m = re.match(r'^\$([0-9A-F]+)$', t)
    if m:
        v = int(m.group(1), 16)
        if len(m.group(1)) == 2:
            return h(v)
        return h(v, 4)
    return regdesc(t, ctx)


def describe(a, ins, prev, ctx, blockdesc):
    """Return (what, newctx updates).  ctx tracks constants in HL/DE/BC."""
    i = ins.strip()
    mm = re.match(r'^([A-Z]+)\s*(.*)$', i)
    op = mm.group(1)
    args = mm.group(2)
    parts = [x.strip() for x in args.split(',')] if args else []

    def mem(t):
        m = re.match(r'^\(\$([0-9A-F]{4})\)$', t)
        return int(m.group(1), 16) if m else None

    def idx(t):
        m = re.match(r'^\((I[XY])([+-])\$([0-9A-F]{2})\)$', t)
        if not m:
            return None
        d = int(m.group(3), 16)
        return m.group(1), (-d if m.group(2) == '-' else d)

    def thingbit(r, d, bit):  # ctx comes from describe's scope
        if d in (4, 5, 6) and ctx.get('_thing'):
            n = {4: BITNAMES4, 5: BITNAMES5, 6: BITNAMES6}[d].get(bit)
            return n
        return None

    if op == 'LD':
        d, s = parts[0], parts[1]
        m = mem(s)
        if m is not None and d in ('A',) + REG16:
            ctx[d] = None
            return 'Read %s into %s' % (name(m), d)
        m = mem(d)
        if m is not None:
            return 'Store %s in %s' % (s, name(m))
        di = idx(s)
        if di:
            ctx[d] = None
            f = field(di[0], di[1], ctx)
            return 'Read %s into %s' % (f, d)
        di = idx(d)
        if di:
            f = field(di[0], di[1], ctx)
            if re.match(r'^\$', s):
                return 'Set %s to %s' % (f, operand(s, ctx))
            return 'Store %s in %s' % (s, f)
        if d in REG16 and re.match(r'^\$[0-9A-F]{4}$', s):
            v = int(s[1:], 16)
            ctx[d] = v
            if re.match(r'^ADD (HL|IX|IY|A),%s$' % d, ctx.get('_next', '')):
                sv = v - 65536 if v >= 0x8000 else v
                return 'Load %s with %s%s, the amount that is added next' % (d, h(v, 4), (' (%d as a signed offset)' % sv) if sv < 0 else '')
            if v >= 0x5D00 or v in ROM:
                return 'Point %s at %s' % (d, name(v))
            return 'Load %s with %s' % (d, h(v, 4))
        if d in ('A', 'B', 'C', 'D', 'E', 'H', 'L') and re.match(r'^\$[0-9A-F]{2}$', s):
            ctx[d] = int(s[1:], 16)
            return 'Load %s with %s' % (d, s)
        if s == '(HL)' or s == '(DE)' or s == '(BC)':
            ctx[d] = None
            hl = ctx.get('HL') if s == '(HL)' else None
            if hl is not None:
                return 'Read the byte at %s into %s' % (name(hl), d)
            return 'Read the byte %s points at into %s' % (s[1:-1], d)
        if d in ('(HL)', '(DE)', '(BC)'):
            if re.match(r'^\$', s):
                return 'Store %s at the address %s points to' % (s, d[1:-1])
            return 'Store %s at the address %s points to' % (s, d[1:-1])
        if d == 'SP':
            return 'Set the stack pointer from %s' % s
        ctx[d] = None
        if re.match(r'^[A-Z]{2}$', d):
            return 'Copy %s into %s' % (s, d)
        return 'Copy %s into %s' % (s, d)
    if op == 'PUSH':
        return 'Save %s on the stack' % args
    if op == 'POP':
        ctx[args] = None
        return 'Restore %s from the stack' % args
    if op == 'CALL':
        t = int(parts[-1][1:], 16)
        if len(parts) == 2:
            cc = parts[0]
            c = cond_phrase(prev, cc, ctx) or GENERIC[cc]
            return 'If %s, call %s' % (c, rname(t))
        ctx.clear()
        return 'Call %s' % rname(t)
    if op in ('JP', 'JR'):
        if parts[0] in ('(HL)', '(IX)', '(IY)'):
            return 'Jump to the address in %s' % parts[0][1:-1]
        t = int(parts[-1][1:], 16)
        if len(parts) == 2:
            cc = parts[0]
            c = cond_phrase(prev, cc, ctx) or GENERIC[cc]
            return 'If %s, %s' % (c, goto(a, t))
        return goto(a, t, True)
    if op == 'DJNZ':
        t = int(args[1:], 16)
        return 'Count B down and, while it is not zero, go back to %s' % label_target(t)
    if op == 'RET':
        if parts:
            cc = parts[0]
            c = cond_phrase(prev, cc, ctx) or GENERIC[cc]
            return 'If %s, return' % c
        return 'Return to the caller'
    if op == 'XOR' and args == 'A':
        ctx['A'] = 0
        return 'Clear A to zero (and the carry flag)'
    if op == 'SUB' and args == 'A':
        ctx['A'] = 0
        return 'Clear A to zero'
    if op == 'AND' and args == 'A':
        return 'Test A for zero (this leaves A as it was and clears carry)'
    if op == 'OR' and args == 'A':
        return 'Test A for zero (this leaves A as it was and clears carry)'
    if op == 'CP':
        v = operand(parts[0], ctx)
        return 'Compare A with %s' % v
    if op in ('AND', 'OR', 'XOR'):
        v = operand(parts[0], ctx)
        verb = {'AND': 'Keep only the bits of A that are set in', 'OR': 'Set in A the bits that are set in',
                'XOR': 'Flip in A the bits that are set in'}[op]
        if op == 'AND' and re.match(r'^\$[0-9A-F]{2}$', parts[0]):
            bits = [b for b in range(8) if int(parts[0][1:], 16) >> b & 1]
            if len(bits) == 1:
                return 'Isolate bit %d of A (mask %s)' % (bits[0], parts[0])
            if len(bits) == 0:
                return 'Clear A'
            return 'Keep only bits %s of A (mask %s)' % (', '.join(map(str, bits)), parts[0])
        if op == 'OR' and re.match(r'^\$[0-9A-F]{2}$', parts[0]):
            bits = [b for b in range(8) if int(parts[0][1:], 16) >> b & 1]
            if len(bits) == 1:
                return 'Set bit %d of A' % bits[0]
            return 'Set bits %s of A (mask %s)' % (', '.join(map(str, bits)), parts[0])
        return '%s %s' % (verb, v)
    if op == 'SUB':
        return 'Subtract %s from A' % operand(parts[0], ctx)
    if op == 'ADD' and parts[0] == parts[1] and parts[0] in ('A', 'HL', 'IX', 'IY'):
        ctx[parts[0]] = None
        return 'Double %s (shift it left one bit)' % parts[0]
    if op == 'ADD' and parts[0] == 'A':
        return 'Add %s to A' % operand(parts[1], ctx)
    if op == 'ADC':
        return 'Add %s and the carry to %s' % (parts[1], parts[0])
    if op == 'SBC':
        if parts[0] == 'HL':
            return 'Subtract %s and the carry from HL' % parts[1]
        return 'Subtract %s and the carry from A' % operand(parts[1], ctx)
    if op == 'ADD':
        ctx[parts[0]] = None
        return 'Add %s to %s' % (parts[1], parts[0])
    if op in ('INC', 'DEC'):
        t = args
        verb = 'Add one to' if op == 'INC' else 'Subtract one from'
        if t in REG16:
            ctx[t] = None
            if t in ('HL', 'DE', 'BC', 'IX', 'IY'):
                return ('Step %s on to the next byte' % t) if op == 'INC' else ('Step %s back one byte' % t)
        if t.startswith('(') or t in ('A', 'B', 'C', 'D', 'E', 'H', 'L'):
            ctx[t] = None
        return '%s %s' % (verb, regdesc(t, ctx) if t.startswith('(') else t)
    if op in ('BIT', 'SET', 'RES'):
        bit = int(parts[0])
        tgt = parts[1]
        di = idx(tgt)
        extra = ''
        if di:
            nm = thingbit(di[0], di[1], bit)
            if nm:
                extra = ' (%s)' % nm
        what = regdesc(tgt, ctx)
        verb = {'BIT': 'Test', 'SET': 'Set', 'RES': 'Clear'}[op]
        if tgt in ('A', 'B', 'C', 'D', 'E', 'H', 'L'):
            what = tgt
            if op != 'BIT':
                ctx[tgt] = None
        return '%s bit %d of %s%s' % (verb, bit, what, extra)
    if op == 'EX':
        if args == 'DE,HL':
            ctx['HL'], ctx['DE'] = ctx.get('DE'), ctx.get('HL')
            return 'Swap DE and HL'
        if args == '(SP),HL':
            ctx['HL'] = None
            return 'Swap HL with the word on top of the stack'
        if args == "AF,AF'":
            return 'Swap AF with the shadow copy'
    if op == 'EXX':
        ctx.clear()
        return 'Swap BC, DE and HL with their shadow copies'
    if op in ('RRCA', 'RLCA'):
        return 'Rotate A %s one place (bit %s goes to carry and bit %s)' % (
            'right' if op == 'RRCA' else 'left', '0' if op == 'RRCA' else '7', '7' if op == 'RRCA' else '0')
    if op in ('RRC', 'RLC', 'RL', 'RR', 'SLA', 'SRA', 'SRL'):
        if len(parts) == 1:
            ctx[parts[0]] = None
        d = {'RRC': 'Rotate %s right', 'RLC': 'Rotate %s left', 'RL': 'Rotate %s left through the carry',
             'RR': 'Rotate %s right through the carry', 'SLA': 'Shift %s left (double it)',
             'SRA': 'Shift %s right keeping its sign', 'SRL': 'Shift %s right (halve it)'}[op]
        return d % args
    if op == 'SCF':
        return 'Set the carry flag'
    if op == 'CCF':
        return 'Flip the carry flag'
    if op == 'CPL':
        return 'Flip every bit of A'
    if op == 'NEG':
        return 'Negate A'
    if op == 'NOP':
        return 'Do nothing (padding)'
    if op == 'DI':
        return 'Disable interrupts'
    if op == 'HALT':
        return 'Wait for the next interrupt'
    if op == 'LDIR':
        return 'Copy BC bytes from where HL points to where DE points, counting up'
    if op == 'LDDR':
        return 'Copy BC bytes from where HL points to where DE points, counting down'
    if op == 'OUT':
        return 'Write A to port %s' % parts[0]
    if op == 'IN':
        return 'Read port %s into A' % parts[1]
    if op == 'RST':
        return 'Call the ROM routine at %s' % args
    return None


def fix_tail(what, ins, nxt, pins=''):
    if what is None:
        return what
    if ins == 'AND A' and nxt.startswith('SBC HL,'):
        return 'Clear the carry flag, so that the subtraction that follows is a plain one (a compare)'
    if ins.startswith('SBC HL,') and pins == 'AND A':
        return 'Subtract %s from HL without changing HL for later: the carry flag says HL was smaller, zero says equal' % ins.split(',')[1] if False else 'Subtract %s from HL (a compare: carry = HL was smaller, zero = equal)' % ins.split(',')[1]
    m = re.match(r'^OR \$([0-9A-F]{2})$', ins)
    if m and int(m.group(1), 16) and nxt.startswith('RET'):
        return 'Make A non-zero, which clears the zero flag, and hand that back to the caller'
    if ins == 'XOR A' and nxt.startswith('RET'):
        return 'Set A to zero, which sets the zero flag for the caller'
    if ins in ('AND A', 'OR A') and nxt.startswith('RET'):
        return 'Clear the carry flag for the caller (A is unchanged)'
    if ins == 'SCF' and nxt.startswith('RET'):
        return 'Set the carry flag for the caller'
    return what


def goto(a, t, cap=False):
    d = 'go back to' if t <= a else 'skip ahead to'
    if t > a and t - a > 40:
        d = 'jump on to'
    if cap:
        d = d[0].upper() + d[1:]
    return '%s %s' % (d, label_target(t))


def label_target(t):
    b = block_of(t)
    if b and b[0] == t and b[3] == 'c':
        return 'the routine "%s" (%s)' % (short(b[1], 50), h(t, 4))
    return h(t, 4)


def main():
    out = {}
    # which rows already have their own comment
    # group state
    prev = None
    ctx = {}
    ingroup = False
    groupfirst = None
    entries = []   # (index) rows to treat
    n = len(rows)
    # find groups: a row whose comment starts with '{' up to the row whose comment ends with '}'
    gid = [None] * n
    g = None
    for i, (a, ins, cm, mark, bi) in enumerate(rows):
        if ins.startswith('DEF') or not ins:
            g = None if not ins.startswith('DEF') else g
        if cm.startswith('{') and not ins.startswith('DEF'):
            g = i
        if g is not None:
            gid[i] = g
        if g is not None and cm.endswith('}') and not ins.startswith('DEF'):
            g = None
    # group text: the comment fragments joined
    gtext = {}
    for i, (a, ins, cm, mark, bi) in enumerate(rows):
        if gid[i] is not None:
            gtext.setdefault(gid[i], []).append(cm)
    for k in list(gtext):
        t = ' '.join(gtext[k])
        t = t.lstrip('{').rstrip('}').strip()
        t = re.sub(r'\s+', ' ', t)
        gtext[k] = t
    prev = None
    ctx = {}
    for i, (a, ins, cm, mark, bi) in enumerate(rows):
        if ins.startswith('DEF') or not ins:
            prev = None
            ctx = {}
            continue
        if a in TARGETS:
            ctx = {}
        blk = block_of(a)
        bd = blk[2] if blk else ''
        ttl = (blk[1] if blk else '').lower()
        ctx['_thing'] = bool(re.search(r'\bthings?\b', ttl)) and not re.search(
            r'node|order|case|statement|verb record|evidence|sentence|parse|script|plan|actor table|word|action record|object', ttl)
        ctx['_next'] = rows[i + 1][1] if i + 1 < n else ''
        what = describe(a, ins, prev, ctx, bd)
        what = fix_tail(what, ins, rows[i + 1][1] if i + 1 < n else '', rows[i - 1][1] if i else '')
        if re.match(r'^(INC|DEC) (BC|DE|HL|SP|IX|IY)$', ins):
            pass                      # 16-bit INC/DEC leave the flags alone
        elif FLAGRE.match(ins):
            prev = ins
        elif re.match(r'^(LD|PUSH|JR|JP|RET)\b', ins) or ins in ('EX DE,HL', 'NOP'):
            pass
        else:
            prev = None
        if ins.startswith(('RET', 'JP ', 'JR ')) and ',' not in ins:
            ctx = {}
        own = gid[i] is not None or not cm
        if not own:
            continue
        if what is None:
            continue
        txt = what
        if gid[i] == i or (gid[i] is not None and rows[gid[i]][0] == a):
            g_ = gtext.get(gid[i], '')
            norm = lambda x: re.sub(r'[^a-z0-9]', '', x.lower())
            if g_ and (norm(g_)[:24] in norm(what) or norm(what)[:30] in norm(g_)):
                txt = what
            else:
                txt = '%s - %s' % (what, g_) if g_ else what
        out[a] = txt
    return out


if __name__ == '__main__':
    out = main()
    with open(OUT, 'w') as f:
        f.write('"""Generated by tools/autolines.py: a plain-English comment for each instruction."""\n')
        f.write('AUTO = {\n')
        for a in sorted(out):
            f.write('    0x%04X: %r,\n' % (a, out[a]))
        f.write('}\n')
    print(len(out), 'lines')
