const std = @import("std");

fn main() i32 {
    var a: [5]i32;

    a[0] = 5;
    a[1] = 2;
    a[2] = 4;
    a[3] = 1;
    a[4] = 3;

    std.debug.print("original:\n", .{});

    var i: i32 = 0;
    while (i < 5) {
        std.debug.print("{} ", .{a[i]});
        i += 1;
    }

    std.debug.print("\n", .{});

    // insertion sort
    i = 1;
    while (i < 5) {
        var key: i32 = a[i];
        var j: i32 = i - 1;

        while (j >= 0 && a[j] > key) {
            a[j + 1] = a[j];
            j -= 1;
        }

        a[j + 1] = key;

        i += 1;
    }

    std.debug.print("sorted:\n", .{});

    i = 0;
    while (i < 5) {
        std.debug.print("{} ", .{a[i]});
        i += 1;
    }

    std.debug.print("\n", .{});

    return 0;
}