"""Site presentation for the SkoolKit build: themes for the Trivia entries, the page
templates (layout bar, landing page), the grouped index and the 'Trivia by theme' page.
build.py calls reorder_facts() and extra_ref_sections()."""
import html

# ---- trivia themes: (title, blurb, [fact ids in reading order]) -----------------------
THEMES = [
 ('winning', 'Winning the game',
  'The route that wins, why each step is where it is, and the timings that make or break it.',
  ['the-last-scene', 'the-win-typed', 'second-winning-route', 'replay-is-deterministic', 'tuesday-ordering',
   'burning-note-typed', 'followers-lag-one-turn', 'train-goes-on-to-platform-two', 'police-cab-seats',
   'ordering-the-cab-strands-lestrade', 'phipps-shoots-the-bedroom', 'window-exit-bedroom',
   'messenger-note-watched', 'train-circle-timings', 'lestrade-orders-tried', 'lestrade-cab-clash',
   'cab-change-and-fares', 'cab-fares', 'stale-quotes-cabbie', 'pay-not-give-money']),
 ('case', 'The case, the evidence and the endings',
  'What the game counts as proof, what ends it early, and how it can end.',
  ['three-endings', 'meet-lestrade-by-3pm', 'the-case-table', 'watson-remembers', 'watson-connections',
   'catch-the-major', 'tricia-is-mrs-jones', 'blackmail-statement', 'early-sale-statement-unneeded',
   'wall-safe-trap', 'large-rock-tuesday', 'large-rock-needs-lestrade', 'disguise-needs-a-trick',
   'basils-london-house', 'the-game-goes-on', 'bedtime', 'bring-a-lamp']),
 ('world', 'The world: people, places and things',
  'The cast, the map, and the odd ways the world is built.',
  ['cast-list', 'map-decoded-and-walked', 'police-men-are-doors', 'lestrade-hails-a-cab', 'plan-scripts',
   'waiting-for-the-hour', 'busy-characters', 'thirteen-pictures', 'scenery-words', 'examine-closely',
   'follow-climbs-in', 'go-furiously']),
 ('parser', 'The parser and the keyboard',
  'How typed commands are understood, and what the words really mean.',
  ['verb-system-decoded', 'dictionary-front-coded', 'synonyms', 'abbreviations', 'object-flag-words',
   'quit-means-load', 'pounds-shillings-pence', 'cursor-keys', 'repeat-key']),
 ('engine', 'Engine internals',
  'How the program itself works: actor table, scripts, dispatch and printing.',
  ['boot-actor-table', 'actor-table-record-size', 'action-dispatcher-found', 'verb-table-found',
   'object-id-catalog', 'dispatch-mechanisms-unified', 'aa71-purpose-confirmed', 'aa71-action-library-expanded',
   'print-char-verified', 'messages-rendered', 'unused-hang-opcode', 'saved-game-on-the-tape']),
 ('corrections', 'Corrections along the way',
  'Findings that were revised or withdrawn while the work went on. Kept so the record is honest.',
  ['always-checked-table-found', 'verb-number-hypothesis-double-checked', 'npc-turn-processing-confirmed',
   'room-text-path-resolved', 'b91f-is-setup-only', 'dictionary-matching-confirmed',
   'dictionary-to-verb-number-corrected', 'get-actor-room-confirmed']),
]
ORDER = [i for _, _, _, ids in THEMES for i in ids]


def slug(s):
    import re
    return re.sub(r'[^a-zA-Z0-9]+', '_', s).strip('_')


def reorder_facts(facts):
    """Facts in theme order. Every fact must be in exactly one theme."""
    ids = [f[0] for f in facts]
    missing = [i for i in ids if i not in ORDER]
    extra = [i for i in ORDER if i not in ids]
    dup = {i for i in ORDER if ORDER.count(i) > 1}
    assert not missing and not extra and not dup, (missing, extra, dup)
    pos = {i: n for n, i in enumerate(ORDER)}
    return sorted(facts, key=lambda f: pos[f[0]])


