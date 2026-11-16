# Changes from upstream

This is the Asciiverse packaging of
[Oathbreaker](https://github.com/kiedtl/roguelike) by Kiëd Llaentenn
(kiedtl), GPL-3.0, built from upstream's tag `v4.1.0` (31 December 2025).
Upstream is the `upstream` remote; the `asciiverse` branch carries the
changes below, one commit each. Tags read `v4.1.0-av.<n>`.

We build the terminal edition, on termbox, which is upstream's default
build; upstream's own release downloads are the SDL tiles edition.

## The game

No rule, text, map or item is changed.

- **No crash reports to sentry.io.** Upstream uploads a report through
  libcurl when the game panics or hits a bug, unless `RL_NO_SENTRY` is
  set. The upload is gone, the switch is always on, and curl (the zig-curl
  dependency) is no longer linked. The game makes no network connections.
- **The terminal edition starts.** `present()` cleared the SDL frontend's
  dirty-cell buffer for every frontend, but only SDL allocates it, so the
  v4.1.0 termbox build crashed with a segfault on its first frame.
  Clearing it is now SDL only. Worth offering upstream.

## Files

- **Data beside the binary, everything written in the state folder.**
  Upstream reads `data/` from the current directory and writes `morgue/`
  there, its log going to stderr (over the game screen in a terminal). Now
  the game changes into its own folder when `data/` is there, so it starts
  from anywhere (also through a symlink), and writes to
  `$XDG_STATE_HOME/oathbreaker` (`~/.local/state/oathbreaker` by default;
  an empty `XDG_STATE_HOME` counts as unset; `OATHBREAKER_STATE_DIR` names
  the folder directly, for tests and recordings):
  - `morgue/`: the record of every finished run, as upstream writes it
  - `session.log`: the session's log (`std.log`), fresh each run
  All of it is in the new `src/asciiverse.zig`. Oathbreaker has no save
  games and no settings file.

## Build

- **Janet without `-march=native`**, so a binary runs on any CPU of its
  target, not only on the build machine's.
- **No libpng or zlib in the terminal build.** They load the SDL edition's
  PNG font only, so the termbox build needs nothing but libc and links
  fully static on Linux.
- **The binary is called `oathbreaker`** (upstream: `rl`).
- **`-Dstrip=true`** leaves the debug info out of release builds.
- **Zig:** upstream pins Zig 0.14.0, and so does our release workflow. The
  packaging was developed with Zig 0.14.1 (a patch release); it builds
  and runs the same, with no change needed.

## Platforms

- **Linux** (x86-64, ARM64): static musl builds, played.
- **macOS 11 and later** (Intel, Apple silicon): upstream's README says
  macOS is not supported, meaning its SDL edition; termbox already has the
  macOS definitions it needs (`_DARWIN_C_SOURCE`), and Zig 0.14 cross
  builds both macOS targets without errors. Not yet played on a Mac.
- **No Windows:** termbox needs a POSIX terminal (`termios`,
  `sys/select.h`). Upstream's Windows builds are the SDL edition.

## Packaging

- `.github/workflows/release.yml` (new): runs upstream's unit tests and
  its scripted combat tests (`RL_MODE=tester`), then builds the av
  archives for Linux and macOS, each with the binary at the top, `data/`
  beside it (without `data/font`, which only the SDL edition draws),
  `COPYING`, this file and our README, plus SHA256SUMS.
- `.github/workflows/build.yml` (removed): upstream's CI, which installs
  the SDL edition's libraries and runs the old binary name.
- `asciiverse/README.md` (new): the package README, shipped as
  `README.md`.
- `asciiverse/record-preview.py`, `asciiverse/compose-preview.py` (new):
  the catalog preview. The game's smallest screen is 150x44, so a bot
  plays at that size and the 100x30 preview is put together from the
  game's own cells: the map following the player, the sidebar, the log.
- `asciiverse/oathbreaker.toml`, `asciiverse/oathbreaker.md`,
  `asciiverse/oathbreaker.cast` (new): the catalog manifest, store page and
  preview, as drafts for hub.
- `CLAUDE.md` (new), `PATCHES.md` (new): notes.
