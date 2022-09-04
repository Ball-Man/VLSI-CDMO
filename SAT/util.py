"""optimization and other utilities for SAT models."""
from math import ceil


def linear_optimization(solve_fun, width, nofrectangles, dimensions,
                        max_height):
    """Apply linear optimization to solve_fun, passing other parameters."""

    total_area = 0

    for i in range(nofrectangles):
        total_area += dimensions[i][0] * dimensions[i][1]

    # If total area is not divisible by width we round up
    min_height = max(ceil(total_area / width),
                     max([dimensions[i][1] for i in range(nofrectangles)]))

    while True:
        # print('Trying height =', min_height)
        testsol = solve_fun(width, nofrectangles, dimensions, min_height)
        if testsol != None:
            return testsol
        min_height += 1


def binary_optimization(solve_fun, width, nofrectangles, dimensions,
                        max_height):
    """Apply binary optimization to solve_fun, passing other parameters."""

    total_area = 0

    for i in range(nofrectangles):
        total_area += dimensions[i][0] * dimensions[i][1]

    min_height = max(ceil(total_area / width),
                     max([dimensions[i][1] for i in range(nofrectangles)]))
    #max_height = sum([dimensions[k][1] for k in range(nofrectangles)])

    if min_height == max_height:
        return solve_fun(width, nofrectangles, dimensions, min_height)

    while min_height != max_height:
        # print('Trying height =', (min_height + max_height) // 2)
        testsol = solve_fun(width, nofrectangles, dimensions,
                            (min_height + max_height) // 2)
        #print(A[2])
        if testsol == None:
            min_height = ((min_height + max_height) // 2) + 1
        else:
            # testsol1 keeps track of the last correct solution so it
            # can be returned without recomputing sat_vlsi if in the
            # last iteration A == None
            testsol1 = testsol
            max_height = (min_height + max_height) // 2

    return testsol1
