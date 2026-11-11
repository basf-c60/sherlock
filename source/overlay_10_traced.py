"""Pass over every block that was marked 'Not traced' (9 November 2026).

The label had two causes. Most of the action records carried a generic line added by a script ('Found as an
action record by tools/allplans.py ... Not traced.') that said where the record was found, not what it does; the
rest were routines whose purpose was read but not checked. For each of the 57 blocks this overlay

  * removes the generic line and any 'not traced' wording,
  * says what the block does, from its code,
  * adds what was seen in the emulator: how often the body ran in the 15 stored routes and who ran it
    (tools/experiments/record_coverage.py), what it changed (record_effects.py), and which of its instructions
    ran at all (insn_coverage.py), merged into source/record_evidence.json by make_record_evidence.py,
  * and records the targeted tests (tools/experiments/untraced_tests.py) for the records no stored route runs.

What is still not known is said in one specific sentence per block rather than by the old label.
"""
import json, os, re
from build_skeleton import A, C

_EV = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'record_evidence.json')))
ROUTES = 15


def _evidence(addr, extra_ran=(), actors=True):
    """The sentence built from the merged measurements."""
    parts = []
    r = _EV['records'].get(str(addr))
    if r:
        who = sorted(r['actors'].items(), key=lambda kv: -kv[1])
        names = ', '.join(n for n, _ in who[:4]) + (' and others' if len(who) > 4 else '')
        parts.append("Seen in the emulator (9 November, tools/experiments/record_coverage.py over the %d stored routes): "
                     "the body ran %s times in %d of them%s." % (ROUTES, format(r['runs'], ','), r['routes'],
                                                                  (', run by ' + names) if actors else ''))
    c = _EV['insn_coverage'].get(str(addr))
    if c:
        total, hit, miss = c
        hit_all = [m for m in miss if m not in set(extra_ran)]
        if not hit_all:
            parts.append("Every one of its %d instructions was executed (tools/experiments/insn_coverage.py%s)." %
                         (total, ' plus the targeted tests described above' if extra_ran else ''))
        else:
            parts.append("%d of its %d instructions were executed; the rest (%s) never ran in any stored route%s." %
                         (hit, total, ' '.join('$%04X' % m for m in hit_all[:10]) + (' ...' if len(hit_all) > 10 else ''),
                          ', and were therefore read from the code only'))
    return ' '.join(parts)


def tidy(addr, title=None, text=(), ran=(), evidence=True, actors=True):
    d = A[addr]
    keep = []
    for p in d['desc']:
        if 'Found as an action record by tools/allplans.py' in p or 'Found as the target of a plan script (tools/allplans.py)' in p:
            continue
        if p.startswith('Coverage, 9 November: the winning route'):
            continue
        p = re.sub(r'\s*Not traced( in detail| line by line)?\.', '', p)
        p = p.replace('(not traced)', '').replace(' ,', ',')
        if p.strip() and p.strip() != '.':
            keep.append(p)
    # a lone '.' paragraph separator left at the end is dropped
    while keep and keep[-1].strip() == '.':
        keep.pop()
    for t in text:
        keep.append(t)
    if evidence:
        e = _evidence(addr, ran, actors)
        if e:
            keep.append(e)
    d['desc'] = keep
    if title:
        d['title'] = title


# ---------------------------------------------------------------------------------------------------------
# Routines (not records)
# ---------------------------------------------------------------------------------------------------------
tidy(0xA5C4, text=[
    "Only the driver loop: $A5CD does the work for each element of the message (its own block, with the "
    "element types listed there). Every message the game prints goes through here."], actors=False)

B98C_TAIL = [47532,47535,47537,47538,47540,47543,47544,47546,47550,47554,47557,47559,47593,47594,47596,47600,47602,47604]
tidy(0xB98C, ran=B98C_TAIL, text=[
    "Reached from $B936 when an actor has been given an order (ASK): the order's verb and objects are turned "
    "into the command the actor will run and the order is removed from the list. Orders are issued by ASK instructions "
    "in the scripts - for example Lestrade's own script at $EA6D, ASK the local policeman TO GO FURIOUSLY TO "
    "Tricia's front door - and the block ran in the stored routes (count below). ",
    "The tail from $B9AC drops an order's sentences when the order cannot be parsed or an ALL has run out, and "
    "$B9CA hands back the remark's remaining words one sentence at a time. It never ran in the stored routes, "
    "so it was provoked on 9 November (tools/experiments/tails_test7.py: orders typed as SAY TO LESTRADE \"...\", "
    "with the player put in Lestrade's room): WAIT and GO EAST - an order he cannot carry out - go $B9B4, $B9AC, "
    "$B9CA and he says 'Sorry, I cannot do that now.'; TAKE ALL and DROP ALL, whose ALL has run out, go $B9B4, "
    "$B9BA, $B9CA ($B9BE-$B9C5 on the way); WAIT AND WAIT and GO EAST AND GO EAST drop the first sentence and go round "
    "again ($B9E9, $B9F2, back to $B9AC); TAKE ALL AND WAIT goes through $B9C7 to try the next sentence; and "
    "HELLO AND GOODBYE (which is not an order but speech) goes through $B9CA, $B9E9, $B9F2 and he answers only the "
    "first sentence. Every instruction of the tail has now run."], actors=False)

