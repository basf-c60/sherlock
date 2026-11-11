"""Turn every $XXXX address in descriptions and comments into a link.

Addresses of the program become #R macros (to the routine, message or data byte; an address in
the middle of an instruction links to the line it belongs to). Addresses of the ROM and system
variables link to the 'rom_symbols' page. Numbers that are not addresses are left alone."""
import re, os, bisect

ROMLINKS = {0x04C2, 0x0556, 0x22AA, 0x0F12, 0x5C3C, 0x5C3A, 0x5C3B, 0x5C08, 0x5C0B, 0x5C42,
            0x5B00, 0x5B81, 0x4000, 0x5800}

_starts = []
_pat = re.compile(r'(?<![#\w$])\$([0-9A-F]{4})\b')


def _load():
    global _starts
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'game.skool')
    if not os.path.exists(p):
        return
    s = set()
    for l in open(p):
        m = re.match(r'^[ *a-z]\$([0-9A-F]{4}) ', l)
        if m:
            s.add(int(m.group(1), 16))
    _starts = sorted(s)


_load()


def _repl(m, own, anchor=True):
    a = int(m.group(1), 16)
    t = m.group(0)
    if a in ROMLINKS:
        return '#LINK(rom_symbols#a%04X)(%s)' % (a, t)
    if a < 0x5D80 or not _starts or a == own:
        return t
    j = bisect.bisect_right(_starts, a) - 1
    if j < 0:
        return t
    st = _starts[j]
    if st == a:
        return '#R$%04X' % a
    if a - st < 32:
        return '#R$%04X(%s)' % (st, t)
    return t


_verb = re.compile(r'\b([Vv]erbs?) (\d+(?:(?:, | and | or )\d+)*)(?![\d+-]| first)')


def _verb_link(m, police):
    import sys
    ov = sys.modules.get('overlay_08_plans')
    if ov is None or not hasattr(ov, 'VERB_REC'):
        return m.group(0)

    def one(n):
        n = int(n.group(0))
        a = (ov.POLICE_REC if police and n in ov.POLICE_REC else ov.VERB_REC).get(n)
        return '#R$%04X(%d)' % (a, n) if a else str(n)
    return m.group(1) + ' ' + re.sub(r'\d+', one, m.group(2))


_macro = re.compile(r'(#R\$[0-9A-F]{4}(?:\([^)]*\))?|#LINK\([^)]*\)\([^)]*\))')


def link_text(text, own=None, anchor=True):
    # leave macros that are already there exactly as they are
    parts = _macro.split(text)
    police = bool(re.search(r'police|constable', text, re.I))
    for i in range(0, len(parts), 2):
        parts[i] = _pat.sub(lambda m: _repl(m, own, anchor), parts[i])
        parts[i] = _verb.sub(lambda m: _verb_link(m, police), parts[i])
    return ''.join(parts)


def link_ctl(lines):
    out = []
    seen_title = set()
    for l in lines:
        h = re.match(r'^([a-z]) (\d+) (.*)$', l)
        if h:
            out.append(l)
            adr = list(dict.fromkeys(_pat.findall(h.group(3))))
            lk = [link_text('$' + x, int(h.group(2))) for x in adr]
            lk = [x for x in lk if x.startswith('#')]
            for vm in _verb.finditer(h.group(3)):
                t = _verb_link(vm, False)
                for a, n in re.findall(r'#R\$([0-9A-F]{4})\((\d+)\)', t):
                    if int(a, 16) != int(h.group(2)):
                        lk.append('verb %s: #R$%s' % (n, a))
            if lk:
                out.append('D %s Addresses named in the title: %s.' % (h.group(2), ', '.join(lk)))
            continue
        m = re.match(r'^([DNRCBTWSUM]) (\d+)(,[\d,]*)?( .*)$', l)
        if not m:
            out.append(l)
            continue
        k, a = m.group(1), int(m.group(2))
        body = m.group(4)
        if k == 'R':
            pass        # register notes are laid out in columns and cannot hold macros safely
        else:
            body = link_text(body)
        out.append('%s %s%s%s' % (k, m.group(2), m.group(3) or '', body))
    return out


def link_ref(lines):
    out = []
    skip = False
    for l in lines:
        if l.startswith('['):
            sec = l.split(':')[0].strip('[]')
            skip = sec in ('Game', 'Titles', 'PageHeaders', 'Links', 'Index', 'IndexGroup', 'Paths', 'Colours')
            out.append(l)
            continue
        if skip or 'id="a' in l or re.match(r'^[A-Za-z]+=', l) and not l.startswith('PageContent'):
            out.append(l)
            continue
        out.append(link_text(l))
    return out
