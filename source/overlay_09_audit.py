"""Comment audit, 9 November 2026: add what the unpoked playthrough showed to
the blocks it touched. Everything here was seen in the emulator by typed
commands (v11_full_win.cmds, v12_clean_win.cmds, endings/)."""
from build_skeleton import A

def add(addr, *paras):
    A[addr]['desc'].extend(paras)

add(0x9CA2,
    "Played, Wednesday morning: with the player waiting outside, the "
    "note is revealed at 10:05am, the countdown $9CA1 (15 at the start) falls "
    "once a minute and reaches 0 at 10:24am. A plain TAKE of the note runs the "
    "shared TAKE script at $DF7E, which sets the countdown to $FF (stopped) "
    "and renames the note SINGE, so it can be examined and used as evidence; "
    "TAKE NOTE FROM FIREPLACE does not run that script and the note still "
    "burns away.")
add(0xDF7E,
    "Played: DROP BURN NOTE then a plain TAKE BURN NOTE runs this script - the "
    "countdown $9CA1 goes to $FF and the note is called SINGE; EXAMINE CLOSELY "
    "SINGE NOTE then counts as examining it. TAKE NOTE FROM FIREPLACE takes the "
    "note through a different action and leaves the countdown running. Note "
    "that typing BURNING NOTE is read as BURNT (the dictionary shares BURN), "
    "so the note must be called BURN NOTE until it is singed.")
add(0xE370,
    "Played: PAY 10D TO CABBIE takes 10d from the purse (thing 27) and the "
    "cabbie pays the change back ('You pay 10d. To the cabbie. The cabbie "
    "pays 8d. To you.'); a paid cab then leaves, an unpaid one waits. The "
    "default GIVE TO ($DF02) moves the whole purse instead.")
add(0xDF02,
    "Played: GIVE MONEY TO CABBIE hands over the entire purse (thing 27): "
    "INVENTORY shows no money afterwards and the cabbie keeps asking for his "
    "fare. Use PAY n TO instead ($E370).")
add(0xF2B2,
    "Played: the cabbie takes the quotation at the head of the list ($9FEC), "
    "not necessarily the one just typed (see $B01C: a failed SAY leaves its "
    "quotation behind), starts the journey, and waits for his fare at the end "
    "of it; the fare is 2d plus 2d for each full five minutes, change is "
    "given. Two cabs may stand in Parliament Street; if the player boards "
    "the one Lestrade is in at the same time, Lestrade's own cab script "
    "($EBA4) and the player's ride collide and he stays in the cab for good.")
add(0xEB72,
    "Played: this journey collides with the player's own cab ride if the "
    "player is in the same hansom cab when Lestrade hails it (Tuesday about "
    "12:20am and 7:05am, Wednesday after the sale statement): in the first "
    "trials Lestrade stayed in cab 33's off-stage room (pc $EBC5) for the "
    "rest of the game. Hail the other cab, or take the train.")
add(0xEE2B,
    "Played, Wednesday morning with the player outside in Camden Street or "
    "in Basil's front yard: Phipps is in the bedroom (room 35) through the "
    "night, in the hall (33) at 10:06, in Camden Street (32) at 10:09 and in "
    "his cab (room 1) at 10:15 - the same whether the player is in room 102 "
    "or in the street. The 9:55am in the earlier phipps_route.py log came "
    "from a run with five-minute WAITs and nothing done in the case, and was "
    "not reproduced. At 9:50am he shoots whoever is in the bedroom, in disguise "
    "or not.")
add(0xE7E7,
    "UPDATE, 9 November: the winning line described above, and every other "
    "ending named in this block, has since been reached by typed commands "
    "only, from a fresh boot, with nothing poked (tools/experiments/"
    "playthrough/v12_clean_win.cmds and endings/*.cmds). The order that "
    "matters on Wednesday: THE SALE LOCATION IS OLD MILL ROAD said at "
    "10:53am; hansom cab (not Lestrade's) to Kings Cross Road; noon train; "
    "out at platform one; police cab at 1:37pm in the minute Lestrade "
    "boards; at 4:56pm on platform two SAY TO LESTRADE \"FOLLOW ME\" once; "
    "police cab GO FURIOUSLY TO KINGS CROSS ROAD (74 minutes); the 6:29 "
    "train from Kings Cross platform one, boarded in the minute it is in, "
    "so that Lestrade (who follows a turn behind) is aboard; Victoria "
    "platform one at 6:41.")
add(0x9E48,
    "Played, 9 November: reached by typed commands only (no poke), "
    "with Watson and Lestrade aboard the 6:29 underground train. With Lestrade "
    "left on the platform the same room and minute give 'With his usual skill "
    "his first shot disposes of you.' instead (endings/end5_victoria_without_"
    "lestrade).")
add(0xB01C,
    "Played: each quotation in a SAY TO / TALK TO is added to the list at $9FEC "
    "($B049) whether or not the command later succeeds; $B86A hands on the "
    "first node. A SAY that failed (I SEE NO ... THAT YOU CAN TALK TO, no "
    "answer) therefore leaves a stale quotation in front of the next one, "
    "and the next person spoken to hears the old words. TALK TO <person> "
    "with no quotation empties the list (2 nodes to 0 in the emulator).")