tidy(0xBB67, text=[
    "Played, 9 November (a fresh replay of the winning route to Scotland Yard at 1:58pm on Tuesday, then "
    "sentences typed to Inspector Lestrade; the reply and the branch taken are given for each): "
    "MRS BROWN KILLED HERSELF - 'So Mrs Brown killed herself, excellent Holmes, another brilliant conclusion' ($BBE5, "
    "the statement is proven); MRS JONES KILLED TRICIA FENDER - 'Brilliant Holmes, I do not know how you do it' and "
    "Mrs Jones is led away; BASIL KILLED MRS BROWN, BASIL HAS THE PLANS and THE SALE LOCATION IS OLD MILL ROAD before "
    "the evidence is in - 'I do not believe that you have the evidence to prove that ...' ($BBC4, $72A6); "
    "TRICIA FENDER HAD PLANS - 'I do not see the importance of that'; BASIL KILLED WATSON, WATSON KILLED MRS BROWN, "
    "WHAT HAPPENED and THE PLANS ARE IN THE DRAWER - the stock reply 'That may well be, Holmes, I will think about it' "
    "($BB87, $725F); a sentence with a word the game does not know is refused before it gets here "
    "(I DO NOT KNOW THE WORD). A plain HELLO does not come here at all: Lestrade answers 'Good afternoon' "
    "through $9A80.",
    "Branches reached later the same day (tools/experiments/tails_test.py to tails_test6.py, same set-up: the "
    "player put in Lestrade's room, then remarks typed): BASIL KILLED - a statement that stops after the verb - goes to "
    "$BBBE and Lestrade says 'What' ($7243). MAJOR FFOULKES VISITED THE OPIUM DEN with the Major's confession "
    "already poked in (bit 1 of $9972) and nothing else waiting goes through the summary at $BBC9, finds nothing "
    "unprovable and nothing newly provable ($BBD3), and Lestrade says 'Thats fine Holmes but what does it prove' "
    "($727E at $BBDE). The same remark after TRICIA FENDER KILLED MRS JONES has been told (and left waiting) finds one "
    "newly provable statement ($BBD9): 'That is well and good, but I do not see how it proves that Tricia Fender killed "
    "Mrs Jones' ($72BD). After MAJOR FFOULKES IS INNOCENT is left waiting the same remark proves it and "
    "Lestrade says 'Very good Holmes, I shall return to Leather head tomorrow...', through $BBE5.",
    "Still not seen: $BBFB-$BC17, which names a statement with flags bit 4 that is still waiting. Only the four "
    "flags-$B4 statements (Tricia Fender or Phipps killed Mrs Brown or Mrs Jones) have that bit, and each has a "
    "child record that asks only that thing 0, the player, has been seen. They were always found provable, even in a "
    "run that cleared bit 7 of the player's +6 before the check ($BBD9 was taken instead), so no sentence that "
    "can be typed has been found to reach it, and I have not worked out why the poke made no difference. "
    "Those 12 of the routine's 93 instructions are read from the code; the other 81 have run, 66 of them in the stored routes."], evidence=False, ran=[a_ for a_ in (48007,48010,48013,48062,48065,48083,48086,48087,48089,48092,48094,48097,48100,48123,48175,48176)])

tidy(0xCC78, text=[
    "Instruction coverage, 9 November: 73 of this routine's 75 instructions were executed over the 15 stored "
    "routes, including the order path $CCAE-$CCC6 (an actor who has been given an ASK order). The two that never "
    "ran, $CC98 and $CC99, skip a zero byte - a spent one-shot instruction - and no script in the game uses "
    "one-shot instructions."], evidence=False)

# ---------------------------------------------------------------------------------------------------------
# The player's own script: the turn loop at $9921
# ---------------------------------------------------------------------------------------------------------
_PLAYER = ("This record is one step of the loop in the player's own plan script at $9921: DO LOOK once, then "
           "read a line ($D6BF), split it into words ($D715), check there is a word ($D769), parse a sentence "
           "($D77E), check there is a sentence ($D7D9), turn it into a command ($D7FA) and DO it. "
           "When you wear the china man's disguise the same script runs for him; the counts below include both.")
tidy(0xD6BF, title="Player's turn: read a line from the keyboard (RUN at $9923)", text=[_PLAYER])
tidy(0xD715, title="Player's turn: split the typed line into words (RUN at $9928)", text=[_PLAYER])
tidy(0xD769, title="Player's turn: stop when the line has no more words (RUN at $992D)", text=[
    "Its body just succeeds; the work is its pre-check ($D770), which fails when the next token is the end of "
    "the line (class $C0). " + _PLAYER])
tidy(0xD77E, title="Player's turn: parse the next sentence (RUN at $9932)", text=[_PLAYER],
     ran=())
