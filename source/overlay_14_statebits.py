"""The state-bits reference page: every flag byte of a thing record and what it does."""
from build_skeleton import page

_T5 = [
 ('7', '$80', 'Revealed (visible)',
  'Set on everything the player can see. A thing with this bit clear is hidden: #R$C821 says it cannot be seen, and EXAMINE needs it set. '
  '#R$9C56 sets it and #R$9C60 clears it. The torn note, the false bottom and the large rock start hidden and are revealed by examining the place that holds them; the steam trains are hidden until #R$9C41 moves one, which sets the bit.'),
 ('6', '$40', 'Person (alive and able to act)',
  'Set on every character who is in play. What a person holds is introduced with "&lt;name&gt; IS CARRYING", and a person can be talked to. '
  'Clearing it is how the game makes someone <b>asleep</b> or <b>unconscious</b> (#R$EFB3, #R$9ED1, #R$F1A8). The flag-word table at $C471 names the missing bit DEAD, so a check that needs a living person and finds the bit clear would say "IS DEAD". '
  'There is no separate "dead" bit: the dead are things with this bit clear, such as the female corpse (46) and the body (72).'),
 ('5', '$20', 'Open',
  'Set when a door, window, drawer or similar thing is open. OPEN sets it and CLOSE clears it (the two shared actions at $DE9D and $DEAF); OPEN refuses a thing that has it set ("IS OPEN") and CLOSE refuses one that has it clear ("IS CLOSED"). '
  'The containment walk at #R$C86E lets what is inside a holder be seen only when the holder has this bit or bit 3 set. The cabs and trains have it set, and so do the large rock and the burning note.'),
 ('4', '$10', 'On (alight)',
  'Set on the oil lamp when it is lit; the flag-word tables call the opposite OFF and this ON. The cabs and trains have it set. The light test at #R$D078 needs a thing in reach that is on and full.'),
 ('3', '$08', 'Contents can be seen',
  'The second way, besides bit 5, that a holder lets the things inside it be seen ($C86E). It is not set on any thing at the start of the game, and there is no word for it in the flag tables.'),
 ('2', '$04', 'Full',
  'Set on the oil lamp, the cabs, the trains and the deep stream. The flag-word tables call the opposite EMPTY and this FULL. The lamp must be both on and full to give light.'),
 ('1', '$02', 'Not used by any check found',
  'Set only on the deep stream (59). No verb record, flag table or light test reads it.'),
 ('0', '$01', 'Locked',
  'Set on the doors and windows that start locked (the front doors, the windows). The flag tables call the opposite UNLOCKED and this LOCKED. OPEN refuses a thing that has it set ("IS LOCKED"); the script helpers at $F203 and $F210 clear and set it.'),
]

_T6 = [
 ('7', '$80', 'Seen', 'Set on every thing that has been listed in a room description ($D526 sets it as it names each one). A piece of case evidence of the plain kind needs both of its things seen ($BE91).'),
 ('6', '$40', 'Examined', 'Set by EXAMINE ($DF5B). Evidence of the second kind needs both things examined.'),
 ('5', '$20', 'Countable', 'Set on the money things (27, 28, 32 and 35). COUNT needs it ($E31C).'),
]

_T4 = [
 ('7', '$80', 'Needs light', 'Set on the player, the china man, the old man and the cabbies; an actor with it set can be "too dark to see" ($D078). It is also set on the oil lamp and the vehicles.'),
 ('6-4', '$70', 'Kind of passenger', 'GET INTO a cab needs the thing at the cab\'s +3 and the actor to share one of these three bits ($E3B8): Lestrade, Watson, Straker, the police men, Tricia Fender and Mrs Jones have $10; the Major, Strachan, Phipps, the gardener, the cook, the maid and the German agent have $40; the player has $10 too, and the china man and the old man have $20.'),
 ('2-0', '$07', 'How it holds things', '0: cannot hold things. 1 IN, 2 ON, 3 BEHIND, 4 UNDER, 5 TIED TO: the word printed by $D5D3 when it lists what a thing holds. PUT IN refuses a thing whose bits 0-2 are all clear ($DED9).'),
]

_CASE = [
 ('0', '$01', 'Waiting', 'Holmes has told this statement and it has not yet been proven; Lestrade asks about it ($BC46, $9DD8). Cleared when it is proven.'),
 ('1', '$02', 'Proven (done)', 'The statement or piece of evidence has been established. Routines such as $9A74 set it. Once set it stays set.'),
 ('2', '$04', 'Has children', 'The evidence records that follow it, up to one with bit 3, are its sub-evidence; all must pass ($BF08).'),
 ('3', '$08', 'Last in its group', 'Closes a level of sub-evidence ($BE72).'),
 ('4-5', '$30', 'A routine follows', 'The record is six bytes, not four: the last two are the address of the routine that runs when it is proven (the Lestrade and Watson replies, $9A3D and so on). Bit 5 also marks the three "killed" statements: Watson matches those outright, while others he accepts only on a 50 per cent roll, and the waiting-statement check skips them.'),
 ('6-7', '$C0', 'Kind of test', '00: both things seen; 01: both examined; 10: only true once something else has marked it done; 11: no test of its own, only its group ($BE91).'),
]

