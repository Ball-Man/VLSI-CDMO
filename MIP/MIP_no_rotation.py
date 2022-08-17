import gurobipy as gp
from gurobipy import GRB
import json

from util import linear_max, reify_or, lex_less

def solve(width, n, circuits, sort_column_row = False):
    m = gp.Model("mip1")
    m.setParam('TimeLimit', 5*60)
    min_height = sum([circuits[i][0]*circuits[i][1] for i in range(n)]) // width
    max_height = max(max([circuits[i][0] for i in range(n)]), sum([circuits[i][0] for i in range(n)]))
    

    x = []
    y = []
    for i in range(n):
        x.append(m.addVar(vtype=GRB.INTEGER, name=f"x_{i}"))
        y.append(m.addVar(vtype=GRB.INTEGER, name=f"y_{i}"))
        m.addConstr(x[i] <= width - circuits[i][0], f"width_{i}")
    
    print(f"Best height: {min_height}")
    
    height = m.addVar(vtype=GRB.INTEGER, name="height")
    linear_max(
        [y[i] + circuits[i][1] for i in range(n)],
        [(0, max_height) for _ in range(n)],
        height, m, "height")
        
    m.addConstr(height >= min_height, name="optimal_solution")
    
    # Non overlap
    for i in range(n):
        for j in range(i+1,n):
            # x[i] >= x[j] + w[j]   ->   -x[i] + x[j] + w[j] <= 0
            # x[j] >= x[i] + w[i]   ->   -x[j] + x[i] + w[i] <= 0
            # y[i] >= y[j] + h[j]   ->   -y[i] + y[j] + h[j] <= 0
            # y[j] >= y[i] + h[i]   ->   -y[j] + y[i] + h[i] <= 0

            # M[0] = w[j] + max(-1*0, -1*width) + max(1*0, 1*width)              -> M[0] = w[j] + width
            # M[1] = w[i] + max(-1*0, -1*width) + max(1*0, 1*width)              -> M[1] = w[i] + width
            # M[2] = h[j] + max(-1*0, -1*max_height) + max(1*0, 1*max_height)    -> M[2] = h[j] + max_height
            # M[3] = h[i] + max(-1*0, -1*max_height) + max(1*0, 1*max_height)    -> M[3] = h[i] + max_height
            reify_or(
                [
                    -x[i] + x[j] + circuits[j][0],
                    -x[j] + x[i] + circuits[i][0],
                    -y[i] + y[j] + circuits[j][1],
                    -y[j] + y[i] + circuits[i][1]
                ],
                [
                    circuits[j][0] + width,
                    circuits[i][0] + width,
                    circuits[j][1] + max_height,
                    circuits[i][1] + max_height
                ], m, "diffn")



    # Symmetry breaking
    # Horizontal
    lex_less(x, [width - x[i] - circuits[i][0] for i in range(0,n)], [(0, width) for _ in range(0,n)], [(0, width) for _ in range(0,n)], m, "horizontal_symmetry")

    # Vertical
    lex_less(y, [height - y[i] - circuits[i][1] for i in range(0,n)], [(0, max_height) for _ in range(0,n)], [(0, max_height) for _ in range(0,n)], m, "vertical_symmetry")
    
    # Equal circuits
    for i in range(n):
        for j in range(i+1,n):
            if circuits[i][0] == circuits[j][0] and circuits[i][1] == circuits[j][1]:
                lex_less([x[i], y[i]], [x[j], y[j]], [(0,width), (0,max_height)], [(0,width), (0,max_height)], m, f"equal_{i}_{j}")


    
    if sort_column_row:
        # Same width and same column sort by size in descending order 
        # w[i] = w[j] /\ h[i] < h[j] |= (x[i] = x[j] /\ h[i] = y[j] - y[i]) -> y[j] < y[i]
        for i in range(n):
            for j in range(i+1, n):
                if circuits[i][0] == circuits[j][0]:
                    (h,k) = (i,j) if circuits[i][1] < circuits[j][1] else (j,i) # if h[i] > h[j] swap i with j

                    reify_or(
                        [
                            x[h] - x[k] + 1,                        # x[i] <= x[j] - 1
                            x[k] - x[h] + 1,                        # x[i] >= x[j] + 1
                            y[k] - y[h] - circuits[h][1] + 1,       # h[i] <= y[j] - y[i] - 1
                            y[h] - y[k] + circuits[h][1] + 1,       # h[i] >= y[j] - y[i] + 1
                            y[k] - y[h] + 1                         # y[j] <= y[i] - 1
                        ],
                        [
                            1 + width,                              # 1 + max(1*0, 1*width) + max(-1*0, -1*width)
                            1 + width,                              # 1 + max(1*0, 1*width) + max(-1*0, -1*width)
                            - circuits[h][1] + 1 + max_height,      # - h[i] + 1 + max(1*0, 1*max_height) + max(-1*0, -1*max_height)
                            circuits[h][1] + 1 + max_height,        # h[i] + 1 + max(1*0, 1*max_height) + max(-1*0, -1*max_height)
                            1 + max_height                          # 1 + max(1*0, 1*max_height) + max(-1*0, -1*max_height)
                        ], m, f"same_column_{h}_{k}"
                    )


        # Same height and same row in ascending order 
        # h[i] = h[j] /\ w[i] < w[j] |= (y[i] = y[j] /\ w[i] = x[j] - x[i]) -> x[j] < x[i]
        for i in range(n):
            for j in range(i+1, n):
                if circuits[i][1] == circuits[j][1]:
                    (h,k) = (i,j) if circuits[i][0] < circuits[j][0] else (j,i) # if h[i] > h[j] swap i with j

                    reify_or(
                        [
                            y[h] - y[k] + 1,                        # y[i] <= y[j] - 1
                            y[k] - y[h] + 1,                        # y[i] >= y[j] + 1
                            x[k] - x[h] - circuits[h][0] + 1,       # w[i] <= x[j] - x[i] - 1
                            x[h] - x[k] + circuits[h][0] + 1,       # w[i] >= x[j] - x[i] + 1
                            x[k] - x[h] + 1                         # x[j] <= x[i] - 1
                        ],
                        [
                            1 + max_height,                         # 1 + max(1*0, 1*max_height) + max(-1*0, -1*max_height)
                            1 + max_height,                         # 1 + max(1*0, 1*max_height) + max(-1*0, -1*max_height)
                            - circuits[h][0] + 1 + width,           # - w[i] + 1 + max(1*0, 1*width) + max(-1*0, -1*width)
                            circuits[h][0] + 1 + width,             # w[i] + 1 + max(1*0, 1*width) + max(-1*0, -1*width)
                            1 + width                               # 1 + max(1*0, 1*width) + max(-1*0, -1*width)
                        ], m, f"same_column_{h}_{k}"
                    )
    
    m.setObjective(height, GRB.MINIMIZE)
    m.optimize()
    result = json.loads(m.getJSONSolution())

    rect = [(circuits[i][0], circuits[i][1], round(x[i].X), round(y[i].X)) for i in range(n)]
    return {"result": {"width": width, "height": round(height.X), "rect": rect},
            "statistics": result['SolutionInfo'],
            "status": result['SolutionInfo']["Status"]}