tidy(0xD7D9, title="Player's turn: another sentence waiting? (RUN at $9937)", text=[
    "Its body just succeeds; the pre-check at $D7E1 fails when the last sentence did not parse (and throws "
    "the rest of the line away) or when there is no sentence left. " + _PLAYER])
tidy(0xD7FA, title="Player's turn: turn the sentence into a command (RUN at $993C)", text=[
    "Tried 9 November: TAKE ALL (the 'ALL has run out' failure at $D865), TAKE ALL BUT LAMP (the BUT chain "
    "$D84F-$D856) and DROP ALL BUT LAMP both reached the paths that the stored routes do not. " + _PLAYER],
     ran=(0xD84F, 0xD850, 0xD852, 0xD856, 0xD865, 0xD867, 0xD86A, 0xD86D))
# D77E: parse result 2 (D7D0-D7D6) stays unreached
A[0xD77E]['desc'].append("The 'parser result 2' tail ($D7D0-$D7D6) was not reached by any stored route or by "
                         "the keyboard tests (TAKE alone, BLAH, GO BLAH); BLAH and GO BLAH give I DO NOT KNOW THE WORD "
                         "before this record is run, and TAKE alone gives TAKE WHAT ?.")

# ---------------------------------------------------------------------------------------------------------
# Verb defaults
# ---------------------------------------------------------------------------------------------------------
tidy(0x9A7E, text=[
    "The record is only its two header bytes: HELLO has no body of its own, and the code that follows at $9A80 "
    "is what runs. Played: HELLO by itself prints 'HI.' and takes no time; SAY TO WATSON \"HELLO\" makes Watson "
    "answer 'Watson says \" Good morning \"'. In the stored routes this body ran 11 times, all with Chief "
    "Constable Straker as the actor."], evidence=False)

tidy(0xDC19, title="Action record: default for verb 35 (LOOK THROUGH)", text=[
    "Tested 9 November (tools/experiments/untraced_tests.py, in the sitting room): LOOK THROUGH WINDOW gets "
    "'YOU CANNOT LOOK THROUGH THE WINDOW', LOOK THROUGH YOUR DOOR with the door shut gets 'YOU CANNOT LOOK THROUGH "
    "YOUR DOOR', and after OPEN YOUR DOOR it prints 'You look through your door. You can see a hall.' - this is the "
    "only way found to run the body, so the door must be open. No stored route uses LOOK THROUGH."],
     ran=tuple(range(0xDC20, 0xDC4E)))

tidy(0xDC57, text=[
    "GO THROUGH <door>. The characters use it constantly - Chief Constable Straker, the cook, the gardener, Lestrade, "
    "the local policeman, Phipps and others walk through doors with it - and the player can too (tested 9 "
    "November: with the door shut, GO THROUGH YOUR DOOR gets 'I SEE NO YOUR DOOR THAT YOU CAN GO THROUGH'; after "
    "OPEN YOUR DOOR it prints 'You go through your door.' and describes the hall). The verb becomes a GO in the "
    "door's direction. In the runs sampled the actor's room (+15) changed to the room on the other side of the door "
    "(Lestrade through the solid door, room 94 to 97; Straker through the large oak door, 63 to 64)."])
tidy(0xDC7B, text=[
    "LOOK: a new line, then the full description of the room the player is in. It runs for the player and for "
    "the china man (the disguise), and does nothing for other actors (the pre-check at $DC6C passes only actors "
    "0, 1 and $64 - you, the china man and the old man)."])
tidy(0xDC8D, text=[
    "Seen: DROP CRUMPLED NOTE and DROP BURN NOTE by the player, DROP BODY by the local policeman - in each the "
    "dropped thing's holder (+1) went from 0 (the player) or the policeman to $FF (lying in the room)."])
tidy(0xDD03, text=[
    "Seen in the emulator: every compass move by every character, including the cook (EAST and WEST between "
    "rooms 65 and 68), the gardener (NORTHWEST, SOUTHWEST, NORTHEAST ...) and the player. In the sampled runs "
    "the mover's room (+15) is set to the destination and nothing else changes. $DD1D, if it ever ran, would "
    "turn a destination of $FF into room 0."], actors=False)
tidy(0xDD61, title="Action record: find the exit to a room next door (RUN at $DD54)", text=[
    "The pre-check takes the direct object as a room number, finds the exit from the actor's room to it ($D471) and "
    "refuses if there is none or if the exit is not a plain movement direction (a value below 11); the body stores that "
    "direction in plan register $9FD7. Used by the walk-to-a-room sub-script at $DD52, which then DOes the "
    "direction. Seen: Watson, Lestrade and Straker walking between rooms - the register held, for example, 1 "
    "(north), 2 (south) or 4 (west)."])
tidy(0xDD84, title="Action record: remember what holds the direct object (RUN at $E476, $E7CF)", text=[
    "Puts the direct object's holder (+1) into plan register $9FD6; the pre-check refuses if nothing holds it ($FF). "
    "Used by the follow loops of Watson ($E456) and Lestrade ($E72F): when the person they follow is in a cab "
    "or train, the register holds that vehicle and the next step is DO CLIMB INTO it. Seen: Watson climbing "
    "into the cab you climbed into (the register held that cab's number), Straker climbing into Lestrade's police "
    "cab (thing 109) and Lestrade into yours."])
