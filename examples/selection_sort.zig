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

    // selection sort
    i = 0;
    while (i < 5) {
        var min: i32 = i;
        var j: i32 = i + 1;

        while (j < 5) {
            if (a[j] < a[min]) {
                min = j;
            }
            j += 1;
        }

        if (min != i) {
            var tmp: i32 = a[i];
            a[i] = a[min];
            a[min] = tmp;
        }

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