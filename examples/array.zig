const std = @import("std");

fn main() i32 {
    var a: [5]i32;

    a[0] = 5;
    a[1] = 2;
    a[2] = 4;
    a[3] = 1;
    a[4] = 3;

    // простой пузырёк (частичный, для демонстрации)
    var i: i32 = 0;

    while (i < 4) {
        if (a[i] > a[i + 1]) {
            var tmp: i32 = a[i];
            a[i] = a[i + 1];
            a[i + 1] = tmp;
        }

        i += 1;
    }

    std.debug.print("first = {}\\n", .{a[0]});

    return a[0];
}