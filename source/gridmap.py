"""
Grid map: every room sits on a grid cell, and a room that is north of
another is drawn above it, east of it to its right, and so on. The exit
table is not a flat plan (the garden maze and Brown's house have exits that
cannot all be drawn on one grid), so the map is laid out area by area; an
exit that cannot be drawn between neighbouring cells is drawn as an orange
dashed line with its direction written on it, and an exit to another area
or another floor is a small tag under the room.
"""
import collections
import html
import textwrap

V = {1: (0, -1, 0), 2: (0, 1, 0), 3: (1, 0, 0), 4: (-1, 0, 0), 5: (1, -1, 0), 6: (-1, -1, 0),
     7: (1, 1, 0), 8: (-1, 1, 0), 9: (0, 0, 1), 10: (0, 0, -1)}
SH = {1: 'N', 2: 'S', 3: 'E', 4: 'W', 5: 'NE', 6: 'NW', 7: 'SE', 8: 'SW', 9: 'U', 10: 'D'}
AREAS = [
    ('Leatherhead: streets, station and platforms', [50, 51, 52, 62, 92, 104, 53, 54, 55]),
    ("Basil's house", list(range(56, 62))),
    ("Brown's house", list(range(63, 76))),
    ('Garden and maze', list(range(76, 92))),
    ("Jones's house", list(range(93, 102))),
]
TITLES = {5: "Baker Street and the lodgings", 10: 'Parliament Street and Scotland Yard',
          12: 'Slater Street and the opium den', 14: 'Aldergate Street, station and platforms',
          18: "King's Cross Road, station and platforms", 24: "Bishop's Road, Paddington station and platforms",
          28: 'Buckingham Palace Road, Victoria station and platforms',
          32: "Camden Street and Basil's London house", 40: 'Sidmouth Street',
          45: "Portman Street and Tricia's house"}
W, H, GX, GY = 150, 54, 46, 54


def layout(ids, edges):
    ids = set(ids)
    adj = collections.defaultdict(list)
    for a, d, b in edges:
        if a in ids and b in ids:
            v = V[d]
            adj[a].append((b, v))
            adj[b].append((a, tuple(-x for x in v)))
    pos, used, flagged = {}, set(), 0
    for root in sorted(ids):
        if root in pos:
            continue
        # start each further component on a free spot to the right
        ox = max([p[0] for p in pos.values()] + [-2]) + 2 if pos else 0
        pos[root] = (ox, 0, 0)
        used.add(pos[root])
        q = [root]
        while q:
            a = q.pop(0)
            for b, v in sorted(adj[a]):
                if b in pos:
                    continue
                p = tuple(x + y for x, y in zip(pos[a], v))
                if p in used:  # collision: nearest free cell on the same floor
                    best = None
                    for r in range(1, 8):
                        for dx in range(-r, r + 1):
                            for dy in range(-r, r + 1):
                                c = (p[0] + dx, p[1] + dy, p[2])
                                if c not in used and (best is None or abs(dx) + abs(dy) < best[0]):
                                    best = (abs(dx) + abs(dy), c)
                        if best:
                            break
                    p = best[1]
                    flagged += 1
                pos[b] = p
                used.add(p)
                q.append(b)
    return pos


