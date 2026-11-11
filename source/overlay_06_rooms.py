"""
Overlay 06: the rooms and the map.

Everything here is decoded from the room table by rooms.py and then
checked by playing: tools/walkall.py puts the player in every room, opens
the door in the way, types each of the 206 decoded exits and reads back
where the player ended up (results in exits_checked.json). Room
descriptions are rendered by the game's own message interpreter
(room_descriptions.json, from render_messages.Renderer).

Also generates the map (a grid drawn by gridmap.py, map.svg) and the reference pages for
rooms, things and vocabulary.
"""

import html
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_skeleton import A, blk, fact, bug, page, note, RESOURCES  # noqa: E402,F401
import rooms as R          # noqa: E402
import objects as O        # noqa: E402
import dictionary as D     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
from plan import w as _w  # noqa: E402
RM = R.rooms()
ENT = {e['id']: e for e in O.entities()}
CHECKED = json.load(open(os.path.join(HERE, 'exits_checked.json')))
DESCS = {int(k): v for k, v in json.load(open(os.path.join(HERE, 'room_descriptions.json'))).items()}
LONG = {1: 'north', 2: 'south', 3: 'east', 4: 'west', 5: 'northeast', 6: 'northwest',
        7: 'southeast', 8: 'southwest', 9: 'up', 10: 'down'}
PLAYER_SIZE = ENT[0]['size']


def rname(r):
    return R.room_name(RM[r])


def thing(i):
    return O.display_name(ENT[i]) if i in ENT else f'thing {i}'


# ---------------------------------------------------------------- table
blk(0x840B, 'w', 'Room table: room number -> room record',
    ["One address per room, 0-105, read by $D224 (room number in A, "
     "record address out in IX). Entry 106 points at $8B6F, the end of "
     "the room records (and the start of the entity index), and is not "
     "a room. Room 0 is never described or entered: it is where things "
     "that are not yet (or no longer) in play are kept - the China man "
     "starts there, as do the case, 'what happened' and the other "
     "abstract topics you can TELL people about.",
     "Trivia: $840B is also the load address of the separate 'SHD V2.0' "
     "block on the tape (see loader_notes)."],
    subs=[('W', 0x840B + 2 * r, 2, f'Room {r}: {rname(r)}' if r in RM else
           'End marker: the end of the room records ($8B6F)')
          for r in range(len(RM) + 1)])


def room_subs():
    subs = []
    for r, room in RM.items():
        a = room['address']
        names = ', '.join(room['names']) or 'no name'
        desc = (f'description at ${room["description"]:04X}' if room['description']
                else 'no description of its own')
        subs.append(('B', a, 9, f'Room {r} ({rname(r)}): flags ${room["flags"]:02X}, '
                     f'name words ({names}), {desc}'))
        ex = '; '.join(f'{LONG[d]} to {dest}' + (f' past {thing(door)}' if door else '')
                       for d, door, dest in room['exits']) or 'no exits'
        subs.append(('B', a + 9, room['end'] - a - 9, f'Room {r} exits: {ex}'))
    return subs


blk(0x84E1, 'b', 'Room records (rooms 0-105)',
    ["Layout (see rooms.py, which decodes it the way the code reads it): "
     "byte 0 flags; +1..+6 up to three word slots naming the room - noun "
     "first, its top nibble the article (1 'a', 2 'an', 8 none); +7/+8 "
     "the room's own description message (0 = none); then exits, 3 bytes "
     "each - direction (the verb number 1-10), the thing in the way (0 "
     "= nothing) and the destination room - ended by $FF.",
     "The thing in the way is what the room description names: \"To the "
     "east there is a deep stream\" comes from an exit whose 'door' is "
     "the stream. An exit with destination 0 is only ever scenery: "
     "the exit finder $D448 skips it, so it is described but never "
     "offered as a visible exit and can't be taken.",
     "Confirmed by play: all 206 exits were tried (tools/walkall.py); "
     "194 move the player to the decoded destination, and the other 12 "
     "are exactly the ones the code says must refuse - 7 scenery exits "
     "with destination 0, and 5 through a passage narrower than the "
     "player (see the move pre-check at $DCD2)."],
    subs=room_subs())
A[0x84E1]['end'] = 0x8B6F

# ---------------------------------------------------------------- code
blk(0xD224, 'c', 'Find a room record',
    ["Looks the room number up in the table at $840B."],
    regs=['Input:A Room number', 'Output:IX Address of its record'],
    comments={0xD225: '', 0xD228: '', 0xD229: 'HL = room * 2', 0xD22C: '',
              0xD22D: '...+ the table', 0xD22E: 'Read the record address',
              0xD231: '...into IX', 0xD234: '', 0xD236: ''})

