"""optimization and other utilities for SAT models."""
from math import ceil


def flatten(l):
    """Return a flattened list from a list of lists."""
    return [item for sublist in l for item in sublist]


def dict_from_stats(statistics) -> dict:
    """Return a dictionary from z3 statistics."""
    return {key: statistics.get_key_value(key) for key in statistics.keys()}


def linear_optimization(solve_fun, width, nofrectangles, dimensions,
                        max_height, timeout=300000, rotations=False):
    """Apply linear optimization to solve_fun, passing other parameters."""
    total_solve_time = 0
    total_build_time = 0

    total_area = 0

    for i in range(nofrectangles):
        total_area += dimensions[i][0] * dimensions[i][1]
    area_min_height = ceil(total_area / width)

    # If total area is not divisible by width we round up
    if rotations:
        min_height = max(area_min_height, max(flatten(dimensions)))
    else:
        min_height = max(area_min_height,
                         max([dimensions[i][1] for i in range(nofrectangles)]))

    while True:
        # print('Trying height =', min_height)
        testsol = solve_fun(width, nofrectangles, dimensions, min_height,
                            timeout=timeout)

        # Update timeout based on passed time
        sol_height, solutions, stats, build_time = testsol
        solve_time = stats.get_key_value('time')
        total_build_time += build_time
        total_solve_time += solve_time
        timeout -= (solve_time + build_time) * 1000

        if testsol[0] is not None:
            # Return cumulative times
            # Last solution statistics are returned, but time value is
            # replaced by its cumulative
            stats_dict = dict_from_stats(stats)
            stats_dict['time'] = total_solve_time
            return sol_height, solutions, stats_dict, total_build_time

        if timeout < 0:
            return None

        min_height += 1


def binary_optimization(solve_fun, width, nofrectangles, dimensions,
                        max_height, timeout=300000, rotations=False):
    """Apply binary optimization to solve_fun, passing other parameters."""

    total_area = 0

    for i in range(nofrectangles):
        total_area += dimensions[i][0] * dimensions[i][1]

    # If total area is not divisible by width we round up
    if rotations:
        min_height = max(area_min_height, max(flatten(dimensions)))
    else:
        min_height = max(area_min_height,
                         max([dimensions[i][1] for i in range(nofrectangles)]))
    #max_height = sum([dimensions[k][1] for k in range(nofrectangles)])

    if min_height == max_height:
        return solve_fun(width, nofrectangles, dimensions, min_height)

    while min_height != max_height:
        # print('Trying height =', (min_height + max_height) // 2)
        testsol = solve_fun(width, nofrectangles, dimensions,
                            (min_height + max_height) // 2)
        #print(A[2])
        if testsol is None:
            min_height = ((min_height + max_height) // 2) + 1
        else:
            # testsol1 keeps track of the last correct solution so it
            # can be returned without recomputing sat_vlsi if in the
            # last iteration A == None
            testsol1 = testsol
            max_height = (min_height + max_height) // 2

    return testsol1