tidy(0xDD9E, text=[
    "TALK TO: passes the quoted words to $B86A with A = 1 when the person spoken to is an actor with a record, 0 "
    "otherwise, and succeeds. Seen when SAY TO LESTRADE, CABBIE, MRS JONES, TRICIA FENDER and WATSON were typed "
    "('You talk to Watson.')."])
tidy(0xDDB4, text=[
    "WAIT HERE: byte 1 is $50, and the player's WAIT moves the clock on by five minutes. Body and pre-check are "
    "the same three instructions at $DDB8: refuse if the actor is busy ($CBA7), otherwise succeed. The "
    "record at $DDBE (wait a given number of minutes) uses this code as its pre-check as well."])
tidy(0xDE6F, text=[
    "INVENTORY: prints 'You are carrying' and the list of what the actor holds ($D4CC, $D51A), or 'nothing'. "
    "Played 9 November: after DROP ALL, 'You are carrying nothing' (the $DE86 branch); in the old man's "
    "disguise, 'An old man is carrying nothing'."], ran=(0xDE86, 0xDE89, 0xDE8B))
tidy(0xDF40, text=[
    "Seen: the player's EXAMINE marks the thing as seen (+6 bit 6 goes from 0 to 1 - the female corpse, the burning "
    "note); Lestrade's script also examines things (the deep stream, the sandstone bridge, the sofa, the bookcase, "
    "the corpse); the body prints a description only for you, the china man and the old man ($DC6C), so for him "
    "it prints nothing."])
tidy(0xE135, text=[
    "Seen: the thing is marked as seen (+6 bit 6) when examined closely - the sandstone bridge, the crumpled note, "
    "the body, the bloodstained clothes. The table at $E16B is data (thing, message pairs) that the disassembler "
    "listed as code, which is why the last 12 'instructions' were not executed."], ran=())

# ---------------------------------------------------------------------------------------------------------
# Scripts' actions: notes, safes, examining
# ---------------------------------------------------------------------------------------------------------
tidy(0xDF8B, title="Action record: singe the note when it is picked up (RUN at $DF85)", text=[
    "The tail of the shared TAKE script at $DF7E. If the burning note's countdown ($9CA1) is still running it "
    "is set to $FF (stopped) and the note's name word is changed from BURNING ($0157) to SINGED ($07D5), so the TAKEn note is a "
    "singed note you can examine. Seen on TAKE BURN NOTE: $9CA1 went from 6 (or 4) to 255 and the name word "
    "from $0157 to $07D5."])
tidy(0xDFB6, title="Action record: opening the wall safe on Monday (RUN at $DFAB)", text=[
    "Part of the shared OPEN WALL SAFE script at $DFAB. If the direct object is thing $59 (the wall safe) and "
    "the day is Monday, control passes to $DFCC and Basil shoots you. Any other day it just succeeds. Seen: "
    "OPEN WALL SAFE on Monday (end4a_shot_wall_safe_monday) ended the game; on the other runs (Tuesday) "
    "nothing happened."])
tidy(0xDFCA, title="Action record: Basil shoots you (RUN at $EF99, and from $DFB6)", text=[
    "Game over. If Basil (thing 6, Phipps) is not in the player's room it prints 'Basil enters and says \" Holmes, "
    "your interference is becoming annoying. \" ...' ($759C), if he is it prints the version without 'enters' ($75D2), "
    "then ends the game through $9E74. Reached from the wall-safe script on Monday and from Phipps's wake-up "
    "routine $EFC7 when you are inside his house at that time. The three instructions at $DFE3-$DFE8 belong to "
    "the pre-check of the next record ($DFEA), not to this one."], ran=(0xDFE3, 0xDFE6, 0xDFE8))
tidy(0xDFEA, text=[
    "Shared action 24: TAKE OFF the old man's disguise. The pre-check ($DFE3) lets only the old man (thing $64) "
    "do it; the body jumps to the common tail at $E007. Tested 9 November in the closet (room 9): WEAR OLD MANS "
    "DISGUISE, then TAKE OFF OLD MANS DISGUISE gives 'The old man takes off the old mans disguise.' No stored "
    "route wears the old man's disguise (they use the china man's)."], ran=(0xDFEE,))
tidy(0xDFF0, text=[
    "Shared action 23: WEAR the old man's disguise: A = $64 (the old man, thing 100) and on to the common "
    "tail at $E028. Tested 9 November in the closet: 'You wear the old mans disguise.' After it INVENTORY says "
    "'An old man is carrying nothing' and LOOK 'An old man is in a small closet'; TAKE OFF and WEAR again both "
    "worked."], ran=(0xDFF4, 0xDFF6))
