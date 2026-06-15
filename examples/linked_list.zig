const std = @import("std");

const Node = struct {
    value: i32,
    next: ?*Node,
    prev: ?*Node,
};

fn main() i32 {
    var first: Node = undefined;
    var second: Node = undefined;

    first.value = 10;
    second.value = 20;

    first.next = &second;
    first.prev = null;

    second.next = null;
    second.prev = &first;

    std.debug.print("first = {}\n", .{first.value});
    std.debug.print("second = {}\n", .{first.next.*.value});

    return first.next.*.value;
}