blk(0xD206, 'c', 'Step to the next 3-byte entry',
    ["Moves IX on 3 bytes (one exit) and tests for the $FF that ends a "
     "list. Also loads IY with the entry's bytes 1-2, which the exit "
     "walkers ignore."],
    regs=['Input:IX An entry', 'Output:IX The next entry', 'F Z set at the end ($FF)'],
    comments={0xD20A: 'Next entry', 0xD215: 'End of the list?'})

blk(0xD33C, 'c', "IX = record of the actor's room",
    ["The actor's record is at $A017; its location byte (+$0F) is the "
     "room, looked up by $D224."],
    regs=['Output:IX Room record'],
    comments={0xD33D: 'The current actor', 0xD341: 'Its room', 0xD344: ''})

blk(0xD448, 'c', "Find the actor's exit in a direction",
    ["Walks the exits of the actor's room, skipping any whose destination "
     "is 0 (scenery exits - described, never usable). Used by the move "
     "pre-check $DCD2 with the verb number as the direction."],
    regs=['Input:A Direction (1-10, the verb number)',
          'Output:IX The exit (direction, thing in the way, destination)',
          'A $FF if there is no usable exit that way'],
    comments={0xD44C: 'B = direction', 0xD44D: "The actor's room record...",
              0xD450: '', 0xD453: '...+6, so the first step lands on the exits at +9',
              0xD455: 'Next exit (Z: no more)', 0xD45A: 'Destination 0?',
              0xD45E: '...a scenery exit: skip it', 0xD460: 'The right direction?'})

blk(0xDCD2, 'c', 'Pre-check for moving in a direction (verbs 1-10)',
    ["Refuses (via $DC15, \"YOU CANNOT GO ...\") when there is no usable "
     "exit that way, when the actor is inside something (sitting in an "
     "armchair - GET OUT first), or when the thing in the way stops "
     "them ($DD35).",
     "Confirmed by play for the player: every one of the 206 decoded "
     "exits behaves as this routine predicts (tools/walkall.py)."],
    comments={0xDCD2: 'The direction is the verb number',
              0xDCD5: 'Find the exit',
              0xDCDA: 'None: "YOU CANNOT GO ..."',
              0xDCDD: 'Refuse if $B934 bit 6 is set ("SORRY, I CANNOT DO THAT NOW")',
              0xDCE0: 'The actor',
              0xDCE4: 'Inside something?',
              0xDCE9: '...then they cannot walk off',
              0xDCEC: 'Destination',
              0xDCF0: '(0: refuse)',
              0xDCF3: 'The thing in the way',
              0xDCF6: '...lets the actor through?',
              0xDCF9: 'No: refuse',
              0xDCFC: 'Yes'})

blk(0xDD35, 'c', 'Can the actor get past the thing in an exit?',
    ["Nothing in the way (A = 0) always lets the actor through. "
     "Otherwise the thing must be open - +5 bit 5, or bit 3 - and its "
     "size (+2) must be at least the actor's size (IY+2).",
     "This is how guards work: the local police men at Browns and Jones "
     "front gates are themselves the 'door' of the exit they stand in. "
     "They are 'open' (bit 5) with size 69, smaller than the player (96) "
     "and Watson (96), so neither can pass, while Lestrade (32) could. "
     "The hidden door into the opium den (85) and the front door between "
     "Camden Street and the entrance hall (32) are narrower than the "
     "player too. Confirmed by play: with the player's size poked down "
     "from 96 to 8, all five of those exits let the player through."],
    regs=['Input:A The thing in the way (0 = nothing)', 'IY The actor',
          'Output:F Z set if the actor can pass'],
    comments={0xDD35: 'Nothing in the way...', 0xDD36: '...pass',
              0xDD39: "The thing's record", 0xDD3C: 'Open?',
              0xDD41: 'Its size', 0xDD46: 'Not open: refuse',
              0xDD48: "At least the actor's size?",
              0xDD4B: 'Too small: refuse', 0xDD4D: 'Pass (Z)',
              0xDD4F: 'Refuse (NZ)'})

C_MOVE = {0xDD0B: 'The actor', 0xDD0F: 'Is it the one the display follows?',
          0xDD16: 'Yes: the displayed room changes',
          0xDD1E: 'Remember the room just entered ($DD01) and its record ($DCFF)',
          0xDD29: "The actor's own record...", 0xDD2C: '...location = the new room'}
for k, v in C_MOVE.items():
    A[0xDD03]['comments'].setdefault(k, v)
