const std = @import("std");

fn fib(n: u32) u32 {
    if (n <= 1) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

fn main() void {
    std.debug.print("fib = {}\n", .{fib(10)});
}