tidy(0xE0AD, title="Action record: Lestrade finds the large rock in the stream (RUN at $E0A2)", text=[
    "The extra step of EXAMINE CLOSELY DEEP STREAM. If the player is in room 88 (the east side of the stream) on "
    "Tuesday, the large rock (indirect object, thing 93) is made visible (+5 and +6 bit 7), put in the player's "
    "room and held by Inspector Lestrade (the direct object): 'As you search the river Lestrade comes over to help. "
    "He stumbles and slid...' ($7B5A). Seen: thing 93 +5 went from $20 to $A0 and +6 from 0 to $80."])
tidy(0xE0EB, title="Action record: the trash pile gives up the torn note (RUN at $E0E7)", text=[
    "Run after EXAMINE CLOSELY TRASH PILE: sets bit 7 of thing 81's +5 (the torn coded note), making it visible. "
    "Seen: +5 went from $00 to $80."])
tidy(0xE0FD, title="Action record: the drawer's false bottom (RUN at $E0F9)", text=[
    "Run after EXAMINE CLOSELY DRAWER: sets bit 7 of thing 63's +5 (the false bottom), making it visible: "
    "'Careful examination shows that the drawer has a false bottom.' Seen: +5 went from $00 to $80."])
tidy(0xE104, title="Action record: the bookcase swings away (shared 18)", text=[
    "EXAMINE CLOSELY BOOKCASE. The first time, the bookcase (thing 66) is marked open (+5 bit 5), its description "
    "message is changed to 'It has been swung away from the wall revealing a small room' ($7BF7), and "
    "'As you run your hands over the books you touch a hidden spring...' is printed ($7C13). Seen: +5 went from $80 "
    "to $A0, +6 from 0 to $40 and the description pointer from 0 to $7BF7."])
tidy(0xE188, title="Action record: Mrs Jones is asked what happened or about her alibi (RUN at $E17D)", text=[
    "If the topic (indirect object) is thing 16 (WHAT HAPPENED), 67 (BLOODSTAINED CLOTHES) or 17 (YOUR ALIBI), bit 1 of "
    "the statement at $9993 is set; Mrs Jones (Tricia Fender in disguise) has then been asked. Seen: $9996 went from 8 to 10 when Mrs Jones was asked about her alibi."])
tidy(0xE1B2, title="Action record: asked about the bloodstained clothes, Tricia Fender becomes Mrs Jones (RUN at $E1A5)", text=[
    "If the topic is thing 67 (BLOODSTAINED CLOTHES) and the actor can see them ($C821), the actor is renamed "
    "thing $5F (Mrs Jones) and bit 1 of the case record at $998F is set (Tricia Fender turns out to be Mrs Jones). "
    "If she cannot see them the refusal at $E1FC is printed. Seen (3 runs): Tricia's id 13 was replaced by 95 in the actor table, $9992 went from 0 to 2, and the two things "
    "swapped places (thing 13's room from 47 to 0, thing 95's from 0 to 47). The 'cannot see them' branch ($E1C0, $E1C3) "
    "was not reached."], ran=())
tidy(0xE1D6, title="Action record: default for TELL and TELL ABOUT (verbs 47 and 48)", text=[
    "The interview table at $E22A: the actor is looked up ($E207), then the topic ($E201); a match prints that "
    "entry's reply ($6830 with the entry's message as its parameter), otherwise 'I AM SORRY I CANNOT HELP YOU WITH "
    "THAT' ($761D). Seen both in the player's questions (Mrs Jones's confession, Tricia's) and in the characters' "
    "own scripts: Strachan, Phipps, the gardener, the maid and the cook each answer Lestrade's TELL ABOUT WHAT "
    "HAPPENED / YOUR ALIBI, and Straker answers about the case."], ran=())

# ---------------------------------------------------------------------------------------------------------
# Money and cabs
# ---------------------------------------------------------------------------------------------------------
tidy(0xE328, title="Action record: shared 10 (COUNT the money)", text=[
    "COUNT: prints 'It totals' and the sum held in the money thing (+9/+10), in pounds, shillings and pence. "
    "Tested 9 November from the start: COUNT MONEY and COUNT YOUR MONEY both print 'You count your money. It totals "
    "\u00a35 4/-' (the game's pound sign is character $60, which my capture shows as a backquote). No stored route "
    "counts money."],
     ran=tuple(range(0xE32C, 0xE345)) + (0xE365, 0xE368, 0xE369))
tidy(0xE370, text=[
    "Tested 9 November: PAY 100D TO WATSON gets 'DON'T BE SILLY.' (the cannot-afford branch, $E365). In the stored "
    "routes it runs for the player paying the cabbie, for Lestrade paying the cabbie, and for the cabbie "
    "paying change back."],
     )
tidy(0xE488, title="Action record: where is the person I follow? (RUN at $E45B, $E7B9)", text=[
    "Puts the direct object's room (+15) into plan register $9FD6. The follow loops of Watson, Lestrade and "
    "Straker use it to know where to walk next."])
