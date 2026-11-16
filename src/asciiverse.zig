// Asciiverse: where Oathbreaker finds its data and keeps its files.
//
// Upstream reads `data/` from the current directory and writes `morgue/`
// and its log there too (the log on stderr). Here the data is read from
// beside the binary, wherever the game is started from, and everything it
// writes goes to the state folder:
//
//   $XDG_STATE_HOME/oathbreaker/          (default ~/.local/state/oathbreaker)
//     morgue/      the record of every finished run, as upstream writes it
//     session.log  this session's log (std.log), started fresh each run
//
// An empty XDG_STATE_HOME counts as unset. OATHBREAKER_STATE_DIR, when set
// and not empty, names the folder directly (used by tests and recordings).

const std = @import("std");
const builtin = @import("builtin");

pub var state_dir: ?std.fs.Dir = null;
var log_file: ?std.fs.File = null;
var log_mutex: std.Thread.Mutex = .{};

fn envOwned(alloc: std.mem.Allocator, name: []const u8) ?[]u8 {
    const v = std.process.getEnvVarOwned(alloc, name) catch return null;
    if (v.len == 0) {
        alloc.free(v);
        return null;
    }
    return v;
}

fn statePath(alloc: std.mem.Allocator) ?[]u8 {
    if (envOwned(alloc, "OATHBREAKER_STATE_DIR")) |p| return p;
    if (envOwned(alloc, "XDG_STATE_HOME")) |x| {
        defer alloc.free(x);
        return std.fs.path.join(alloc, &.{ x, "oathbreaker" }) catch null;
    }
    const home_var = if (builtin.os.tag == .windows) "USERPROFILE" else "HOME";
    if (envOwned(alloc, home_var)) |h| {
        defer alloc.free(h);
        return std.fs.path.join(alloc, &.{ h, ".local", "state", "oathbreaker" }) catch null;
    }
    return null;
}

/// Changes into the folder holding the binary when `data/` is there, so
/// upstream's relative data paths work from anywhere, and opens the state
/// folder and the session log. Call before anything else.
pub fn setup() void {
    var buf: [std.fs.max_path_bytes]u8 = undefined;
    const alloc = std.heap.page_allocator;

    if (std.fs.selfExeDirPath(&buf)) |exe_dir| {
        var d = std.fs.cwd().openDir(exe_dir, .{}) catch null;
        if (d) |*dir| {
            defer dir.close();
            if (dir.access("data", .{})) |_| {
                std.posix.chdir(exe_dir) catch {};
            } else |_| {}
        }
    } else |_| {}

    const path = statePath(alloc) orelse return;
    defer alloc.free(path);
    const dir = std.fs.cwd().makeOpenPath(path, .{}) catch return;
    state_dir = dir;
    log_file = dir.createFile("session.log", .{ .truncate = true }) catch null;
}

/// std.log goes to the session log; without a state folder, to stderr as
/// upstream does.
pub fn logFn(
    comptime level: std.log.Level,
    comptime scope: @Type(.enum_literal),
    comptime format: []const u8,
    args: anytype,
) void {
    const f = log_file orelse return std.log.defaultLog(level, scope, format, args);
    const prefix = "[" ++ comptime level.asText() ++ "] " ++
        (if (scope == .default) "" else "(" ++ @tagName(scope) ++ ") ");
    log_mutex.lock();
    defer log_mutex.unlock();
    var bw = std.io.bufferedWriter(f.writer());
    bw.writer().print(prefix ++ format ++ "\n", args) catch return;
    bw.flush() catch {};
}