def gist(body, n=150):
    import re
    t = re.sub(r'<[^>]+>|`', '', body)
    t = re.sub(r'\s+', ' ', t).strip()
    m = re.match(r'(.+?[.!?])(\s|$)', t)
    g = m.group(1) if m else t
    if len(g) > n: g = g[:n].rsplit(' ', 1)[0] + '...'
    return g


def themes_page(facts):
    """HTML for the 'Trivia by theme' page: links into reference/facts.html anchors."""
    by_id = {f[0]: f for f in facts}
    out = ['<p>All %d trivia entries, grouped by what they are about. Each link goes to the full entry on the '
           '<a href="reference/facts.html">Trivia</a> page, which lists them in this same order.</p>' % len(facts)]
    out.append('<ul>' + ''.join('<li><a href="#%s">%s</a></li>' % (k, html.escape(t)) for k, t, _, _ in THEMES) + '</ul>')
    for key, title, blurb, ids in THEMES:
        out.append('<h2 id="%s">%s</h2><p>%s</p><ul>' % (key, html.escape(title), html.escape(blurb)))
        for i in ids:
            f = by_id[i]
            out.append('<li><a href="reference/facts.html#%s">%s</a><small>%s</small></li>' % (slug(i), html.escape(f[1]), html.escape(gist(f[2]))))
        out.append('</ul>')
    return '\n'.join(out)


# ---- page grouping ---------------------------------------------------------------
GROUPS = [
 ('PlayGroup', 'Playing the game', ['the-walkthrough', 'the-endings-played', 'the-case', 'map', 'things', 'cast', 'vocabulary', 'pictures']),
 ('HowGroup', 'How it works', ['how-it-works', 'state-bits', 'trains-cabs', 'rom_symbols', 'loader-notes', 'dictionary-notes', 'world-model-notes', 'harness-notes']),
 ('HistGroup', 'Earlier write-ups (superseded by the walkthrough)', ['the-endgame', 'the-playthrough', 'the-playthrough-2']),
]
NICE_TITLES = {
    'loader-notes': 'Loader notes: the tape and how the game starts',
    'harness-notes': 'Harness notes: the emulator test rig',
    'dictionary-notes': 'Dictionary notes',
    'world-model-notes': 'World-model notes: actors and scripts',
    'the-walkthrough': 'Walkthrough: Monday to the win',
    'the-endings-played': 'Every ending, played',
    'the-endgame': 'The endgame, as first played',
    'the-playthrough': 'First walkthrough, part 1 (superseded)',
    'the-playthrough-2': 'First walkthrough, part 2 (superseded)',
    'trivia-by-theme': 'Trivia by theme',
}

NAV_JS = """<script>
(function(){var b=document.querySelector('header.site a.brand');if(!b)return;
var base=b.getAttribute('href').replace(/index\\.html$/,'');
var L=[['Start','index.html'],['Walkthrough','the-walkthrough.html'],['Endings','the-endings-played.html'],
['Bugs','reference/bugs.html'],['Trivia','trivia-by-theme.html'],['Map','map.html'],['Routines','maps/routines.html'],['Messages','maps/messages.html']];
var n=document.querySelector('header.site nav');var here=location.pathname.split('/').pop();
L.forEach(function(x){var a=document.createElement('a');a.href=base+x[1];a.textContent=x[0];
if(x[1].split('/').pop()===here)a.setAttribute('aria-current','page');n.appendChild(a);});})();
</script>"""

NAV_JS_ESC = NAV_JS.replace("{", "{{").replace("}", "}}")
LAYOUT = """<!DOCTYPE html>
<html lang="en">
<head>
<title>{SkoolKit[title]} - {Game[Game]}</title>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<# foreach($css,SkoolKit[stylesheets]) #>
<link rel="stylesheet" type="text/css" href="{$css[href]}" />
<# endfor #>
<# foreach($js,SkoolKit[javascripts]) #>
<script type="text/javascript" src="{$js[src]}"></script>
<# endfor #>
</head>
<body class="{SkoolKit[page_id]}">
<header class="site"><div class="bar"><a class="brand" href="{SkoolKit[index_href]}">{Game[Logo]}</a><nav aria-label="Site"></nav></div></header>
<main>
<# if(SkoolKit[page_id]!='GameIndex') #>
<h1 class="page-title">{SkoolKit[page_header][1]}</h1>
<# endif #>
<# include({SkoolKit[include]}) #>
</main>
<# include(footer) #>
""" + NAV_JS_ESC + """
</body>
</html>
"""