A[0xDD03]['desc'].append(
    "The body also stores the destination and its room record at $DD01 "
    "and $DCFF - for ANY actor that moves, not just the player. After "
    "the boot sequence they hold room 16 (platform one of Aldergate "
    "station), left there by someone moving during the first turns. "
    "The 'what's here' code uses $DCFF, so a harness that teleports the "
    "player must set it as well, or the next room description starts "
    "with platform one.")

blk(0xA277, 'c', "Describe a room's picture",
    ["Called while describing the displayed room ($D118). $A25D decides "
     "whether there is a picture; if so the record's +1/+2 is passed to "
     "the picture interpreter at $F3C2.",
     "The picture interpreter draws through the ROM (PIXEL-ADD at $22AA), "
     "which the harness does not have, so the harness skips the call to "
     "$F3C2 (it changes no game state - see harness_notes). Before that, "
     "entering the entrance hallway (room 6) ran off into empty memory."],
    comments={0xA27C: 'Is there a picture?', 0xA287: 'The picture data...',
              0xA28D: '...drawn by the picture interpreter'})

# ---------------------------------------------------------------- facts
fact('map-decoded-and-walked',
     'The map: 106 rooms, 206 exits, every one tried',
     "The room table at $840B gives 106 rooms. tools/walkall.py puts the "
     "player in each room in turn, opens whatever is in the way, types "
     "each exit's direction and reads back where the player is: 194 of "
     "206 exits go exactly where the table says. The other 12 are the "
     "ones the code says must refuse - 7 'scenery' exits to room 0 (a "
     "deep stream, a window) that the room description mentions but the "
     "exit finder skips, and 5 through something narrower than the "
     "player. See the Map page.")

fact('police-men-are-doors',
     'The police men are doors',
     "The two local police men at Browns and Jones front gates are listed "
     "in the room table as the 'door' of the exit they guard. The move "
     "check $DD35 treats them like any other passage: they count as open, "
     "and their size, 69, is smaller than the player's 96, so the player "
     "can't get past ('YOU CANNOT GO SOUTH'), though a smaller character "
     "could. Poking the player's size down to 8 lets the player straight "
     "past both.")

# ---------------------------------------------------------------- map
def map_svg():
    import gridmap
    svg, stats = gridmap.build(RM, {r: rname(r) for r in RM}, CHECKED)
    print('grid map:', stats)
    with open(os.path.join(ROOT, 'map.svg'), 'w') as f:
        f.write(svg)
    RESOURCES['map.svg'] = os.path.join(ROOT, 'map.svg')
    return True


have_svg = map_svg()

rows = []
for r, room in RM.items():
    ex = []
    for d, door, dest in room['exits']:
        res = next((x for x in CHECKED if x['room'] == r and x['dir'] == {
            1: 'NORTH', 2: 'SOUTH', 3: 'EAST', 4: 'WEST', 5: 'NORTHEAST', 6: 'NORTHWEST',
            7: 'SOUTHEAST', 8: 'SOUTHWEST', 9: 'UP', 10: 'DOWN'}[d]), None)
        if dest == 0:
            s = f'{LONG[d]}: {html.escape(thing(door))} (scenery only)'
        else:
            s = f'{LONG[d]} to <a href="#room{dest}">{dest}</a>'
            if door:
                s += f' past {html.escape(thing(door))}'
            if res and not res['ok']:
                s += ' <em>(too narrow for the player)</em>'
        ex.append(s)
    desc = DESCS.get(r, {}).get('text', '')
    rows.append(
        f'<tr id="room{r}"><td>{r}</td><td>#R${room["address"]:04X}({html.escape(rname(r))})</td>'
        f'<td>{"<br>".join(ex) or "-"}</td>'
        f'<td>{html.escape(desc.capitalize() if desc.isupper() else desc)}</td></tr>')

page('map', 'Map and rooms',
     '<p>Decoded from the room table at #R$840B. The map is a grid: a room that '
     'is north of another is drawn above it, one to the east is drawn to its '
     'right, and so on, area by area. Arrows are the exits the room table gives; '
     'a two-headed arrow is an exit that exists in both directions; a red dashed '
     'line is an exit that is blocked for the player by something too narrow. '
     'An orange dashed line is an exit that cannot be drawn between neighbouring '
     'cells because the exit table is not a flat plan (the garden maze does this, and so do a couple of single exits in '
     'Brown\'s house and Basil\'s London house); its directions are written on it, '
     'for example NW/SE for "northwest one way, southeast back". A small purple '
     'tag under a room, such as S&rarr;76, is an exit to another area or another '
     'floor. Click a room to jump to its row below. Rooms with no walking exits '
     'are vehicles (the cab and trains), reached by getting in rather than by walking.</p>'
     + '<div style="overflow-x:auto">' + open(os.path.join(ROOT, 'map.svg')).read().replace('<svg ', '<svg style="max-width:none" ', 1) + '</div>'
     + '<p>Room descriptions below are the rooms\' own description messages, '
       'rendered by the game\'s interpreter (it prints them in capitals to the '
       'renderer; in play they appear in sentence case). Most rooms have none '
       'and are described from their name and exits alone.</p>'
     '<table class="disassembly"><tr><th>#</th><th>Room</th><th>Exits</th><th>Own description</th></tr>'
     + ''.join(rows) + '</table>')


