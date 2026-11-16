#!/usr/bin/env python3
"""Makes the 100x30 catalog preview from a 150x44 recording of Oathbreaker
(record-preview.py). The game's smallest screen is 150x44: a 112x32 map, a
35-column sidebar on its right and a 10-line log below. The preview is put
together from the game's own cells, nothing redrawn or invented:

    columns  0-63, rows  0-20   the map, a window that follows the player
    columns 64-99, rows  0-20   the sidebar (stats, then what is in view)
    columns  0-99, rows 21-29   the newest lines of the log

Screens without the map (the title) are cut from the middle instead. The
cast is played through pyte and written again at up to 15 frames a second,
only the cells that changed, with pauses capped at the idle limit so
times in the file are the times a viewer sees.

    python3 asciiverse/compose-preview.py raw.cast oathbreaker.cast
"""
import json, sys

import pyte

SRC_COLS, SRC_ROWS = 150, 44
COLS, ROWS = 100, 30
MAP_W, MAP_H = 112, 32
WIN_W, WIN_H = 64, 21
SIDE_X, SIDE_Y = 114, 1
LOG_Y, LOG_H = 34, 9
MARGIN = 12                        # keep the player this far from the edges
FPS = 15.0


def rgb(c):
    if isinstance(c, str) and len(c) == 6:
        try:
            return int(c, 16)
        except ValueError:
            return None
    return None


def sgr(ch):
    parts = []
    for col, base in ((ch.fg, 38), (ch.bg, 48)):
        r = rgb(col)
        parts.append(f"{base};2;{r >> 16};{(r >> 8) & 255};{r & 255}" if r is not None
                     else str(base + 1))
    if ch.bold:
        parts.append("1")
    return ";".join(parts)


class Window:
    """Top left of the map window, moved only when the player nears an edge."""

    def __init__(self):
        self.x, self.y = (MAP_W - WIN_W) // 2, (MAP_H - WIN_H) // 2

    def follow(self, screen):
        for y in range(MAP_H):
            row = screen.buffer[y]
            for x in range(MAP_W):
                if row[x].data == "@":
                    if x < self.x + MARGIN or x >= self.x + WIN_W - MARGIN:
                        self.x = x - WIN_W // 2
                    if y < self.y + WIN_H // 4 or y >= self.y + WIN_H - WIN_H // 4:
                        self.y = y - WIN_H // 2
                    self.x = max(0, min(MAP_W - WIN_W, self.x))
                    self.x -= self.x % 2   # whole tiles: they sit two columns apart
                    self.y = max(0, min(MAP_H - WIN_H, self.y))
                    return


def source(screen, win, playing, y, x):
    """The source cell shown at (y, x) of the preview."""
    if not playing:
        return screen.buffer[y + (SRC_ROWS - ROWS) // 2][x + (SRC_COLS - COLS) // 2]
    if y < WIN_H:
        if x < WIN_W:
            return screen.buffer[win.y + y][win.x + x]
        return screen.buffer[SIDE_Y + y][SIDE_X + x - WIN_W]
    return screen.buffer[LOG_Y + y - WIN_H][x]


def main():
    src, dst = sys.argv[1], sys.argv[2]
    lines = open(src).read().splitlines()
    header = json.loads(lines[0])
    assert (header["term"]["cols"], header["term"]["rows"]) == (SRC_COLS, SRC_ROWS)
    header["term"]["cols"], header["term"]["rows"] = COLS, ROWS
    events = [json.loads(l) for l in lines[1:]]
    screen = pyte.Screen(SRC_COLS, SRC_ROWS)
    stream = pyte.ByteStream(screen)
    win = Window()
    shown = [[None] * COLS for _ in range(ROWS)]
    out = []
    last_t = 0.0
    step = 1.0 / FPS
    next_frame = step
    outputs = [i for i, e in enumerate(events) if e[1] == "o"]
    last_output = outputs[-1] if outputs else -1

    def frame(at):
        nonlocal last_t
        playing = "turns:" in "".join(screen.display[1])
        if playing:
            win.follow(screen)
        buf, cur = [], None
        for y in range(ROWS):
            moved = False
            for x in range(COLS):
                ch = source(screen, win, playing, y, x)
                key = (ch.data, ch.fg, ch.bg, ch.bold)
                if shown[y][x] == key:
                    moved = False
                    continue
                if not moved:
                    buf.append(f"\x1b[{y + 1};{x + 1}H")
                    moved = True
                s = sgr(ch)
                if s != cur:
                    buf.append(f"\x1b[0;{s}m")
                    cur = s
                buf.append(ch.data or " ")
                shown[y][x] = key
        if buf:
            buf.append("\x1b[0m")
            out.append([round(at - last_t, 3), "o", "".join(buf)])
            last_t = at

    limit = header.get("idle_time_limit") or 2.0
    t = 0.0
    for i, (dt, kind, data) in enumerate(events):
        t += min(dt, limit)            # pauses as the players show them
        while t >= next_frame:
            frame(next_frame)
            next_frame += step
        if kind == "o" and i == last_output:
            frame(t)               # the last frame, then the terminal reset
            out.append([round(t - last_t, 3), "o", data])
            last_t = t
        elif kind == "o":
            stream.feed(data.encode())
        else:
            out.append([round(t - last_t, 3), kind, data])
            last_t = t
    with open(dst, "w") as f:
        f.write(json.dumps(header, separators=(",", ":")) + "\n")
        for e in out:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
