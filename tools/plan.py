"""Decode a plan script (the per-actor behaviour language run by $CC78).

    python3 tools/plan.py ADDR [ADDR...]     (hex)

Follows control flow from each start address (next instruction, success
and failure branches, GOTO targets) and prints every reachable
instruction in address order. Also importable: decode(addr) returns one
instruction as a dict, walk(starts) returns {addr: instr}.

Instruction format, read from the interpreter at $CC82-$CF7F:
  byte 0 low nibble = opcode, high nibble = flags
    bit 7: a success address follows the operands
    bit 4: a failure address follows (after the success address, if any)
    bit 5: one-shot - on success the whole instruction is overwritten
           with zeros, and zero bytes are skipped by the interpreter
           (supported by $CF43, but no script in the game uses it)
    bit 6: busy - the character refuses the player's requests while on
           it ($B934/$CBA7: "SORRY, I CANNOT DO THAT NOW.")
  operands by opcode (lengths from $CF03):
    0  (zero byte: skipped; what a spent one-shot instruction becomes)
    1  DO verb                          2 bytes
    2  DO verb dobj iobj                4 bytes
    3  RUN record                       3 bytes   (no objects)
    4  ASK person verb dobj iobj        5 bytes   (an order to another actor)
    5  SAY person message               4 bytes
    6  PRINT message                    3 bytes
    7  RUN record dobj iobj             5 bytes
    8  SIGNAL actor                     2 bytes
    9  AWAIT actor                      2 bytes
    A  RETURN FAIL                      1 byte
    B  RETURN OK                        1 byte
    C  (hangs: JR Z,$CD08 jumps to itself) 5 bytes by $CF03
    D  PASS (one minute)                2 bytes
    E  GOTO addr                        3 bytes
    F  PASS (one minute)                1 byte
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'source'))
D = open(os.path.join(ROOT, 'p.bin'), 'rb').read()


def b(a):
    return D[a - 0x5D80]


def w(a):
    return b(a) | b(a + 1) << 8


LEN = {0x0: 1, 0x1: 2, 0x2: 4, 0x3: 3, 0x4: 5, 0x5: 4, 0x6: 3, 0x7: 5,
       0x8: 2, 0x9: 2, 0xA: 1, 0xB: 1, 0xC: 5, 0xD: 2, 0xE: 3, 0xF: 1}
NAME = {0x1: 'DO', 0x2: 'DO', 0x3: 'RUN', 0x4: 'ASK', 0x5: 'SAY',
        0x6: 'PRINT', 0x7: 'RUN', 0x8: 'SIGNAL', 0x9: 'AWAIT',
        0xA: 'RETURN FAIL', 0xB: 'RETURN OK', 0xC: 'HANG', 0xD: 'PASS',
        0xE: 'GOTO', 0xF: 'PASS'}

_names = None


def names():
    global _names
    if _names is None:
        import overlay_04_actions as o4
        from objects import entities, display_name
        _names = (o4.VERBS, {e['id']: display_name(e) for e in entities()})
    return _names


SPECIAL = {0xFA: 'its remembered thing ($9FD6)', 0xFB: 'itself',
           0xFC: 'the plan\'s indirect object', 0xFD: 'the plan\'s direct object',
           0xFE: '(number)', 0xFF: '(none)'}


def obj(n):
    if n in SPECIAL:
        return SPECIAL[n]
    if 0xF5 <= n <= 0xF9:
        return f'the plan\'s direct object (${n:02X})'
    return names()[1].get(n, f'object {n}')


def verb(n):
    if n >= 0xF5:
        return obj(n)
    return names()[0].get(n, f'verb {n}')


def decode(a):
    op = b(a)
    code = op & 0x0F
    n = LEN[code]
    r = dict(addr=a, op=op, code=code, len=n, ok=None, fail=None,
             oneshot=bool(op & 0x20), raw=[b(a + i) for i in range(n)])
    p = a + n
    if code and op & 0x80:
        r['ok'] = w(p)
        p += 2
    if code and op & 0x10:
        r['fail'] = w(p)
        p += 2
    r['next'] = p
    r['size'] = p - a
    x = r['raw']
    if code == 0:
        t = '(spent)'
    elif code == 1:
        t = f'DO {verb(x[1])}'
    elif code == 2:
        t = f'DO {verb(x[1])} / {obj(x[2])} / {obj(x[3])}'
    elif code == 3:
        t = f'RUN ${x[1] | x[2] << 8:04X}'
        r['target'] = x[1] | x[2] << 8
    elif code == 4:
        t = f'ASK {obj(x[1])} TO {verb(x[2])} / {obj(x[3])} / {obj(x[4])}'
    elif code == 5:
        t = f'SAY TO {obj(x[1])} ${x[2] | x[3] << 8:04X}'
        r['msg'] = x[2] | x[3] << 8
    elif code == 6:
        t = f'PRINT ${x[1] | x[2] << 8:04X}'
        r['msg'] = x[1] | x[2] << 8
    elif code == 7:
        t = f'RUN ${x[1] | x[2] << 8:04X} / {obj(x[3])} / {obj(x[4])}'
        r['target'] = x[1] | x[2] << 8
    elif code in (8, 9):
        t = f'{NAME[code]} {obj(x[1])}'
    elif code == 0xD:
        t = f'PASS (${x[1]:02X})'
    elif code == 0xE:
        t = f'GOTO ${x[1] | x[2] << 8:04X}'
        r['goto'] = x[1] | x[2] << 8
    else:
        t = NAME[code]
    flags = []
    if r['oneshot']:
        flags.append('once')
    if r['ok'] is not None:
        flags.append(f'ok->${r["ok"]:04X}')
    if r['fail'] is not None:
        flags.append(f'fail->${r["fail"]:04X}')
    if op & 0x40:
        flags.append('busy')
    r['text'] = t + (f'  [{", ".join(flags)}]' if flags else '')
    return r


# Records that never return to the script: they end the game (both reach
# the game-over sequence at $9E74), so whatever follows a RUN of one is
# not part of the script.
NORETURN = {0xDFCA, 0x9E48}


def walk(starts, follow_calls=False):
    seen = {}
    todo = list(starts)
    while todo:
        a = todo.pop()
        if a in seen:
            continue
        r = decode(a)
        seen[a] = r
        succ = []
        if r['code'] == 0xE:
            succ.append(r['goto'])
        elif r['code'] in (0xA, 0xB, 0xC) or r.get('target') in NORETURN:
            pass
        else:
            succ.append(r['ok'] if r['ok'] is not None else r['next'])
            succ.append(r['fail'] if r['fail'] is not None else r['next'])
        todo.extend(s for s in succ if s not in seen)
    return seen


if __name__ == '__main__':
    for s in sys.argv[1:]:
        start = int(s, 16)
        print(f'--- script at ${start:04X}')
        for a, r in sorted(walk([start]).items()):
            hexb = ' '.join(f'{b(a + i):02X}' for i in range(r['size']))
            print(f'${a:04X}  {hexb:<26} {r["text"]}')