HOME = """
<div class="hero">
<h1 class="page-title">Sherlock, taken apart</h1>
<p class="lede">An annotated disassembly of <em>Sherlock</em> (Melbourne House, 1984) for the ZX Spectrum:
every routine and data block titled and explained, checked by playing the game in an emulator. The game has been
won by typed commands alone, in two different ways.</p>
<ul class="stats">
<li><b>@BLOCKS@</b><span>blocks titled and described</span></li>
<li><b>@COMMENTS@</b><span>line comments</span></li>
<li><b>@FACTS@</b><span>trivia entries</span></li>
<li><b>@BUGS@</b><span>bugs, each played</span></li>
<li><b>7</b><span>different endings, all reached</span></li>
</ul>
</div>
<div class="cards">
<a class="card" href="the-walkthrough.html"><strong>Win the game</strong><span>The full route, Monday to the final scene at Victoria, with every time.</span></a>
<a class="card" href="the-endings-played.html"><strong>Every ending</strong><span>The seven endings, one win and six ways to lose, and what you type to get each.</span></a>
<a class="card" href="how-it-works.html"><strong>How the engine works</strong><span>Actors, scripts, the parser and the clock, in plain words.</span></a>
<a class="card" href="reference/bugs.html"><strong>Bugs</strong><span>@BUGS@ faults in the original, each reproduced.</span></a>
<a class="card" href="trivia-by-theme.html"><strong>Trivia by theme</strong><span>@FACTS@ findings, grouped: winning, the case, the world, the parser, the engine.</span></a>
<a class="card" href="maps/routines.html"><strong>Browse the code</strong><span>Every routine, with its purpose, inputs and outputs, and a comment on each instruction.</span></a>
</div>
<div class="honest"><b>What is and is not checked.</b> The behaviour described was observed by typing commands into an emulator, and
the winning routes replay exactly. Many routine descriptions, though, were read from the code and not individually
run; those say so. Action records and a few routines also give how often each ran in the stored routes and which instructions never did. The project README lists the gaps.</div>
<# foreach($section,sections) #>
<div class="section-header">{$section[header]}</div>
<ul class="index-list">
<# foreach($item,$section[items]) #>
<li><a href="{$item[href]}">{$item[link_text]}</a>{$item[other_text]}</li>
<# endfor #>
</ul>
<# endfor #>
"""


def extra_ref_sections(index_page_ids, facts):
    """(ref_lines_to_append, page triples) for the template/css/themes/index parts."""
    lines = []
    lines.append('[Template:Layout]')
    lines.append(LAYOUT.strip('\n'))
    lines.append('')
    import build_skeleton as _b
    blocks = len(_b.A)
    comments = sum(len(r['comments']) for r in _b.A.values())
    home = (HOME.strip('\n').replace('@BLOCKS@', str(blocks)).replace('@COMMENTS@', '{:,}'.format(comments))
            .replace('@FACTS@', str(len(facts))).replace('@BUGS@', str(len(_b.BUGS))))
    lines.append('[Template:home]')
    lines.append(home)
    lines.append('')
    return lines


def index_lines(index_page_ids):
    present = set(index_page_ids)
    lines = ['[Index]', 'Reference']
    for key, _, ids in GROUPS:
        lines.append(key)
    lines += ['MemoryMaps', 'Graphics', 'DataTables', 'OtherCode', '']
    lines.append('[Index:Reference:Reference]')
    lines += ['Facts', 'Bugs', 'trivia-by-theme', '']
    for key, title, ids in GROUPS:
        lines.append('[Index:%s:%s]' % (key, title))
        lines += [i for i in ids if i in present]
        lines.append('')
    return lines