tidy(0xE4C9, title="Action record: put a train in a room (internal verb 140, RUN at $F2A7)", text=[
    "The direct object is a room number. The train (the actor) is moved there ($DD0E) and the room record at "
    "$DCFF gets bit 6 cleared. If the room is 2, 3 or 4 (the stretch between stations) 'THE TRAIN PULLS OUT OF THE "
    "STATION.' is printed first. In the sampled runs (the first three of each kind) each of the train things 37 to 41 went "
    "from room 2 to a room of its own (30, 26, 21, 27 and 31) with its +5 bit 7 set; the timetable's later moves "
    "($F278, $F28D) were not sampled."])
tidy(0xE518, title="Action record: pay everything in the purse (RUN at $E508)", text=[
    "Prepares the payment step of the sub-script at $E506. The direct object becomes the number $FE, and the sum "
    "to pay ($A02F) is the whole balance held by the payer's purse (+9/+10) with bit 7 set; the next step, PAY TO "
    "($E370), then hands it over. The cabbie's purse balance is negative while a fare is owed, so paying "
    "'everything' from the cabbie's purse pays the change. Seen: Lestrade paid the cabbie his whole purse "
    "(2,400d, ten pounds) and the cabbie paid the change back; the cabbie did the same for you."])
tidy(0xE5C1, title="Action record: is the player in my room? (RUN at $E781)", text=[
    "Compares the room of the first actor in the table (the player, $9860) with the current actor's and goes "
    "on to $E5F0, which refuses if they differ (and if the actor is the direct object). It is used in Watson's "
    "script (actor 3, $E72F, at $E781)."])
_CAB = ("The cabbie's script at $F2B6 reads the balance of his purse (+9/+10 of the money he holds): negative "
        "while a fare is owed, positive when change is due, zero when settled.")
tidy(0xE63E, title="Action record: is a fare owed? (RUN at $F2D8)", text=[
    "No body; the pre-check passes only if the cabbie holds a purse and its balance is negative (bit 7 of the sum "
    "set) - a fare is owed (my reading of how $F2D8 uses it: the script waits until the record passes). " + _CAB])
tidy(0xE654, title="Action record: is change due? (RUN at $F304, $F31C, $F339)", text=[
    "No body; the pre-check passes only if the cabbie's purse holds a positive sum - change is due to the "
    "passenger. " + _CAB])
tidy(0xE66F, title="Action record: is the account settled? (RUN at $F309, $F321, $F33E)", text=[
    "No body; the pre-check passes when the cabbie has no purse or its balance is exactly zero. " + _CAB,
    "The block also holds two routines that merely follow it in memory ($E686 and $E691): a 50 percent roll "
    "used by Watson's after-turn code, and the remark in which Watson asks 'why do you think that ...?' about a "
    "statement chosen at random from the list of statements already made. Only the empty-list check and the final print "
    "of that remark ($E6A4-$E6B6) were never executed."])
tidy(0xE6BC, title="Action record: the cabbie names the fare (RUN at $F326)", text=[
    "Prints '\"Right guv'nor that will be Nd.\"' using the negative of the cabbie's purse balance. Seen "
    "190 times with you as the passenger, 68 with Lestrade, and with Phipps, the Major and the German agent."])
tidy(0xE6E6, title="Action record: take the passenger in my cab as the one to deal with (RUN at $F2F7, $F35F, $F371)", text=[
    "The pre-check refuses unless the actor is not the direct object and the direct object's holder is one less "
    "than the actor's number - that is, the passenger is inside the cab that the cabbie (thing 31) drives (thing 30). "
    "The body then stores the direct object in +3 of the actor's table record ($CFB6) - the saved direct-object "
    "register of its plan - so the cabbie takes that person as the one he is dealing with. "
    "This body never ran in any stored route or test: its pre-check was reached 29 times in v12_clean_win and "
    "refused each time (the cabbie was its own direct object 19 times, and the passenger was out of the cab, "
    "holder $FF, 10 times). I could not build a situation in which the passenger is still in the cab when the script "
    "reaches it, so the body is read from the code only."], ran=())
tidy(0xE70E, title="Action record: the cabbie's parting shout (RUN at $F35C)", text=[
    "The cabbie's parting shout when a passenger has gone without paying: 'The cabbie shouts \" You bloody snob, "
    "watch out if we ever meet again ... \"' ($6C54). Seen in end4b, after Major Percival Ffoulkes climbed out of "
    "the cab unpaid ('What about me money guv'nor?' repeated first). The record reads +3 of the actor's table "
    "record (the saved direct-object register, $CFB6): if it is non-zero it prints the shout; if it is zero it "
    "sets the ROM variable $5C3C to 1 first and then prints (what that does to the print was not tested; "
    "$E720 and $E722 never ran). When I climbed out unpaid myself in a test the cabbie only repeated 'What about "
    "me money guv'nor?' for the next seven hours, so the route to the shout is not simply 'leave without paying'."])

# ---------------------------------------------------------------------------------------------------------
# Lestrade, Straker, Phipps, the Major
# ---------------------------------------------------------------------------------------------------------
tidy(0xEAF6, title="Action record: Lestrade puts the policeman into the police cab (RUN at $EA5F)", text=[
    "The direct object (the police cab) becomes the holder (+1) of the indirect object (the local policeman) "
    "and both are placed in room $32 (50, the main street). Seen: the policeman's holder went from 255 to 109 (the "
    "police cab) and his room, and the cab's, from 0 to 50."])
