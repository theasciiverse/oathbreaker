#!/usr/bin/env python3
"""Records the raw catalog preview of Oathbreaker at 150x44, the game's
smallest screen, played by a small bot that reads the screen through pyte:
it stabs whatever stands next to it (except fellow prisoners), climbs the
up stairs when it sees them and otherwise explores. compose-preview.py
then makes the 100x30 catalog cast from it.

    python3 asciiverse/record-preview.py STAGE OUT.cast [seed]

STAGE holds the built game (oathbreaker and data/). Needs pyte and
asciinema 3. Runs with a throwaway HOME and state folder, made beside
STAGE (keep STAGE out of /tmp when asciinema is a snap).
"""
import atexit, collections, fcntl, os, pty, select, shutil, signal, struct, sys, tempfile, termios, time

import pyte

COLS, ROWS = 150, 44
MAP_W, MAP_H = 112, 32            # ui.zig: MAP_WIDTH_R * 4, MAP_HEIGHT_R * 2
PLAY_SECONDS = 50

stage, cast = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
seed = sys.argv[3] if len(sys.argv) > 3 else "20261116"
# beside the stage, not in /tmp: the asciinema snap has a /tmp of its own
tmp = tempfile.mkdtemp(prefix="rec-home-", dir=os.path.dirname(stage))
ASCIINEMA = shutil.which("asciinema")
env = {"PATH": f"{stage}:/usr/local/bin:/usr/bin:/bin", "HOME": tmp,
       "XDG_STATE_HOME": os.path.join(tmp, "state"), "USER": "player",
       "LOGNAME": "player", "TERM": "xterm-256color", "COLORTERM": "truecolor",
       "LANG": "C.UTF-8", "RL_SEED": seed}

screen = pyte.Screen(COLS, ROWS)
stream = pyte.ByteStream(screen)
pid, fd = pty.fork()
if pid == 0:
    os.chdir(stage)
    os.execve(ASCIINEMA, ["asciinema", "rec", "--overwrite", "-q", "-i", "2",
        "--window-size", f"{COLS}x{ROWS}", "--capture-env", "TERM,COLORTERM,LANG",
        "--title", "Oathbreaker", "-c", "oathbreaker", cast], env)


def _stop():
    """Never leave a recorder or a game behind, however this script ends."""
    try:
        os.killpg(pid, signal.SIGHUP)
    except OSError:
        pass


atexit.register(_stop)
signal.signal(signal.SIGTERM, lambda *_: sys.exit(1))
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))


def pump(t):
    end = time.time() + t
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            try:
                data = os.read(fd, 65536)
            except OSError:
                return False
            if not data:
                return False
            stream.feed(data)
    return True


def text():
    return "\n".join(screen.display)


def wait_for(s, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        if s in text():
            return
        pump(0.2)
    sys.exit(f"timed out waiting for {s!r}:\n{text()}")


def key(k, t=0.25):
    os.write(fd, k.encode())
    pump(t)


DIRS = {(-1, 0): "k", (1, 0): "j", (0, -1): "h", (0, 1): "l",
        (-1, -1): "y", (-1, 1): "u", (1, -1): "b", (1, 1): "n"}
BLOCK = set("# ▄█▀≈8") | set("╔╗╚╝═║")
FRIENDS = set("p")
DOORS = set("+╋")      # entered and left straight, never diagonally


def tiles():
    """The map as {(row, tile column): char}, tiles on every other column."""
    lines = screen.display[:MAP_H]
    me = None
    for y, line in enumerate(lines):
        x = line[:MAP_W].find("@")
        if x >= 0:
            me = (y, x)
    if me is None:
        return None, {}
    par = me[1] % 2
    grid = {}
    for y, line in enumerate(lines):
        for x in range(par, MAP_W, 2):
            grid[(y, x // 2)] = line[x] if x < len(line) else " "
    return (me[0], me[1] // 2), grid


visits = collections.Counter()
LOG = open(os.environ["OB_REC_LOG"], "w", buffering=1) if os.environ.get("OB_REC_LOG") else None
pos = [0, 0]           # where the player is in the level, by dead reckoning:
                       # the map scrolls to keep the player in place


def same(a, b, dy, dx):
    return sum(1 for (y, x), c in a.items() if c not in " " and b.get((y - dy, x - dx)) == c)


def move(d, me, grid):
    key(DIRS[d])
    now, new = tiles()
    # the map scrolls only near its edges: the player moved when the @ did,
    # or when the map shifted under it
    if now == (me[0] + d[0], me[1] + d[1]) or (
            now == me and new and same(new, grid, -d[0], -d[1]) > same(new, grid, 0, 0)):
        pos[0] += d[0]
        pos[1] += d[1]
    else:                  # did not move: try somewhere else next time
        visits[(pos[0] + d[0], pos[1] + d[1])] += 5


def step():
    if "Really " in text():        # "Really attack unaware enemy?": yes
        if LOG:
            LOG.write("prompt\n" + text() + "\n")
        key("\r" if "> Yes" in text() else "j", 0.3)
        return True
    me, grid = tiles()
    if me is None:                 # mid-redraw or a screen over the map
        pump(0.2)
        return False
    off = (pos[0] - me[0], pos[1] - me[1])     # screen tile to level tile
    visits[tuple(pos)] += 1
    for d in DIRS:
        c = grid.get((me[0] + d[0], me[1] + d[1]), " ")
        if c.isalpha() and c not in FRIENDS:
            if LOG:
                LOG.write(f"attack {c} {d}\n")
            key(DIRS[d])
            return True

    def passable(c):
        return c not in BLOCK and not c.isalpha()

    want_stairs = any(c == "<" for c in grid.values())
    prev = {me: None}
    q = collections.deque([me])
    goal = best = None
    while q:
        p = q.popleft()
        c = grid.get(p, " ")
        if p != me:
            if want_stairs and c == "<":
                goal = p
                break
            if not want_stairs and any(grid.get((p[0] + dy, p[1] + dx), " ") == " "
                                       for dy, dx in DIRS):
                score = visits[(p[0] + off[0], p[1] + off[1])]
                if best is None or score < best[0]:
                    best = (score, p)
                    if score == 0:
                        goal = p
                        break
        for dy, dx in DIRS:
            n = (p[0] + dy, p[1] + dx)
            if dy and dx and (c in DOORS or grid.get(n, " ") in DOORS):
                continue
            if n not in prev and passable(grid.get(n, " ")):
                prev[n] = p
                q.append(n)
    if goal is None and best:
        goal = best[1]
    if goal is None:
        key("s")
        return True
    while prev[goal] != me:
        goal = prev[goal]
    d = (goal[0] - me[0], goal[1] - me[1])
    if LOG:
        LOG.write(f"pos {pos} -> {d}\n")
    move(d, me, grid)
    return True


pump(1.0)
wait_for("New  game")
key("\r", 1.0)
wait_for("Press any key")
key(" ", 1.5)
wait_for("turns:")
pump(2.0)
end = time.time() + PLAY_SECONDS
while time.time() < end and "turns:" in text() and "You die" not in text():
    step()
pump(1.5)
if "You die" in text():            # on to the summary of the run
    key("\r", 4.0)
for _ in range(5):                 # Ctrl+C quits; leave any open prompt first
    if "turns:" not in text() and "Really" not in text():
        break
    os.write(fd, b"\x1b" if "Really" in text() else b"\x03")
    pump(1.0)
os.write(fd, b"\x03")
pump(2.0)
os.waitpid(pid, 0)
