const std = @import("std");

fn main() i32 {
    var stack: [8]i32;
    var visited: [8]bool;

    var top: i32 = 0;

    stack[top] = 0;
    top += 1;

    while (top > 0) {
        top -= 1;
        const v: i32 = stack[top];

        if (!visited[v]) {
            visited[v] = true;
            std.debug.print("visit = {}\n", .{v});

            if (v + 1 < 4) {
                stack[top] = v + 1;
                top += 1;
            }
        }
    }

    return top;
}