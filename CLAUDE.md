# Oathbreaker, Asciiverse edition

kiedtl's stealth coffee-break roguelike (Zig, GPL-3.0), packaged for the
Asciiverse catalog: the terminal (termbox) edition of upstream `v4.1.0`.
Upstream is the `upstream` remote (github.com/kiedtl/roguelike); our work is
on the `asciiverse` branch, one commit per change, each listed in
PATCHES.md. Tags `v4.1.0-av.<n>`.

## Build and test

- Zig 0.14.0 (pinned upstream and in CI); 0.14.1 builds it the same.
  `git submodule update --init --recursive` first.
- `zig build -Doptimize=ReleaseSafe` gives `zig-out/bin/oathbreaker` with
  `data/` beside it. `zig build test` runs upstream's unit tests; from
  `zig-out/bin`, `RL_SEED=0xdefaced_cafe RL_MODE=tester ./oathbreaker` runs
  its scripted combat tests.
- Run heavy builds and plays under `systemd-run --user --scope -p
  MemoryMax=4G`, with a scratch `HOME` and `OATHBREAKER_STATE_DIR` (or
  `XDG_STATE_HOME`) in the same command, never the real state folder.
- The game needs a 150x44 terminal.

## Preview

`asciiverse/record-preview.py STAGE raw.cast SEED` records a bot at 150x44
(STAGE outside /tmp when asciinema is a snap: it has its own /tmp), and
`asciiverse/compose-preview.py raw.cast asciiverse/oathbreaker.cast` makes
the 100x30 preview. The current one is seed 3.

## Notes

- Windows is out: termbox is POSIX only.
- macOS archives are cross-built but have not been played on a Mac yet.
- Rules: no em or en dashes anywhere; commit as David
  <sandquist@gmail.com> with the Co-Authored-By line.
