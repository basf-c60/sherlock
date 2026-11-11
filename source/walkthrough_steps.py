"""Builds the step-by-step part of the walkthrough page from walkthrough_v12.json
(made by tools/experiments/walkthrough_steps.py: one fresh-boot replay of the 372-command winning file,
recording the clock, the place and the game's reply after every command)."""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rooms as _rooms

DATA = json.load(open(os.path.join(HERE, 'walkthrough_v12.json')))
STEPS = DATA['steps']
RM = _rooms.rooms()
ABL = {int(k): v['win'] for k, v in json.load(open(os.path.join(HERE, 'walkthrough_ablation_v12.json'))).items()}
GREEDY = json.load(open(os.path.join(HERE, 'walkthrough_greedy_v12.json')))
DAY = ['Mon', 'Tue', 'Wed']
MOVE = re.compile(r'^(NORTH|SOUTH|EAST|WEST|NORTHEAST|NORTHWEST|SOUTHEAST|SOUTHWEST|UP|DOWN)$')

# (first step, last step, title, what this stretch does, optional note)
PHASES = [
 (1, 6, 'Take the lamp and get Watson moving',
  'Take the oil lamp, then WAIT until Watson reads out the case (8:16am). SAY TO WATSON "FOLLOW ME" so that he comes along; '
  'he is with you in every cab and train from here.', None),
 (7, 11, "Pick up the china man's disguise",
  'Open the plain door, go north into the small closet, WEAR the china man\'s disguise and TAKE it OFF again, then back south. '
  'The disguise is carried from now on (the inventory at step 51 lists it).', None),
 (12, 22, 'Baker Street to Kings Cross Road by cab',
  'Out of the flat and the front door, HAIL CAB, climb in, and SAY TO CABBIE "GO TO KINGS CROSS ROAD". The ride takes about 80 minutes '
  '(8:41 to 10:01am), so the LOOK is repeated until the cab arrives. PAY 10D TO CABBIE, then climb out.',
  'Here the fare comes to 6d: paying 10d gets 4d back (the page on trains and cabs explains how the fare is worked out).'),
 (23, 30, 'Kings Cross to Leatherhead by steam train',
  'Four NORTHEAST moves up through the platforms to platform three, wait for the steam train (it enters at 10:45), climb in at 10:47, '
  'and ride to Leather Head platform one (12:00 noon). Climb out.', None),
 (31, 37, "Leatherhead to Brown's front gate; Lestrade arrives",
  'South through the station to the main street, a quick look into the police station, then WEST to Browns Front Gate. '
  'LOOK until Inspector Lestrade arrives (12:25pm); he introduces Chief Constable Straker.', None),
 (38, 51, 'The bridge: corpse, bridge, crumpled note',
  'Down the garden paths to the east side of the sandstone bridge (12:39pm). EXAMINE CLOSELY the female corpse and the bridge, TAKE the crumpled note and '
  'EXAMINE CLOSELY it ("Meet me by the bridge at half past twelve..."). The rock is not here on Monday.', None),
 (52, 61, "Back round the garden and along to Jones's house",
  'A loop of garden paths (SOUTHEAST, EAST, NORTH, NORTH, NORTH, NORTHWEST, WEST, NORTH) brings you back to the front gate by 1:14pm; '
  'then EAST along the main street to Jones Front Gate.',
  'Each of the eight moves is needed (checked one at a time). Replacing the loop with the direct way back (WEST, NORTH, NORTH, NORTHEAST, NORTH, as on Tuesday), with a WAIT and a LOOK added so that you reach the gate at the same minute, loses. The reason the loop is needed is not known.'),
 (62, 87, "Jones's house: the library, the bookcase, the clothes",
  'OPEN FRONT DOOR, the sitting room, the solid door and into the library (1:31pm). EXAMINE CLOSELY the body and the bookcase (it swings open on a small room). '
  'Lestrade, Straker and the Major come in; SAY TO LESTRADE "MAJOR PERCIVAL FFOULKES IS INNOCENT" and he asks for proof. '
  'In the small room, EXAMINE CLOSELY and TAKE the bloodstained clothes (labelled "Tricia. Fender."), then out through the house to Jones Front Gate (2:06pm).', None),
 (88, 115, "Brown's house: the study",
  'West along the main street to the gate, south down the garden path to Browns Front Door, OPEN LARGE OAK DOOR, then the long passage and the wooden door into the study (2:22pm). '
  'EXAMINE CLOSELY the drawer, OPEN it, find and OPEN the false bottom, TAKE and EXAMINE CLOSELY the bank account book and the note. '
  'The crumpled note is dropped in the passage (step 100) and you go back in. Then out again to the front door.',
  'Steps 98, 101 and 111 try to open the wooden door when it is already open. Each can be left out, and all three together can be left out (checked).'),
 (116, 125, 'Back to Leather Head platform two',
  'North to the gate, EAST to the main street, then NORTH three times up to platform two (3:11pm). Three extra NORTH commands at the gate (steps 118-120) get "YOU CANNOT GO NORTH".',
  'A command that fails costs no time by itself, but each failure adds 3 to a count that the game keeps for the turn; when the count passes 10 the character gives up and one minute passes (the code is at $CD8B; in the game the count goes 2, 5, 8 and then starts again while the clock moves on one minute at the third NORTH). So steps 118-120 are a way of spending exactly one minute. One LOOK or one INVENTORY (a minute each) in their place still wins; a WAIT (five minutes) does not.'),
 (126, 137, 'Platform two to Kings Cross by train',
  'WAIT until the train enters (3:18pm), climb in at 3:21 with Lestrade, SAY TO LESTRADE "MAJOR PERCIVAL FFOULKES IS INNOCENT" again (he still wants proof), '
  'and wait to Kings Cross platform four (4:33pm). Back down to Kings Cross Road.', None),
 (138, 144, 'Kings Cross Road to Slater Street by cab',
  'HAIL CAB, climb in, SAY TO CABBIE "GO TO SLATER STREET". Arrive 5:09pm, PAY 10D TO CABBIE, climb out and LOOK: there is a hidden door to the north.', None),
 (145, 153, "The opium den: the Major's confession",
  'WAIT (80 times) until 11:53pm. While you wait the Major arrives by cab, does not pay and goes north through the hidden door; the cabbie shouts at him. '
  'WEAR the china man\'s disguise to pass the narrow hidden door, go NORTH into the opium den and TAKE OFF the disguise: the Major confesses. '
  'WEAR it again, SOUTH, and SAY TO LESTRADE "MAJOR PERCIVAL FFOULKES VISITED OPIUM DEN"; Lestrade lets the Major go. TAKE OFF the disguise.', None),
 (154, 165, 'Slater Street to Kings Cross platform four (Tuesday 1:30am)',
  'WAIT to 12:53am, HAIL CAB, SAY TO CABBIE "GO TO KINGS CROSS ROAD", pay, and walk NORTHEAST up to platform four.',
  'The first walkthrough warned that taking this cab at 12:20-12:45am leaves Lestrade stuck in a cab. That did not reproduce: waiting only until 12:3 instead of 12:5 (the cab is hailed at 12:34am) still wins.'),
 (166, 172, 'Wait for the 7:30am train; to Leatherhead',
  'WAIT through the night until the steam train enters at 7:30am, climb in at 7:32 and ride to Leather Head platform one (9:00am). Climb out.', None),
 (173, 186, 'The bridge again: the gun in the stream',
  'The same garden route to the east side of the bridge (9:20am). EXAMINE CLOSELY DEEP STREAM: Lestrade finds a gun tied to a large rock. Then back to the main street.', None),
 (187, 205, "Basil's house at Cobden Lane: the wall safe",
  'OPEN FRONT DOOR, the sitting room, to Basils Library. OPEN WALL SAFE (it takes 15 minutes), TAKE and EXAMINE CLOSELY the letters (blackmail letters to Mrs Brown from Tricia). '
  'Back out and to Leather Head platform two (10:23am).', None),
 (206, 214, 'Platform two to Kings Cross by train',
  'LOOK until the steam train enters (10:45am), climb in, wait to Kings Cross platform four (12:03pm), climb out and walk back down to Kings Cross Road.', None),
 (215, 221, 'Kings Cross Road to Portman Street by cab',
  'WAIT to 12:30pm, HAIL CAB, SAY TO CABBIE "GO TO PORTMAN STREET". Arrive 12:54pm, pay, climb out.', None),
 (222, 237, "Tricia Fender's house",
  'OPEN TRICIAS FRONT DOOR, south, OPEN THICK HEAVY DOOR, south into Tricias Lounge (1:03pm). The first SAY TO TRICIA FENDER gets an answer (it is really Mrs Jones); '
  'after that the person is called Mrs Jones and the next two get "I SEE NO TRICIA FENDER". Then SAY TO MRS JONES "TELL ME ABOUT YOUR ALIBI" three times. '
  'OPEN WALL SAFE (15 minutes), EXAMINE CLOSELY the unfinished note and the folder ("Top Secret. Military plans."). Back out to Portman Street.',
  'Steps 226, 227 and 228 are the same line. Any one of them can be left out, but leaving only the first loses, so the extra lines matter even though two of them fail (checked). The bug entry on stale quotations describes how a failed SAY leaves its quotation behind; whether that is why the failing lines matter was not checked directly.'),
 (238, 247, 'Portman Street to Scotland Yard',
  'HAIL CAB and climb in. SAY TO CABBIE "GO TO PARLIAMENT STREET" four times: the first two and the last only get "You talk to the cabbie", '
  'and the cab sets off on the third (1:43pm). Arrive 1:54pm, pay, climb out and go EAST into Scotland Yard.', None),
 (248, 255, 'Scotland Yard: the statements',
  'Two bare SAY TO LESTRADE lines and a TALK TO LESTRADE open the conversation, then SAY TO LESTRADE "MRS BROWN KILLED HERSELF" and "MRS JONES KILLED TRICIA FENDER" (he is delighted; Mrs Jones is led away). '
  '"TRICIA FENDER HAD PLANS" gets "I do not see the importance of that"; "PHIPPS HAS PLANS" and "THE SALE LOCATION IS OLD MILL ROAD" get "I do not believe that you have the evidence".',
  'PHIPPS HAS PLANS is not said again in this route; the sale location is said again at step 323.'),
 (256, 269, "Scotland Yard to Basil's front yard; wait for the window",
  'WEST, HAIL CAB, SAY TO CABBIE "GO TO CAMDEN STREET" (arrive 2:18pm), pay, climb out, EAST into Basils Front Yard. '
  'WAIT and LOOK until "Someone opens the window" at 10:03pm.', None),
 (270, 295, "Inside Basil's house in disguise (Tuesday night)",
  'WEAR the china man\'s disguise, NORTHEAST through the window, through the oak door and the thick heavy door to Basils Library; TAKE the ripped coded note '
  '(step 277 mistypes it and gets "WHAT ?"), TAKE OFF the disguise to EXAMINE CLOSELY it. North-west to the passage, the plain door, the kitchen and back door to Basils Yard; '
  'EXAMINE CLOSELY the trash pile, TAKE and EXAMINE CLOSELY the torn coded note. WEAR the disguise again and retrace to the front yard (10:51pm); TAKE OFF.',
  'Step 282 tries to open a door that is already open and can be left out.'),
 (296, 304, 'Wednesday morning: wait outside',
  'WAIT through the night to 9:41am, then LOOK up to 10:06am. You stay in the front yard; the earlier notes say Phipps shoots anyone in the bedroom at 9:50am and leaves at 10:06.', None),
 (305, 312, "Basil's bedroom: the burning note",
  'NORTHEAST into Basils Bedroom (10:08am). TAKE NOTE FROM FIREPLACE (it is burning), EXAMINE it, DROP BURN NOTE and TAKE BURN NOTE (this stops it burning), '
  'then EXAMINE CLOSELY SINGE NOTE: it shows the same coded text. Back out SOUTHWEST.', None),
 (313, 323, 'Camden Street to Scotland Yard: the sale location',
  'WEST, HAIL CAB, SAY TO CABBIE "GO TO PARLIAMENT STREET" (arrive 10:36am), pay, EAST into Scotland Yard. TALK TO LESTRADE, then '
  'SAY TO LESTRADE "THE SALE LOCATION IS OLD MILL ROAD": this time he says "we must hurry if we are to catch them" and goes west.', None),
 (324, 343, 'To Leatherhead with Lestrade',
  'WEST, HAIL CAB (Lestrade climbs in and tells the cabbie Kings Cross Road); arrive 11:00am, pay (Lestrade pays too), walk up to platform four, LOOK until the steam train enters (noon), '
  'climb in at 12:02 and ride to Leather Head platform one (1:30pm). Out, SOUTH twice to the main street (1:36pm).', None),
 (344, 348, 'The police cab to Old Mill Road',
  'CLIMB INTO POLICE CAB at once (1:38pm); the ride takes about 95 minutes. At Old Mill Road (3:13pm) you can see Basil Phipps and a german agent; '
  'Basil whips his horses into action and speeds off at 3:14, and Lestrade tells the police man to go furiously back to the main street.', None),
 (349, 353, 'Back to the main street', 'LOOK through the ride (4:47pm in the main street), then CLIMB OUT (4:49pm).', None),
 (354, 363, 'Find Lestrade and take the police cab again',
  'NORTH x3 to platform two (4:54pm); Lestrade says "I am afraid that Basil has eluded us Holmes". SAY TO LESTRADE "FOLLOW ME", SOUTH x3 to the main street, '
  'CLIMB INTO POLICE CAB and SAY TO POLICE MAN "GO FURIOUSLY TO KINGS CROSS ROAD" (5:06pm).', None),
 (364, 372, 'Kings Cross Road to Victoria: the arrest',
  'LOOK until Kings Cross Road (6:20pm): Basil and the german agent are in two hansom cabs and tell the cabbies to go to Buckingham Palace Road. CLIMB OUT, '
  'NORTHEAST x2 to platform one, CLIMB INTO TRAIN at once (it leaves at 6:29), ride to Victoria platform one (6:41pm), CLIMB OUT, WAIT: '
  'Basil pulls a gun, Watson pushes you aside, Lestrade captures them, and the game is won.', None),
]


