# Oathbreaker

**Executions will continue until prisoner morale improves.**

So says the notice on the prison wall, and yours is next. The hill-goblins
took the cave-goblin city of Irthimgilnaz with the Necromancer's help,
turned its storerooms and cellars into cells, and hired human mercenaries,
your own countrymen, to guard them. You have just slipped out of your cell,
eight floors down. Hurry to the stairs before the guards find you.

Oathbreaker, by Kiëd Llaentenn (kiedtl), is a coffee-break roguelike about
not being seen. You have eight hit points and they do not come back on their
own; one guard who gets away and shouts can bring half the floor down on you.
Keep to the dark, walk on carpet and not gravel, hide in the tall mushrooms,
throw smoke and distractions, and when you must fight, strike first: a guard
who never saw you coming is perforated like a sieve. Rings found in golden
enclosures give you spells, fed by the Necromancer's power drained from the
corpses of his mages. Climb the eight floors of prison to get out, or turn
off into the Laboratory, the Workshop, the Shrine, the Caverns, the Temple,
the Crypt and the Holding cells.

## Playing

Start `oathbreaker` in a terminal of at least 150 by 44 with true colour.
Press **Esc** in the game for every key; the essentials:

- **q w e a d z x c** or **y k u h l b n j**: move; walk into a creature
  to attack it, onto stairs to climb them
- **s** or **.**: wait; **,**: pick up; **A**: use what you stand on;
  **'**: swap weapons
- **Space**: rings and abilities; **i**: inventory; **v**: examine;
  **@**: your character; **M**: messages
- **Ctrl+C**: quit at once

`RL_SEED=1234 oathbreaker` plays the same dungeon every time.

## Your files

Every run, however short, is written to the morgue, as a text file and as
JSON, in `$XDG_STATE_HOME/oathbreaker/morgue` (`~/.local/state/oathbreaker`
when `XDG_STATE_HOME` is not set). The log of the last session is
`session.log` beside it. The game reads its data from the `data` folder
next to the binary, wherever you start it from. It never connects to the
network.

## Credits

- Oathbreaker: Kiëd Llaentenn (kiedtl), https://github.com/kiedtl/roguelike
- Drawn with termbox (termbox_next by nullgemm); scripted with Janet
- Asciiverse edition: Asciiverse, https://asciiverse.sh
- License: GPL-3.0 (COPYING)

## This build

The terminal (termbox) edition of upstream's v4.1.0, built with Zig 0.14.0
as a static binary for Linux (x86-64, ARM64) and for macOS 11 and later
(Intel, Apple silicon). What we changed is in PATCHES.md.