def _rows(rows):
    return '\n'.join('<tr><td>%s</td><td>%s</td><td><b>%s</b></td><td>%s</td></tr>' % r for r in rows)

_HTML = '''
<p>Almost everything that can change about a person or object in Sherlock is a bit in its record. This page lists them: what each bit means, which things have it, and what the game does with it. The bytes below are offsets in an entity record (the things listed by the index at $8B6F).</p>

<h3>Asleep, unconscious, dead</h3>
<p>These are not three bits. Each is a combination of three parts of the record:</p>
<ul>
<li><b>The person bit</b> (+5 bit 6) is cleared, so the character stops being someone you can talk to.</li>
<li><b>A state word</b> (+9/+10, the first adjective slot of the name) is replaced by a word such as SLEEPING or UNCONSCIOUS, so the thing is listed as "a sleeping Phipps" or "an unconscious local police man". #R$F1C1 writes it, together with the article nibble below.</li>
<li><b>The article nibble</b> (the high nibble of +8) is changed so that the name reads properly with the new word: 1 is "a", 2 is "an", 8 is no article.</li>
</ul>
<table class="sherlock">
<tr><th>State</th><th>Who and when</th><th>What changes</th></tr>
<tr><td><b>Asleep</b></td><td>The gardener, the cook and Strachan at 9pm (#R$9ED1, #R$9EC1); Phipps in the night script (#R$EFB3).</td><td>The state word becomes SLEEPING ($07F0), the article nibble becomes 1, and the person bit is cleared. The gardener and cook also go off stage, and Strachan is moved to Daphne's room (74). Waking puts the person bit back and clears the word.</td></tr>
<tr><td><b>Unconscious</b></td><td>The local police man, when the Major knocks him out (#R$F1A8).</td><td>The state word becomes UNCONSCIOUS ($0910), the article nibble becomes 2, and the person bit is cleared. Straker reviving him (#R$ED39) puts back LOCAL ($050B), nibble 1 and the person bit.</td></tr>
<tr><td><b>Dead</b></td><td>The female corpse (46) and the body (72).</td><td>The thing is not a person: bit 6 is clear. A check that needs the person bit and does not find it prints the word DEAD from the flag table at $C471.</td></tr>
<tr><td><b>Burning, singed, burnt</b></td><td>The note Phipps burns (85).</td><td>BURNING ($0157) is replaced by SINGED ($07D5) when it is taken, or BURNT ($015B) when the countdown at $9CA1 runs out (#R$9CA2).</td></tr>
</table>

<h3>The flag byte, +5</h3>
<p>Eight bits of condition. The flag-word tables at $C471 (a bit that is needed but missing) and $C481 (a bit that is present but forbidden) give the words that "THE ... IS ..." messages print.</p>
<table class="sherlock">
<tr><th>Bit</th><th>Mask</th><th>Meaning</th><th>Details</th></tr>
%s
</table>
<p>Common values: $80 an ordinary visible thing, $A0 a visible thing that is open (or a person who is asleep or unconscious), $E0 a person in play, $81 a locked door, $B4 a cab (visible, open, on and full), $34 a train that is out of sight.</p>

<h3>How a verb tests these bits</h3>
<p>A verb's action record can carry a pair of masks and modes for the direct and indirect objects' +5 bytes (#R$C74E). Mode 0 needs every mask bit set, 1 needs at least one, 2 needs none, 3 not all. EXAMINE needs bit 7; OPEN needs bits 5 and 0 clear; CLOSE needs bit 5 set. On failure the offending bits go to $CB79 and #R$CB7B prints "THE ... IS ..." with the word from the table.</p>

<h3>The second flag byte, +6</h3>
<table class="sherlock">
<tr><th>Bit</th><th>Mask</th><th>Meaning</th><th>Details</th></tr>
%s
</table>

<h3>The type byte, +4</h3>
<table class="sherlock">
<tr><th>Bits</th><th>Mask</th><th>Meaning</th><th>Details</th></tr>
%s
</table>

<h3>The case table, +3 of a statement</h3>
<p>The statements and evidence of the case (the table at $9965) are four- or six-byte records; their byte 3 is a set of flags.</p>
<table class="sherlock">
<tr><th>Bit</th><th>Mask</th><th>Meaning</th><th>Details</th></tr>
%s
</table>
'''

page('state-bits', 'State bits: asleep, dead and the rest',
     _HTML % (_rows(_T5), _rows(_T6), _rows(_T4), _rows(_CASE)))