def clock(c):
    return '%s %d:%02d%s' % (DAY[c['day']], c['h'], c['m'], 'am' if c['ap'] == 'a' else 'pm')


def where(s):
    r = s['after']['room']
    if r == 0:
        return 'in disguise'
    room = RM.get(r)
    return _rooms.room_name(room).title() if room else 'room %d' % r


def reply(s):
    t = s['reply']
    t = re.sub(r'(Mon|Tue|Wed) \d+:\d\d[ap]m >?', '', t)
    t = ' '.join(t.replace('|', ' ').split())
    cmd = s['cmd']
    pat = r'[\s."]*'.join(re.escape(ch) for ch in cmd if ch.isalnum()) + r'[."]*\s*'
    m = re.search(pat, t, re.I)
    if m:
        t = t[m.end():]
    t = t.strip(' >')
    tag = ''
    if re.match(r'(YOU CANNOT|I SEE NO|WHAT \?|I DO NOT)', t):
        tag = '(no effect) '
    elif re.match(r'THE [A-Z ]+ IS OPEN', t) or re.match(r'[A-Z ]+ IS OPEN', t):
        tag = '(already open) '
    limit = 700 if s['i'] >= 371 else 230
    if len(t) > limit:
        t = t[:limit].rsplit(' ', 1)[0] + ' ...'
    if MOVE.match(cmd) and not tag:
        t = ''
    return tag + t


