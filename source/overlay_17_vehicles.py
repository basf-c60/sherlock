"""The trains-and-cabs page: how the timetables work, how a train moves from station to station, and
how a hansom cab is hailed, ridden and sent away.  The timetable tables are worked out here from the
plan scripts' own numbers, so they cannot drift from the code."""
from build_skeleton import page

# ---------------------------------------------------------------- the timetables, as the scripts hold them
# One entry per instruction: (room the train is put in, or None to stay where it is, minutes).
LOOP1 = [(16, 3), (2, 3), (20, 3), (2, 1), (None, 2), (26, 4), (2, 4), (None, 1), (30, 4), (2, 5)]
LOOP2 = [(None, 2), (21, 3), (2, 3), (17, 3), (2, 1), (None, 4), (31, 4), (2, 1), (None, 4), (27, 4), (2, 1)]
LOOPL = [(None, 60), (23, 10), (4, 5), (22, 10), (3, 5), (None, 60), (54, 10), (4, 5), (55, 10), (3, 5)]
# actor: (loop, index of the instruction its actor-table entry points at)
START = {36: (LOOP1, 0), 38: (LOOP1, 4), 37: (LOOP1, 7), 39: (LOOP2, 0), 41: (LOOP2, 5), 40: (LOOP2, 8),
         42: (LOOPL, 0), 43: (LOOPL, 5)}
NAME = {16: 'Aldergate platform one', 17: 'Aldergate platform two', 20: 'Kings Cross platform one',
        21: 'Kings Cross platform two', 22: 'Kings Cross platform three', 23: 'Kings Cross platform four',
        26: 'Paddington platform one', 27: 'Paddington platform two', 30: 'Victoria platform one',
        31: 'Victoria platform two', 54: 'Leatherhead platform one', 55: 'Leatherhead platform two'}


def clock(t):
    """Minutes after 8:00am -> '8:10am'."""
    m = 8 * 60 + t
    h, mi = divmod(m, 60)
    h %= 24
    return '%d:%02d%s' % ((h % 12) or 12, mi, 'am' if h < 12 else 'pm')


def visits(actor, until):
    """(arrival minute, room, minutes stayed) for every platform or transit stop."""
    loop, k = START[actor]
    t, out = 0, []
    while t < until:
        room, mins = loop[k % len(loop)]
        if room is not None:
            out.append((t, room, mins))
        t += mins
        k += 1
    return out


def platform_arrivals(rooms, actors, until, limit):
    res = {}
    for r in rooms:
        ts = sorted(t for a in actors for (t, room, mins) in visits(a, until) if room == r)
        res[r] = ts[:limit]
    return res


_UG1 = platform_arrivals([16, 20, 26, 30], [36, 37, 38], 600, 6)
_UG2 = platform_arrivals([21, 17, 31, 27], [39, 40, 41], 600, 6)
for _r, _ts in _UG1.items():
    assert all(b - a == 10 for a, b in zip(_ts, _ts[1:])), (_r, _ts)       # a train every ten minutes
for _r, _ts in _UG2.items():
    assert [b - a for a, b in zip(_ts, _ts[1:4])] in ([9, 9, 12], [9, 12, 9], [12, 9, 9]), (_r, _ts)
_LH = platform_arrivals([23, 22, 54, 55], [42, 43], 900, 8)
for _r, _ts in _LH.items():
    assert all(b - a == 90 for a, b in zip(_ts, _ts[1:])), (_r, _ts)       # a train every ninety minutes


def _ug_rows(d, order):
    rows = []
    for r in order:
        ts = d[r]
        rows.append('<tr><td>%s (#R$%04X)</td><td>%s</td></tr>' % (
            NAME[r], ROOMADDR[r], ', '.join(clock(t) for t in ts) + ' ...'))
    return '\n'.join(rows)