tidy(0xEB19, title="Action record: has Lestrade's statement been proven? (RUN at $EA2C)", text=[
    "Tests bit 1 of the case record at $9997 and returns NZ if it is set. Lestrade's script at $EA25 waits "
    "here until it is."])
tidy(0xEBD5, title="Action record: remember which cab is meant (RUN at $EBAA, $EBBB)", text=[
    "Puts the direct object's number plus one into plan register $9FD6. In the cab-hailing sub-script at $EBA4, "
    "which Lestrade, Phipps, the Major and the German agent each run when they take a cab, it names the "
    "cab they have just hailed."])
tidy(0xED39, title="Action record: Straker revives the policeman (RUN at $ECBB)", text=[
    "Straker's script prints 'Seeing the unconscious police man, you attempt to revive him' ($6D6A) and sets the "
    "policeman (thing 11): state word LOCAL ($050B, so he is the LOCAL POLICE MAN again), +8 high nibble 1, and "
    "+5 bit 6 set again (a person who can be spoken to). Seen: +10/+9 went from $0910 (UNCONSCIOUS) to $050B, and "
    "+5 from $A0 to $E0."])
tidy(0xEF9C, title="Action record: the first messenger takes a note from Basil (RUN at $EE95)", text=[
    "Prints 'A messenger arrives at the door, takes a note from Basil and dissapears down the street.' ($75E8). "
    "It is run by Phipps's script at $EE95 on Tuesday at 1pm, only when you (or the china man) are in Camden "
    "Street or Basil's front yard (rooms 32 and 102). No stored route is there at that hour, so I tested it on 9 "
    "November (tools/experiments/untraced_tests.py, part E): I replayed the winning route to Tuesday 12:30pm in "
    "Kings Cross Road, moved the player to Camden Street by writing the room number into memory (the only poke "
    "in this pass) and typed WAIT: at about 1:00pm the message was printed. Its sibling at $EFAC (Wednesday 9:50am) "
    "ran in the stored routes."],
     ran=(0xEF9E,))
tidy(0xEFAC, title="Action record: the second messenger gives a note to Basil (RUN at $EF01)", text=[
    "Prints 'A messenger arrives at the door, gives a note to Basil and dissapears down the street.' ($7603), "
    "with the same output switch setting as $EF9C. Run by Phipps's script at $EF01 on Wednesday morning "
    "when you or the china man are outside, which is why it appears in the winning route."])
tidy(0xEFB3, title="Action record: Phipps goes to sleep (RUN at $EE3D, $EEBB)", text=[
    "Sets the actor's state word to SLEEPING ($07F0), the high nibble of +8 to 1, and clears bit 6 of +5 "
    "(not a person any more), through $F1C1. Seen: thing 6 (Phipps) +9/+10 went from 0 to $07F0, +8 from $86 "
    "to $16 and +5 from $E0 to $A0."])
tidy(0xEFC7, title="Action record: Phipps wakes at 7 - or shoots you if you are in the house (RUN at $EE46, $EEC3, $EEDB, $EF09)", text=[
    "If the player is in one of the rooms of Basil's house (33 to 39, the seven compares at $EFC9-$EFE4) control "
    "goes to $DFCC and Basil shoots you; otherwise the state word is cleared, the high nibble of +8 becomes 8 "
    "and bit 6 of +5 is set again - he is awake and a person again. Seen: thing 6 +9/+10 went from $07F0 to 0, "
    "+8 from $16 to $86 and +5 from $A0 to $E0 (11 sampled runs); with you in the house the branch to $DFCC "
    "ran twice in the stored routes."])
tidy(0xF1A8, title="Action record: the Major knocks the policeman out (RUN at $F097)", text=[
    "Prints 'You knocks the police man unconscious from behind.' ($6D5D) and sets the policeman (thing 11) to "
    "UNCONSCIOUS ($0910), high nibble 2 of +8, and clears bit 6 of +5. Seen: +10/+9 went from $050B (LOCAL) to "
    "$0910, +8 from $15 to $25 and +5 from $E0 to $A0."])
tidy(0xF1F6, title="Action record: reveal the burning note (RUN at $EF0C)", text=[
    "Sets bit 7 of the direct object's +5 - the bit $C821 tests for being visible. Run by Phipps's script at "
    "$EF0C on Wednesday morning with the burning note (thing 85) as the object; seen: +5 went from $20 to $A0, "
    "which is the note appearing in the bedroom at 10:05am."])