def step_row(s):
    cmd = '<code>%s</code>' % html.escape(s['cmd'])
    if s['until']:
        cmd += ' &times;%d <small>(repeated until the reply shows &ldquo;%s&rdquo;)</small>' % (s['n'], html.escape(s['until']))
    return ('<tr><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
            % (s['i'], cmd, clock(s['after']), html.escape(where(s)), html.escape(reply(s)),
               'still wins' if ABL[s['i']] else 'loses'))



def about():
    n_ok = sum(1 for v in ABL.values() if v)
    dropped = GREEDY['dropped']
    keep = GREEDY['kept_candidates']
    drop_list = ', '.join('%d <code>%s</code>' % (n, html.escape(STEPS[n - 1]['cmd'])) for n in sorted(dropped))
    return (
     '<h2>How exact the route is</h2>'
     '<p>Typed exactly as listed from a fresh start, these %d lines win every time. The last column of each table comes from a check: '
     'the game was started again from scratch and the route typed in with that one line left out and everything else unchanged. '
     '<strong>%d lines still win without it</strong> and <strong>%d lose</strong> (the game ends another way, or the final scene never comes). '
     '&ldquo;Loses&rdquo; says only that the exact sequence breaks; it cannot tell a line that matters to the story from one that only keeps the clock and the '
     'game&rsquo;s random numbers in step, because leaving out one line moves every later minute.</p>'
     '<ul>'
     '<li><strong>Lines that can go.</strong> Taking out all %d of the lines that win alone, at once, loses. Taking them out one after another, and keeping each removal only if the route '
     'still won, removed %d lines in all, leaving a %d-line route that still wins from a fresh start. The lines removed were: %s. '
     'The other %d (steps %s) each win alone but lost once the others were gone.</li>'
     '<li><strong>Timing is exact.</strong> Putting a one-minute INVENTORY in before step 31 or before step 251 still wins; before step 101, 151, 201, 301 or 341 it loses. '
     'So a single minute more or less in the middle of the route changes the outcome.</li>'
     '<li><strong>Failed commands.</strong> A command that fails costs no time by itself, but each failure adds 3 to a count kept for the turn; when the count passes 10 the character gives up and a minute passes. '
     'Three failures in a row therefore cost one minute (steps 118-120).</li>'
     '<li><strong>What this does not show.</strong> It does not say why a particular line is needed. Where the reason is known, it is given in the notes under the stretch; where it is not (the garden loop at steps 52-59), the note says so.</li>'
     '</ul>' % (len(STEPS), n_ok, len(STEPS) - n_ok, n_ok, len(dropped), GREEDY['length'], drop_list,
                len(keep), ', '.join(str(n) for n in sorted(keep))))


