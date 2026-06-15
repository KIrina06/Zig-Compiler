const std = @import("std");

fn main() i32 {
    var queue: [8]i32;
    var visited: [8]bool;

    var head: i32 = 0;
    var tail: i32 = 0;

    queue[tail] = 0;
    tail += 1;
    visited[0] = true;

    while (head < tail) {
        const v: i32 = queue[head];
        head += 1;

        std.debug.print("visit = {}\n", .{v});

        if (v + 1 < 4) {
            if (!visited[v + 1]) {
                visited[v + 1] = true;
                queue[tail] = v + 1;
                tail += 1;
            }
        }
    }

    return head;
}