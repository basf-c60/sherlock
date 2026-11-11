# Emulator experiments

Small scripts used to check claims in the overlays by running the game.
Run them from the project's top folder, e.g.

    python3 tools/experiments/case_test.py

Each prints what it saw; the overlay text that relies on a result quotes
it. 2026-11-07: plan_trace.py (every plan instruction fetched over 106
turns is one tools/plan.py decodes), verbs_test.py and v129.py (verbs
128/129/131, SIGNAL/AWAIT/ASK), hour_test.py (verb 136), case_test.py
and bit5_test.py (proving statements to Lestrade), watson_reply.py,
bit6_test.py (busy characters), busy_test.py (next-turn times),
flags_test.py (THE ... IS OPEN/CLOSED), seen_test.py (+6 seen/examined),
multi_test.py (several sentences on a line), timeout_test.py (the
keyboard time limit), b91f_test.py, ask_test.py, waituntil.py, and the
older codes_test.py / follow_test.py / trash_test.py.

## The endgame (late evening, 2026-11-07)

- `phipps_route.py [ACTOR]` - log an actor's room changes through the
  week with only WAITs (default Phipps, 6). Phipps is at Old Mill Road
  (room 103) on Wednesday from 12:10pm until about 3:20pm.
- `lestrade_route.py` - the same for Lestrade, with the endgame
  statements poked proven; logs his script position too.
- `win_test.py [HOUR]` - an attempt to ride along with Lestrade by
  following him room to room. It does not manage to board the cab with
  him, so it only shows his timing (left at 11am, at Old Mill Road at
  3:13pm).
- `endgame_test.py [--no-lestrade] [--no-watson] [--absent]` - the last
  scene staged on platform one at Victoria. Confirms the winning text
  and both losing versions of $9E48.
- `lestrade_follow.py [COMMAND]` - Lestrade on the Leatherhead
  platform in his wait-for-a-train loop. SAY TO LESTRADE "FOLLOW ME"
  takes him with you.
- `chase.py A B C D E F` - the chase played in stages with snapshots
  (set SNAPS to a directory). Reproducible; lost by a minute at the
  Leatherhead platform - see the docstring.
- `cab_test.py` - hail a cab in Baker Street: 'Sorry guv'nor I cannot
  get there from'ere' for Old Mill Road; 20 minutes and 10d to
  Parliament Street, as the cab table ($9B7F) and fare code ($9B25) say.
- `chase.py P Q` (after A-E) - the police-cab line: Lestrade ordered to
  follow on the Leatherhead platform, the police cab to Kings Cross Road
  (95 minutes, arriving 6:42), then a hansom cab to Victoria (stage Q,
  not reached in time).
- `phipps_route.py 8` - the gardener: off at 9:05pm each night, back at
  5:30am, 1:40am, 1:35am (the lost-carry bug).
- `allbut_test.py [--trace]` - scenery (TAKE WINDOWS), abbreviations,
  synonyms, '@' to repeat, and the ALL BUT bug with its breakpoint trace
  (IY = $D36A at $B517).
- `chase.py A B C D E F2 G3` - **the winning line**: the furious police
  cab to Kings Cross Road and the underground train to Victoria. Ends with
  "...YOU TRULY DESERVE THE TITLE OF WORLDS GREATEST DETECTIVE." (the case
  statements are poked proven in stage A; you and Watson are put in
  Leatherhead's Main Street in stage B).
- `chase.py A B2 C2 D E F2 G3` - the same win with the journey from
  Holmes's rooms to Leatherhead played too (Baker Street, a cab to Kings
  Cross Road, the 12:25 train); boards the police cab when Lestrade's
  script is on $EA69.
- (inline tests, 8 Nov) IN: PUT LAMP IN SOFA gives 'WHAT ?' with IN
  tokenised as $E0 $0956 (VISITED) in the buffer at $5B81; PUT LAMP SOFA
  gives 'YOU CANNOT PUT IN THE SOFA'. The pronoun IT in commands gives
  'WHAT ?'; BECAUSE/THEREFORE in commands give 'WHAT ?'.
- `keys_test.py` - cursor keys as one-key moves, a room's long text only
  on the first visit, GO NORTH, EXAMINE CLOSELY, BREAK = KILL.

- `tails_test.py` ... `tails_test7.py` - remarks and orders typed to Lestrade (player put in his room by a poke) to reach the tails of $BB67 and $B98C: no-sense reply, summary branches ($BBD3/$BBD9/$BBE5) and the order-dropping paths. `tails_test6.py` tries $BBFB-$BC17 and does not reach it.
