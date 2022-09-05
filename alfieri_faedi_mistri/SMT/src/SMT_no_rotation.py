from z3 import *
import json
from math import ceil

from util import max as smt_max, lex_less

DEFAULT_TIME_LIMIT = 5*60


def solve(width, n, circuits, name="no_rotation", time_limit=DEFAULT_TIME_LIMIT,
          max_height=0):
    f'''
    Solve VLSI problem using a MILP formulation and MILP solver. Is not possible to rotate the chips.
    width : width of the plate
    n : number of circuits.
    circuits : list of tuple in the form [(x1,y1), ..., (xn, yn)].
    name : name of the model. Useful when exporting the model. Default "no_rotation".
    time_limit : time limit in which the calculation stops. Default {DEFAULT_TIME_LIMIT}.

    return : dict containing: 
        - status : string with a commend on the solution(eg. Optimal)
        - statistics : statistics of the solving process.
        - result : dict containing:
            - width : width of the plate.
            - height : height of the highest chip.
            - rect : list of tuple in the form [(w[1], h[1], x[1], y[i]), ..., (w[n], h[n], x[n], y[n])]
    '''

    opt = Optimize()
    opt.set("timeout", time_limit*1000)

    # Min height is the lowest possible height of a rectangle that can contain the circuits or the highest chip.
    min_height = max(ceil(sum([circuits[i][0]*circuits[i][1] for i in range(n)]) / width), max([circuits[i][1] for i in range(n)]))

    # Max height is obtained by stacking all chips in one column
    max_height = max_height or sum([circuits[i][0] for i in range(n)])
    print(f"Best height: {min_height}")

    # Objective variable
    height = Int("height")

    x = []
    y = []
    for i in range(n):
        x.append(Int(f"x_{i}"))
        y.append(Int(f"y_{i}"))
        opt.add(y[i] >=0); opt.add(y[i] <= max_height - circuits[i][1])
        opt.add(x[i] >=0); opt.add(x[i] <= width - circuits[i][0])

    # Set height as the max y[i] + h[i]
    opt.add(smt_max([y[i] + circuits[i][1] for i in range(n)], height))
    
    # Lower bound of the solution
    opt.add(height >= min_height)
    
    # Non overlap
    for i in range(n):
        for j in range(i+1,n):
            opt.add(Or(
                    x[i] >= x[j] + circuits[j][0],
                    x[j] >= x[i] + circuits[i][0],
                    y[i] >= y[j] + circuits[j][1],
                    y[j] >= y[i] + circuits[i][1]))



    # Symmetry breaking
    # Horizontal
    opt.add(lex_less(x, [width - x[i] - circuits[i][0] for i in range(0,n)]))

    # Vertical
    opt.add(lex_less(y, [height - y[i] - circuits[i][1] for i in range(0,n)]))
    
    # Equal circuits
    for i in range(n):
        for j in range(i+1,n):
            if circuits[i][0] == circuits[j][0] and circuits[i][1] == circuits[j][1]:
                opt.add(lex_less([x[i], y[i]], [x[j], y[j]]))

    opt.minimize(height)
    
    check_result = opt.check()
    m = opt.model()
    rect = [(circuits[i][0], circuits[i][1], m[x[i]].as_long(), m[y[i]].as_long()) for i in range(n) if m[x[i]] is not None and m[y[i]] is not None]
    found_height = m[height].as_long() if m[height] is not None else -1
    stats = opt.statistics()
    return {"result": {"width": width, "height": found_height, "rect": rect},
            "statistics": {**{k: stats.get_key_value(k) for k in stats.keys()}, "name": name},
            "status": check_result}