# ---------------------------------------------------------------- things
def where(e):
    locs = [l for l in e['locations']]
    if e['container'] != 0xFF:
        return f'in/on/with {html.escape(thing(e["container"]))}'
    if locs == [0]:
        return 'off stage (room 0)'
    return ', '.join(f'<a href="map.html#room{l}">{l}</a> {html.escape(rname(l))}' for l in locs if l in RM)


SHARED = {}
try:
    from overlay_04_actions import SHARED_NAMES as SHARED  # noqa: E402
except ImportError:
    pass

trs = []
for e in O.entities():
    acts = ', '.join(f'verb #R${_w(0xAA71 + 2 * (s - 1)):04X}({v}) &rarr; shared action {s}' + (f' ({html.escape(SHARED[s])})' if s in SHARED else '')
                     for v, s in e['actions'])
    trs.append(f'<tr><td>{e["id"]}</td><td>#R${e["address"]:04X}({html.escape(O.display_name(e))})</td>'
               f'<td>{where(e)}</td><td>{e["size"]}</td><td>{acts or "-"}</td></tr>')
page('things', 'Characters and things',
     '<p>Every entry in the entity index at #R$8B6F, decoded by objects.py. Ids 0-13 are '
     'the characters (0 is you). Size is record byte +2: how big a thing is, and for a '
     'container how much it holds (#R$DEE4); for passages it is how big an actor may be '
     'to get through (#R$DD35). "Starts" is the state in the file, before play.</p>'
     '<table class="disassembly"><tr><th>Id</th><th>Name</th><th>Starts</th><th>Size</th>'
     '<th>Its own actions</th></tr>' + ''.join(trs) + '</table>')

# ---------------------------------------------------------------- words
words = D.all_words()
by_off = {w['offset']: w for w in words}
wrows = []
for w in words:
    syn = ''
    if w['extra'] is not None:
        tgt = by_off.get(w['extra'] & 0x0FFF)
        syn = f'same as {tgt["word"]}' if tgt else f'${w["extra"]:04X}'
    wrows.append(f'<tr><td>#R${w["address"]:04X}({w["word"]})</td><td>${w["offset"]:03X}</td>'
                 f'<td>${w["flags0"]:02X}</td><td>{syn}</td></tr>')
page('vocabulary', 'Vocabulary',
     f'<p>All {len(words)} words of the dictionary at #R$5DC0, decoded by dictionary.py the '
     'way the game expands them (front-coded letter buckets, 5-bit letters, a suffix '
     'table). The offset is what the rest of the game uses to refer to a word (verb '
     'patterns, names of rooms and things, messages). Flags are the record\'s first '
     'byte; its low nibble is the suffix number.</p>'
     '<table class="disassembly"><tr><th>Word</th><th>Offset</th><th>Flags</th><th>Synonym</th></tr>'
     + ''.join(wrows) + '</table>')


# ---------------------------------------------------------------- shared doors
def _shared_doors():
    pairs = {}
    for r, room in RM.items():
        for d, door, dest in room['exits']:
            if door and dest:
                pairs.setdefault(door, set()).add(tuple(sorted((r, dest))))
    return {d: sorted(p) for d, p in pairs.items() if len(p) > 1}


SHARED_DOORS = _shared_doors()
bug('one-front-door-for-three-houses',
    'One front door for three houses',
    "Doors are things, and to save memory one door thing serves several "
    "doorways in different buildings: a door's record lists every room "
    "it appears in (record +15...), and its open/closed state (+5 bit 5) "
    "is shared by all of them. The front door (thing 19) is the front "
    "door of Baker Street, of the Jones house (rooms 93/96) and of the "
    "house on Cobden Lane (51/56). Confirmed in the emulator: at the "
    "start every one of them is shut ('YOU CANNOT GO SOUTH' at Jones "
    "Front Door); after OPEN FRONT DOOR in your own entrance hallway, "
    "SOUTH at Jones Front Door and EAST in Cobden Lane both walk straight "
    "in, without anyone opening them. (The player was placed at those "
    "doors by poking the location rather than walked there.) "
    + f"{len(SHARED_DOORS)} door things are shared like this: "
    + '; '.join(f'{thing(d)} ({len(p)} doorways)' for d, p in SHARED_DOORS.items())
    + '.')