add(0xE7E7,
    "Played, 9 November (tools/experiments/playthrough/endings/end6_* and end7_*): "
    "left alone on platform two at 4:55pm Lestrade says 'has eluded us Holmes' at 4:56 and takes the "
    "6:15pm train (script $EBF1), reaches platform four at 7:31, Kings Cross Road at 7:41, a hansom cab "
    "at 7:46, Parliament Street at 8:01 and Scotland Yard at 8:06pm (script $EA99, which then waits for "
    "10pm; $EAAD puts him off stage at 10:01pm). The speech is only printed if you are in the room: "
    "riding the same train and cab and walking EAST into Scotland Yard at 8:02pm, you hear 'I am afraid "
    "that Basil has eluded us Holmes.' at 8:04pm. At Thursday 10:00am the script is at $EAB3 and the "
    "papers ending fires (end7_eluded_at_scotland_yard). Observed, not just read from the code.")

add(0xEE2B,
    "Why Phipps's Wednesday morning differs between logs (9 November): at $EEE9 his script tests "
    "whether you are in Camden Street or Basil's front yard, or the china man is in either. If so he "
    "plays the messenger scene ($EFAC) and waits 15 minutes before leaving the bedroom; if not he "
    "goes at once. With the player indoors he is in Camden Street at 9:55am; with the player in the "
    "front yard, as in the winning route, about 10:06-10:10.")

from build_skeleton import fact
fact('messenger-note-watched',
     'The messenger who delivers a note to Basil is shown only if you are watching',
     "On Wednesday morning, at about 9:50, Phipps's script ($EEE9) checks whether you are in "
     "Camden Street or Basil's front yard (or the china man is). If so it prints 'A messenger "
     "arrives at the door, gives a note to Basil and dissapears down the street.' (the typo is the "
     "game's) at 9:51-9:55, and Phipps then waits 15 minutes before leaving the bedroom (hall at "
     "about 10:06, street 10:10, cab 10:15). With you elsewhere he skips the scene and is in Camden "
     "Street at 9:55. Seen in the emulator on 9 November from the winning route's Tuesday-night "
     "position (window of Basil's house) against a plain WAIT run from the sitting room. The note "
     "Basil is given is presumably the one you later find burning in the bedroom (revealed at "
     "10:05am); the link was not traced.")

fact('lestrade-orders-tried',
     'Which orders Lestrade takes on platform two (and when)',
     "Played on 9 November from Wednesday 4:55pm on Leatherhead platform two, after the chase. "
     "SAY TO LESTRADE \"WAIT\" gets 'Inspector Lestrade waits.'; \"FOLLOW ME\" makes him follow "
     "(he and Watson trail one turn behind). \"GO TO VICTORIA\", \"GO TO PLATFORM ONE\" and \"GO "
     "SOUTH\" are accepted as speech ('You talk to Inspector Lestrade.') and then nothing happens. "
     "FOLLOW ME at 4:54pm, a minute too early, gets 'Inspector Lestrade says \"Sorry, I cannot do "
     "that now.\"' because his script is still busy getting to the platform; from 4:56 he takes "
     "orders. So there is no way to send him to Victoria ahead of you: he has to be walked there "
     "with FOLLOW ME, and no second structurally different winning route was found in the time spent looking; "
     "that is a statement about the search, not a proof that none exists.")

# ---- Postconditions checked while the route is typed (tools/experiments/probe_routines.py) ----
for _a, _n, _t in ((0xA2B1, 2033, "HL = $8259 + 8 x (A - 1)"),
                   (0xA2AB, 1326, "the B bytes at HL are zero afterwards"),
                   (0xAEA9, 320, "IY = the link word before the node"),
                   (0xA11C, 2957, "the block from IX-2 for A+2 bytes is zero, IX is non-zero, and the size byte at IX-3 is A+3"),
                   (0x9CCE, 4172, "Z only when the thing's room equals the actor's room")):
    add(_a, "Checked 9 November over the first 120 commands of the winning route: %d runs, "
            "every one met its stated postcondition (%s)." % (_n, _t))

# (the 'Coverage' notes that stood here were replaced by overlay_10_traced.py, which has instruction coverage)

fact('second-winning-route',
     'A second winning route: shadow Lestrade from Scotland Yard',
     "tools/experiments/playthrough/v13_shadow_lestrade.cmds (368 lines) wins too. It matches the "
     "cleaned route up to the sale-location statement to Lestrade (Wednesday 10:53am), then, instead "
     "of taking a hansom cab of your own and the noon train from platform four, you go WEST to "
     "Parliament Street, CLIMB INTO HANSOM CAB while Lestrade is in it (he has hailed it at 10:54 and "
     "climbed in at 10:56; you climb in at 10:57 and Watson follows), reach Kings Cross Road at 11:11, "
     "walk NORTHEAST to platform three, and board the steam train that enters at 12:15pm when "
     "Lestrade does. It reaches Leatherhead platform one at 1:30pm, the same minute as the other "
     "route, and everything after that is the same. The first route is therefore not the only one; "
     "what is common to both is the chain of statements and evidence, the 1:37pm police cab with "
     "Lestrade, the FOLLOW ME on platform two at 4:55-4:56, the 6:29 underground train with both "
     "Lestrade and Watson, and Victoria at 6:41.")
