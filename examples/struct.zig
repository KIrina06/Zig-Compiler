const std = @import("std");

const Node = struct {
    value: i32,
    next: ?*Node,
    prev: ?*Node,
};

fn main() i32 {
    var node: Node = undefined;

    node.value = 10;
    node.next = null;
    node.prev = null;

    std.debug.print("node value = {}\n", .{node.value});

    return node.value;
}