# room record addresses, for the links
ROOMADDR = {1: 0x84EB, 2: 0x84F5, 3: 0x84FF, 4: 0x8509, 16: 0x85AE, 17: 0x85BE, 20: 0x85E8, 21: 0x85F8,
            22: 0x8608, 23: 0x8618, 26: 0x8642, 27: 0x8652, 30: 0x867C, 31: 0x868C, 54: 0x87FC,
            55: 0x880C, 105: 0x8B65}

# ---------------------------------------------------------------- the cab journey table (#R$9B7F)
JOURNEYS = [(45, 5, 3), (45, 10, 7), (45, 12, 20), (45, 14, 19), (45, 18, 18), (45, 24, 7), (45, 28, 12),
            (45, 32, 6), (45, 40, 13), (5, 10, 20), (5, 12, 25), (5, 14, 26), (5, 18, 12), (5, 24, 6),
            (5, 28, 15), (5, 32, 24), (5, 40, 9), (10, 12, 18), (10, 14, 18), (10, 18, 12), (10, 24, 19),
            (10, 28, 2), (10, 32, 4), (10, 40, 15), (12, 14, 3), (12, 18, 20), (12, 24, 30), (12, 28, 20),
            (12, 32, 17), (12, 40, 25), (14, 18, 13), (14, 24, 28), (14, 28, 17), (14, 32, 9), (14, 40, 11),
            (18, 24, 11), (18, 28, 16), (18, 32, 18), (18, 40, 3), (24, 28, 15), (24, 32, 24), (24, 40, 13),
            (28, 32, 12), (28, 40, 19), (32, 40, 22)]
STANDS = [(45, 'Portman St'), (5, 'Baker St'), (10, 'Parliament St'), (12, 'Slater St'), (14, 'Aldergate St'),
          (18, 'Kings Cross Rd'), (24, 'Bishops Rd'), (28, 'Buckingham Palace Rd'), (32, 'Camden St'),
          (40, 'Sidmouth St')]


def _matrix():
    mins = {}
    for a, b, m in JOURNEYS:
        mins[(a, b)] = mins[(b, a)] = m
    head = '<tr><th></th>' + ''.join('<th>%s</th>' % n for _, n in STANDS) + '</tr>'
    rows = [head]
    for ra, na in STANDS:
        cells = []
        for rb, nb in STANDS:
            cells.append('<td>&ndash;</td>' if ra == rb else '<td>%d</td>' % mins[(ra, rb)])
        rows.append('<tr><th>%s</th>%s</tr>' % (na, ''.join(cells)))
    return '\n'.join(rows)


def _loop_rows(loop, start_names):
    rows, t = [], 0
    for i, (room, mins) in enumerate(loop):
        where = ('%s (#R$%04X)' % (NAME[room], ROOMADDR[room])) if room in NAME else (
            'between stations (room %d, #R$%04X)' % (room, ROOMADDR[room]) if room else 'stays where it is')
        rows.append('<tr><td>%d</td><td>%s</td><td>%d</td><td>%s</td></tr>' % (
            i + 1, where if room else 'waits where it is (in the same room as before)', mins, start_names.get(i, '')))
        t += mins
    return '\n'.join(rows), t


_L1, _P1 = _loop_rows(LOOP1, {0: 'actor 36 starts here', 4: 'actor 38 starts here', 7: 'actor 37 starts here'})
_L2, _P2 = _loop_rows(LOOP2, {0: 'actor 39 starts here', 5: 'actor 41 starts here', 8: 'actor 40 starts here'})
_LL, _PL = _loop_rows(LOOPL, {0: 'actor 42 starts here', 5: 'actor 43 starts here'})
assert (_P1, _P2, _PL) == (30, 30, 180)