def build(rooms, names, checked, short_edges=None):
    """rooms: {id: room dict with exits}. names: {id: str}. checked: exits_checked list."""
    ok = {(x['room'], x['dest']): x['ok'] for x in checked if x['dest']}
    edges = [(r, d, dest) for r, rm in rooms.items() for d, door, dest in rm['exits'] if dest]
    area_of = {}
    groups = []
    for title, ids in AREAS:
        groups.append([title, list(ids)])
        for i in ids:
            area_of[i] = len(groups) - 1
    # remaining rooms: connected components over leftover rooms
    left = [r for r in rooms if r not in area_of and any(a == r or b == r for a, d, b in edges)]
    seen = set()
    nadj = collections.defaultdict(set)
    for a, d, b in edges:
        nadj[a].add(b)
        nadj[b].add(a)
    n = 0
    for r in sorted(left):
        if r in seen:
            continue
        comp, q = [], [r]
        seen.add(r)
        while q:
            a = q.pop()
            comp.append(a)
            for b in nadj[a]:
                if b not in seen and b not in area_of:
                    seen.add(b)
                    q.append(b)
        n += 1
        lo = min(comp)
        groups.append([TITLES.get(lo, f'Around room {lo}, {names[lo]}'), sorted(comp)])
        for i in comp:
            area_of[i] = len(groups) - 1
    loose = [r for r in rooms if r not in area_of]
    if loose:
        groups.append(['Rooms with no walking exits: off stage, the cab, the trains, the police cab, Old Mill Road', loose])
        for i in loose:
            area_of[i] = len(groups) - 1

    out, y0 = [], 10
    maxw = 0
    stats = {'drawn': 0, 'odd': 0}
    for gi, (title, ids) in enumerate(groups):
        if gi == len(groups) - 1 and loose and ids == loose:
            pos = {r: (i % 8, i // 8, 0) for i, r in enumerate(ids)}
        else:
            pos = layout(ids, edges)
        floors = sorted({p[2] for p in pos.values()})
        for z in floors:
            rs = [r for r in ids if pos[r][2] == z]
            xs = [pos[r][0] for r in rs]
            ys = [pos[r][1] for r in rs]
            mx, my = min(xs), min(ys)
            cx = lambda r: 10 + (pos[r][0] - mx) * (W + GX) + W / 2
            cy = lambda r: y0 + 34 + (pos[r][1] - my) * (H + GY) + H / 2
            label = title + ('' if len(floors) == 1 else f' - floor {z - floors[0] + 1} of {len(floors)}')
            out.append(f'<text x="10" y="{y0 + 14}" font-size="14" font-weight="bold" fill="#4a3d26">{html.escape(label)}</text>')
            pw = 20 + (max(xs) - mx + 1) * (W + GX) - GX
            maxw = max(maxw, pw)
            here = set(rs)
            drawn = set()
            body = []
            for a, d, b in edges:
                if a not in here or b not in here:
                    continue
                key = tuple(sorted((a, b)))
                both = any(aa == b and bb == a for aa, dd, bb in edges)
                if key in drawn:
                    continue
                drawn.add(key)
                fits = (pos[b][0] - pos[a][0], pos[b][1] - pos[a][1]) == V[d][:2]
                if both:
                    d2 = next(dd for aa, dd, bb in edges if aa == b and bb == a)
                    fits = fits and (pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]) == V[d2][:2]
                blocked = not ok.get((a, b), True) or not ok.get((b, a), True)
                x1, y1, x2, y2 = cx(a), cy(a), cx(b), cy(b)
                dx, dy = x2 - x1, y2 - y1
                t1 = min((W / 2) / abs(dx) if dx else 1e9, (H / 2) / abs(dy) if dy else 1e9)
                sx, sy, ex, ey = x1 + dx * t1, y1 + dy * t1, x2 - dx * t1, y2 - dy * t1
                col = '#b03030' if blocked else ('#7a6a4f' if fits else '#d9822b')
                dash = ' stroke-dasharray="5 3"' if (blocked or not fits) else ''
                mk = ' marker-end="url(#ah)"' + (' marker-start="url(#ahs)"' if both else '')
                body.append(f'<line x1="{sx:.0f}" y1="{sy:.0f}" x2="{ex:.0f}" y2="{ey:.0f}" stroke="{col}" stroke-width="1.5"{dash}{mk}/>')
                stats['drawn'] += 1
                if not fits:
                    stats['odd'] += 1
                    lab = SH[d] + (('/' + SH[d2]) if both else '')
                    body.append(f'<text x="{(sx + ex) / 2:.0f}" y="{(sy + ey) / 2 - 3:.0f}" font-size="9" fill="#a85d12" text-anchor="middle" '
                                f'style="paint-order:stroke" stroke="#fff" stroke-width="3">{lab}</text>')
            out.extend(body)
            for r in rs:
                nm = textwrap.wrap('(off stage)' if r == 0 else names[r], 22)[:2]
                x, y = cx(r) - W / 2, cy(r) - H / 2
                out.append(f'<a href="#room{r}"><rect x="{x:.0f}" y="{y:.0f}" width="{W}" height="{H}" rx="8" fill="#f4efe1" stroke="#7a6a4f"/>'
                           f'<text x="{x + 6:.0f}" y="{y + 14:.0f}" font-size="10" font-weight="bold" fill="#4a3d26">{r}</text>'
                           + ''.join(f'<text x="{x + 6:.0f}" y="{y + 28 + 11 * i:.0f}" font-size="10" fill="#222">{html.escape(t)}</text>'
                                     for i, t in enumerate(nm)) + '</a>')
                tags = []
                for dd, door, dest in rooms[r]['exits']:
                    if dest and dest not in here:
                        tags.append(f'{SH[dd]}&#8594;{dest}' + ('!' if not ok.get((r, dest), True) else ''))
                if tags:
                    anyblk = any(t.endswith('!') for t in tags)
                    tags = [t.rstrip('!') for t in tags]
                    out.append(f'<text x="{x + 2:.0f}" y="{y + H + 11:.0f}" font-size="9" fill="#5a4a8a">{" ".join(tags)}</text>')
                    if anyblk:
                        out.append(f'<text x="{x + W - 2:.0f}" y="{y + H + 11:.0f}" font-size="9" fill="#b03030" text-anchor="end">blocked: too narrow</text>')
            ph = 34 + (max(ys) - my + 1) * (H + GY) - GY + 14
            y0 += ph + 26
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {maxw + 20:.0f} {y0}" width="{maxw + 20:.0f}" '
           'font-family="Helvetica,Arial,sans-serif">'
           '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">'
           '<path d="M0 0L10 5L0 10z" fill="context-stroke"/></marker>'
           '<marker id="ahs" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
           '<path d="M0 0L10 5L0 10z" fill="context-stroke"/></marker></defs>'
           + ''.join(out) + '</svg>')
    return svg, stats