# ---------------------------------------------------------------------------------------------------------
# Routines that the audit tagged with a 'Coverage' note although they never carried a 'Not traced' line.
# The note said they were 'still marked not traced'; replace it with the instruction coverage.
# ---------------------------------------------------------------------------------------------------------
for _a in (0x99FC, 0x9C77, 0x9D13, 0x9D95, 0xAC24, 0xB387, 0xC583, 0xCAAF):
    A[_a]['desc'] = [p for p in A[_a]['desc'] if not p.startswith('Coverage, 9 November: the winning route')]
    _c = _EV['insn_coverage'].get(str(_a))
    if _c:
        _t, _h, _m = _c
        if _m:
            A[_a]['desc'].append("Instruction coverage over the 15 stored routes (9 November, tools/experiments/insn_coverage.py): "
                                 "%d of %d instructions executed; %s never ran there and are read from the code only." %
                                 (_h, _t, ' '.join('$%04X' % m for m in _m)))
        else:
            A[_a]['desc'].append("Instruction coverage over the 15 stored routes (9 November, tools/experiments/insn_coverage.py): "
                                 "all %d instructions were executed." % _t)

C(0xCC78, {0xCCAE: 'Yes: turn the order into a command ($B936) and carry it out ($C4D1) before the script\'s own instruction'})
C(0xEFC7, {0xEFF1: '...so it ends with bit 6 set again: awake and a person (the state word and the +8 nibble were cleared by $EFBA first)'})

# ---------------------------------------------------------------------------------------------------------
# Remaining prose caveats (9 November, second pass): resolve from the code or the emulator, or state
# precisely what never ran.
# ---------------------------------------------------------------------------------------------------------
C(0xC41F, {0xC451: 'Upper-case A if it is a lower-case letter ($C240)'})
C(0xC9BF, {0xC9D3: 'Check the direct object against the record ($C628); refuse if it fails',
                                 0xC9D8: 'Check the indirect object ($C6BE); refuse if it fails'})
C(0xE2C7, {0xE2D7: 'Move the cab (thing A = the hailed cab, id in $A034) into the player\'s room (B): $DD0E sets its +15',
           0xE2E2: 'DE = $F2B6, the cabbie\'s fare script',
           0xE2E8: 'Start the cabbie (the cab\'s id + 1) on that script, with the hailer and the cab as its objects ($E2EE)'})

def _setdesc(addr, old_pred, new):
    A[addr]['desc'] = [p for p in A[addr]['desc'] if not old_pred(p)] + new

_setdesc(0xE22A, lambda p: 'Format not decoded' in p, [
    "Decoded 9 November. The table is a list of groups, one per person: the person's id, then pairs of "
    "(topic id, message address) until $FF. The loop at $E207 finds the person, then $E201 finds the topic "
    "in that group; the message is printed through $6830 as the person's reply. A group that starts "
    "with $FE matches any person (the fallback), and a second $FF ends the table. Topic ids are things: "
    "$10 what happened, $11 your alibi, $12 your address, $0F the case, $43 the bloodstained clothes, "
    "and the people $05 Strachan, $06 Phipps, $07 the Major, $0D Tricia Fender.",
    "Gardener ($08): what happened and alibi share one reply (a gun shot woke him, he found Mrs Brown), "
    "and the Major gets another ('such a nice fellow... fighting'). Cook ($09): what happened/alibi (one "
    "reply), Phipps (overheard Basil and Daphne arguing about the will). Maid ($0A): what happened/alibi "
    "(Basil must have something to do with it). Phipps ($06): what happened/alibi (playing Chopin), "
    "address (Camden Street in London, Cobden Lane at Leatherhead). Strachan ($05): what happened/alibi "
    "(knows nothing), Tricia (she was Mr Brown's secretary), the Major (a friend of Mrs Jones). "
    "Straker ($04): the case ($7371, his report). The Major ($07): alibi (not at liberty to say; in London), "
    "address (Sidmouth Street). Tricia ($0D) and Mrs Jones ($5F): the bloodstained clothes (the confession "
    "'you found out, I am really Mrs Jones'); Mrs Jones also gives the confession for what happened/alibi "
    "and a short reply about Tricia ('blackmailing Mrs Brown'). The $FE fallback answers your address, "
    "what happened and your alibi with 'DON'T BE SILLY.' ($6845). Message texts rendered with the "
    "game's own printer (source/render_messages.py)."])

_setdesc(0xE2C7, lambda p: p.startswith('Record header: flags $47'), [
    "Record header: flags $47 (bit 6: pre-check routine at $E298), byte 1 $10; body at $E2CB. The body "
    "remembers the player's room ($A00A) and the hailed cab's id + 1 (the cabbie) in $E2C6, calls $DD0E "
    "to move the cab into the player's room, then calls $E2EE to start the cabbie on the script at $F2B6 "
    "with the hailer and the cab as objects. Confirmed in the emulator (tools/experiments/cab_test.py): "
    "HAIL CAB in Baker Street prints 'You hail the hansom cab.', the cabbie says 'Hello guv'nor.' and the "
    "next LOOK shows the cab with the cabbie in the street."])

_setdesc(0xF389, lambda p: p == 'Not yet examined.', [
    "The pre-check of the checks-only record at $F380 (flags $C8, bit 6). It tests the direct object ($A013): "
    "its holder (+1) must equal the actor's id less 1, and the actor must not be the direct object "
    "itself; otherwise it refuses ($DC15). Read from the code only; no breakpoint was set here."])