_HTML = '''
<p>Sherlock has two kinds of public transport. <b>Trains</b> run to a timetable whether or not you are there: eight steam trains circle the underground stations and run the Leatherhead line. <b>Hansom cabs</b> are the opposite: they stand off stage until somebody hails one, and they go nowhere unless they are told to. Both are ordinary things that hold other things, so a passenger is simply something inside the vehicle, and when the vehicle moves everything in it moves too.</p>

<h3>The short answers</h3>
<ul>
<li><b>How does a timetable work?</b> Each train is an actor (#R$9860) running a short plan script that says "put the train in room X, then wait N minutes", over and over. The timetable <i>is</i> that script: the waits add up to a 30-minute circuit for the underground and a 3-hour circuit for the Leatherhead line. Where each train starts in the cycle is just which instruction its actor-table entry points at.</li>
<li><b>How does a train get from station to station?</b> One action record (#R$E4C9) puts the train in the next room with the move routine at #R$DD0E, and makes the train visible at a platform and invisible between stations. There is no track and no distance: a journey is a number of minutes spent in a "between stations" room.</li>
<li><b>Do cabs move when they are not hailed?</b> No. An unhailed cab is in room 0, off stage, and its cabbie only runs a do-nothing loop (#R$F2B2). A cab moves only when somebody hails it. In the first minutes of the game Lestrade hails cab 30 in Parliament Street and rides it to Kings Cross Road; until 3pm that is the only cab movement in a game where the player does nothing. After that Phipps, the Major and the German agent take cabs as part of their flights.</li>
</ul>

<h3>The things and rooms involved</h3>
<table class="sherlock">
<tr><th style="min-width:9em">What</th><th>Thing or room numbers</th><th>Notes</th></tr>
<tr><td>Underground trains</td><td>things 36 to 41 (actors 36 to 41)</td><td>Three run one way round the platform-one stations and three the other way round the platform-two stations.</td></tr>
<tr><td>Leatherhead trains</td><td>things 42 and 43 (actors 42 and 43)</td><td>Two trains on the same three-hour circuit, half a circuit apart.</td></tr>
<tr><td>Hansom cabs and cabbies</td><td>cab 30 with cabbie 31; cab 33 with cabbie 34</td><td>The cabbie is always the next number after his cab (#R$9B50 relies on it). Both cabbies are actors (#R$9860).</td></tr>
<tr><td>Police cab</td><td>thing 109, room 105 (#R$8B65)</td><td>Driven by the local police man. It has only three routes (#R$9AA3).</td></tr>
<tr><td>Rooms for a train in motion</td><td>room 2 (#R$84F5) for the underground; rooms 3 (#R$84FF) and 4 (#R$8509) for the Leatherhead line</td><td>These are the "between stations" rooms. A passenger's own room number becomes the room the train is in.</td></tr>
<tr><td>Room for a cab in motion</td><td>room 1 (#R$84EB)</td><td>The hansom cab: the cab is put here for the length of the ride, then moved to the destination.</td></tr>
<tr><td>Station rooms</td><td>Aldergate 15 (platforms 16, 17); Kings Cross 19 (platforms 20, 21 underground and 22, 23 Leatherhead); Paddington 25 (26, 27); Victoria 29 (30, 31); Leatherhead 53 (54, 55)</td><td>A station room has no description of its own; the trains stop only in the platform rooms.</td></tr>
</table>

<h3>How a timetable is written</h3>
<p>Every actor has an eight-byte record in the actor table (#R$9860): its thing number, the position in its plan script (+1/+2), the plan registers, and the minute at which it next acts (+6/+7). Once per turn the main loop (#R$A064) walks the table; an actor whose minute has come runs one step of its script (#R$CC78), and the step's duration decides when it next acts. A train's script is built from two instructions only:</p>
<ul>
<li><b>DO 140 room, minutes</b>, four bytes such as <code>$02,$8C,$10,$03</code>, is "put the train in room $10 and wait 3 minutes". It is a call of the sub-script at #R$F2A5, which runs the move record (#R$E4C9) and then the wait record (#R$DDBE).</li>
<li><b>RUN #R$DDBE minutes</b>, five bytes such as <code>$07,$BE,$DD,$3C,$FF</code>, is a plain wait (here 60 minutes) with the train left where it is.</li>
</ul>
<p>A <code>GOTO</code> (<code>$0E</code>) at the end sends the script back to its start, and a <code>PASS</code> (<code>$0F</code>) is a one-minute pause. Because the waits are the only thing that spends time, adding up the minutes gives the timetable exactly.</p>

<h4>The underground: two circuits of 30 minutes</h4>
<p>Six trains share two scripts. The first circuit (#R$F21D to #R$F243) calls at the platform-one stations in the order Aldergate, Kings Cross, Paddington, Victoria; the second (#R$F246 to #R$F275) goes the other way round the platform-two stations: Kings Cross, Aldergate, Victoria, Paddington. Each train is a different distance round the same script because its actor-table entry points at a different instruction, so the three trains on a circuit are spread round it: ten minutes apart on the platform-one circuit, and nine, nine and twelve minutes apart on the platform-two circuit.</p>
<table class="sherlock">
<tr><th>Step</th><th>Platform-one circuit: where the train is</th><th>Minutes</th><th>Start of the day</th></tr>
%s
<tr><td></td><td><b>Whole circuit</b></td><td><b>%d</b></td><td></td></tr>
</table>
<table class="sherlock">
<tr><th>Step</th><th>Platform-two circuit: where the train is</th><th>Minutes</th><th>Start of the day</th></tr>
%s
<tr><td></td><td><b>Whole circuit</b></td><td><b>%d</b></td><td></td></tr>
</table>
<p>From the start of the game (8:00am) a train reaches each platform-one platform every ten minutes. Each platform-two platform gets three trains in every 30 minutes, nine, nine and twelve minutes apart. A train stays three or four minutes. The first arrivals:</p>
<table class="sherlock">
<tr><th>Platform</th><th>Trains arrive at</th></tr>
%s
%s
</table>
<p>The ride from one platform to the next is three or five minutes, depending on the stretch (the platform-one train takes 3 from Aldergate to Kings Cross, 3 on to Paddington, 5 on to Victoria and 5 back to Aldergate).</p>

<h4>The Leatherhead line: one circuit of three hours</h4>
<p>The two Leatherhead trains run the same script (#R$F278 to #R$F2A2) from different starting points. A train stops at Kings Cross platform four, shunts to platform three, then spends 65 minutes on the line in room 3, and does the same at Leatherhead (platforms one and two) before the long run back.</p>
<table class="sherlock">
<tr><th>Step</th><th>Where the train is</th><th>Minutes</th><th>Start of the day</th></tr>
%s
<tr><td></td><td><b>Whole circuit</b></td><td><b>%d</b></td><td></td></tr>
</table>
<p>The two trains are half a circuit apart, so a train arrives at each platform every 90 minutes:</p>
<table class="sherlock">
<tr><th>Platform</th><th>Trains arrive at</th></tr>
%s
</table>
<p>The journey from Kings Cross platform three to Leatherhead takes 65 minutes. A passenger who stays on the train is carried on: at the end of a stop the train moves to the other platform of the same station, so riding on from Leatherhead platform one takes you to platform two, five minutes later, by way of the between-stations room 4 (you cannot get out there). This timetable decides the endgame chase. Phipps boards the train that leaves Leatherhead platform two at 4:55pm, and the next one is 90 minutes behind it (#R$E7E7).</p>

<h3>How a train moves from station to station</h3>
<p>The move is one action record, "put a train in a room" (#R$E4C9, internal verb 140). It does four things:</p>
<ol>
<li>Takes the room number from the direct object (#R$A032($A034)). If it is room 2, 3 or 4, the train is about to leave a station, so it prints THE TRAIN PULLS OUT OF THE STATION. (#R$7611) and uses the routine that <i>clears</i> the train's revealed bit (+5 bit 7, #R$9C60). Otherwise it uses the routine that <i>sets</i> it (#R$9C56). A train is therefore visible at a platform and invisible between stations: the visibility test (#R$C821) refuses anything without that bit.</li>
<li>Moves the train, with everything inside it, to the room (#R$DD0E). The move updates the +15 room byte of the train and of each passenger, and the player's own room, so a passenger's room number follows the train: 23, then 4, then 22, then 3 on the first stage of the Leatherhead run.</li>
<li>Clears bit 6 of the new room's record (the "visited" bit), so the room description is shown in full again.</li>
<li>Returns "done"; the script then waits the stated minutes.</li>
</ol>
<p>Everything a train prints is shown only when the player can see it. Before each actor's turn the engine switches printing off (#R$CC61) and switches it on only if the actor and the player can see each other (#R$C821), so a train pulling out on the other side of London is silent. When a train arrives at your platform the move narration prints A STEAM TRAIN ENTERS.</p>

<h4>Getting on and off</h4>
<p>CLIMB INTO TRAIN works like getting into any container, and needs the train to be visible, which means it is at your platform. While you are aboard the room description reads "You are in a steam train" plus the platform or, between stations, "riding in a steam train through the picturesque English countryside". GET OUT OF TRAIN is refused between stations (the message is YOU CANNOT GET OUT OF THE STEAM TRAIN.); at a platform it works. Characters who follow you, such as Watson and Lestrade, climb in after you with the "follow" script (#R$E476), and a train that carries Lestrade is described with him in it.</p>

<h3>Hansom cabs</h3>
<h4>Where a cab is, and how it is hailed</h4>
<p>At the start of the game both cabs are off stage, in room 0. The HAIL action (#R$E2C7, shared action #R$AA71 entry 11) works only if all of these hold (the pre-check at #R$E298):</p>
<ul>
<li>the direct object is cab 30 or cab 33;</li>
<li>the room you are in is one of the ten cab stands, which means there is a cab journey from here (#R$9C07);</li>
<li>the cab is in room 0, so it is not already on a job; and</li>
<li>the cabbie is free (#R$CFB9).</li>
</ul>
<p>The action then puts the cab in your room (#R$DD0E), remembers which cab it is (#R$E2C6), and starts the cabbie on the fare script at #R$F2B6 with you and the cab as its two objects (#R$E2EE).</p>

<h4>What the cabbie does</h4>
<p>The cabbie is an actor with the script at #R$F2B2. Its first two instructions are a <code>PASS</code> and a <code>GOTO</code> back to itself, so an unhailed cabbie does nothing for ever. HAIL gives him a second entry point to run, with these stages:</p>
<ol>
<li><b>Greeting and waiting.</b> He says GOOD MORNING GUV'NOR (#R$6BAC) and starts a countdown of 4 minutes plus a random 0 to 4 (#R$E52F). Each minute he checks whether you are there (#R$F2C2); if you are, he moves on to the next stage. If you are not, he ticks the countdown (#R$E57A), and when it runs out he prints WITH A PRACTISED FLICK OF THE REINS, YOU MOVES ON DOWN THE STREET IN SEARCH OF OTHER FARES. (#R$6BF6) and puts the cab back in room 0 (#R$F376).</li>
<li><b>Waiting for a destination.</b> While you are there he waits for a "go to" order, re-asking WELL ARE WE GOIN' ANYWHERE GUV'NOR? (#R$6C1B) whenever a countdown (5 plus a random 0 to 3 minutes) runs out, and then starting again from the first stage. An order is SAY TO CABBIE "GO TO ..." or "GO FURIOUSLY TO ...".</li>
<li><b>The ride.</b> See below.</li>
<li><b>Payment.</b> When the ride ends the cabbie names the fare (RIGHT GUV'NOR THAT WILL BE 10D., #R$E6BC). If you stay in the cab without paying he repeats it about every six minutes (a countdown of 5 plus a random 0 to 2 minutes), and the cab never drives off with you. If you get out without paying the cabbie, who now appears to be getting quite agitated, says WHAT ABOUT ME MONEY GUV'NOR? (message #R$6BC7), and if you then walk away he shouts after you (#R$E70E, message #R$6C54): YOU BLOODY SNOB, WATCH OUT IF WE EVER MEET AGAIN. Then he puts the cab back in room 0 (#R$F376) and goes back to his idle loop. Nothing else follows from not paying: he does not chase you, and nothing in the cabbie's script punishes you further. Once the account is settled, or change is given, the script moves on the same way.</li>
</ol>
<p>Whether a fare is owed is kept in the cabbie's purse: the ride makes his balance negative by the fare, so "negative" means a fare is owed, "positive" means change is due and zero means settled (#R$E63E, #R$E654, #R$E66F).</p>

<h4>The ride</h4>
<p>A ride is two shared actions, one for each speed. GO TO (#R$9AF4, shared action 14) and GO FURIOUSLY TO (#R$9AE1, shared action 15) both do the same things:</p>
<ol>
<li>Check that the cab can get there from where it stands (#R$9B50): look for a journey between the two rooms in the journey table (#R$9B7F, searched either way round by #R$9C07). If there is none, the cabbie says SORRY GUV'NOR I CANNOT GET THERE FROM 'ERE.</li>
<li>Price the ride (#R$9B25): the fare is the rate times (the journey's minutes divided by 5, rounded down, plus 1). GO TO charges 2d a step and GO FURIOUSLY TO 6d. Baker Street to Parliament Street is 20 minutes, so 2 &times; 5 = 10d. The fare is taken off the cabbie's purse.</li>
<li>Set the length of the action to the journey's minutes. Going furiously takes two minutes off, so the ride is two minutes quicker but three times dearer.</li>
<li>Put the cab in room 1 (the hansom cab) and make it invisible (#R$9C60), then hand the ride to the vehicle sub-script at #R$F3AD, which, when the minutes have passed, moves the cab and everything in it to the destination (#R$9C41) and makes it visible again.</li>
</ol>
<p>So a cab ride does not pass through the streets in between: the cab sits in room 1 for the journey time, then appears at the destination.</p>

<h4>The journey table</h4>
<p>There are ten cab stands, all street rooms, and every pair has an entry: 45 in all (#R$9B7F). Leatherhead and Old Mill Road are not in it. They are reached by train and by the police cab. The minutes for each pair:</p>
<table class="sherlock">
%s
</table>
<p>Fares at the normal rate are 2d for each full five minutes plus 2d: 3 minutes costs 2d, 6 to 9 minutes 4d, 20 minutes 10d, 30 minutes 14d.</p>

<h4>The police cab</h4>
<p>The police cab (thing 109, with the room 105 inside) is driven by the local police man and has only three routes (#R$9AA3): Old Mill Road to Main Street, Main Street to Old Mill Road and Main Street to Kings Cross Road. A plain GO TO (#R$9A99) takes 20 minutes longer than GO FURIOUSLY TO (shared action 2): the run out to Old Mill Road takes 114 minutes by plain GO TO and 94 going furiously. It is the only way to Old Mill Road, which is why the endgame needs it.</p>

<h3>Do cabs move when they are not hailed?</h3>
<p>No. A cab that has not been hailed is off stage in room 0 and cannot be seen or reached. Its cabbie runs the do-nothing loop at #R$F2B2, so no cabbie ever leaves on his own and no cab ever wanders the streets. The same holds after a ride: when the fare has been dealt with the cab goes back to room 0. A cab is only ever in a street because someone hailed it, and that someone can be a character as well as you: Lestrade hails cab 30 at the start of the game (the action is the same HAIL, run by actor 2) and rides it from Parliament Street to Kings Cross Road, arriving at about 8:16am, after which the cab goes back to room 0. Other characters use cabs the same way: Phipps and the Major each run the cab-hailing sub-script in their own plans, and the German agent runs Phipps's flight code, which includes it, and Lestrade's own cab sub-script is at #R$EBA4. Cab 33 stays in room 0 until somebody hails it.</p>
<p>The trains are different in exactly this respect: they never stand idle, and a train you cannot see (between stations, or at a platform in another part of London) is still running its script.</p>
'''

page('trains-cabs', 'Trains and cabs',
     _HTML % (_L1, _P1, _L2, _P2,
              _ug_rows(_UG1, [16, 20, 26, 30]), _ug_rows(_UG2, [21, 17, 31, 27]),
              _LL, _PL, _ug_rows(_LH, [23, 22, 54, 55]), _matrix()))
