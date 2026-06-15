const std = @import("std");

const Node = struct {
    value: i32,
    next: ?*Node,
    prev: ?*Node,
};

fn main() i32 {
    var n1: Node = undefined;
    var n2: Node = undefined;
    var n3: Node = undefined;

    // заполняем значения
    n1.value = 10;
    n2.value = 20;
    n3.value = 30;

    // связываем список: n1 <-> n2 <-> n3
    n1.prev = null;
    n1.next = &n2;

    n2.prev = &n1;
    n2.next = &n3;

    n3.prev = &n2;
    n3.next = null;

    std.debug.print("forward:\n", .{});

    // проход вперёд
    var current: ?*Node = &n1;

    while (current != null) {
        std.debug.print("{} ", .{current.*.value});
        current = current.*.next;
    }

    std.debug.print("\n", .{});

    std.debug.print("backward:\n", .{});

    // проход назад
    current = &n3;

    while (current != null) {
        std.debug.print("{} ", .{current.*.value});
        current = current.*.prev;
    }

    std.debug.print("\n", .{});

    return n2.value;
}