def body():
    assert PHASES[0][0] == 1 and PHASES[-1][1] == len(STEPS)
    for a, b in zip(PHASES, PHASES[1:]):
        assert b[0] == a[1] + 1, (a, b)
    out = [about()]
    out.append('<h2>The route in %d stretches</h2><ol>' % len(PHASES))
    for n, (a, b, title, summ, note) in enumerate(PHASES, 1):
        t0 = clock(STEPS[a - 1]['before']); t1 = clock(STEPS[b - 1]['after'])
        out.append('<li><a href="#walk%d">%s</a> <small>(steps %d-%d, %s to %s)</small></li>' % (n, html.escape(title), a, b, t0, t1))
    out.append('</ol>')
    for n, (a, b, title, summ, note) in enumerate(PHASES, 1):
        t0 = clock(STEPS[a - 1]['before']); t1 = clock(STEPS[b - 1]['after'])
        out.append('<h3 id="walk%d">%d. %s</h3>' % (n, n, html.escape(title)))
        out.append('<p><small>Steps %d-%d, %s to %s.</small> %s</p>' % (a, b, t0, t1, html.escape(summ)))
        if note:
            out.append('<p><em>Note:</em> %s</p>' % html.escape(note))
        out.append('<div class="tablewrap"><table class="steps"><tr><th>Step</th><th>Type</th><th>Clock after</th><th>Where</th><th>The game replies</th><th>Without this line</th></tr>')
        out.extend(step_row(s) for s in STEPS[a - 1:b])
        out.append('</table></div>')
    return ''.join(out)
