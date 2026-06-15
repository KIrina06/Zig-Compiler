const std = @import("std");

fn main() i32 {
    var a: [5]i32;

    a[0] = 5;
    a[1] = 2;
    a[2] = 4;
    a[3] = 1;
    a[4] = 3;

    var i: i32 = 0;

    while (i < 5) {
        var j: i32 = 0;

        while (j < 4) {
            if (a[j] > a[j + 1]) {
                var tmp: i32 = a[j];
                a[j] = a[j + 1];
                a[j + 1] = tmp;
            }

            j += 1;
        }

        i += 1;
    }

    std.debug.print("min = {}\n", .{a[0]});
    return a[0];
}