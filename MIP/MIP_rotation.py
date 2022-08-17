import gurobipy as gp
from gurobipy import GRB
import json

from util import linear_max, reify_or, lex_less

def solve(width, n, circuits):
    m = gp.Model("mip2")
    m.setParam('TimeLimit', 5*60)
    min_height = sum([circuits[i][0]*circuits[i][1] for i in range(n)]) // width
    max_height = max(max([max(circuits[i]) for i in range(n)]), sum([circuits[i][0] for i in range(n)]))

    x = []
    y = []
    r = []
    for i in range(n):
        x.append(m.addVar(vtype=GRB.INTEGER, name=f"x_{i}"))
        y.append(m.addVar(vtype=GRB.INTEGER, name=f"y_{i}"))
        r.append(m.addVar(vtype=GRB.BINARY, name=f"r_{i}"))
        m.addConstr(x[i] <= width - (1-r[i])*circuits[i][0] - r[i]*circuits[i][1], f"width_{i}")
        
    print(f"Best height: {min_height}")

    height = m.addVar(vtype=GRB.INTEGER, name="height")
    linear_max(
        [y[i] + (1-r[i])*circuits[i][1] + r[i]*circuits[i][0] for i in range(n)],
        [(0, max_height) for _ in range(n)],
        height, m, "height")

    m.addConstr(height >= min_height, name="optimal_solution")
    
    # Non overlap
    for i in range(n):
        for j in range(i+1,n):
            # x[i] >= x[j] + (1-r[j])*w[j] + r[j]*h[j]   ->   -x[i] + x[j] - r[j]*w[j] + r[j]*h[j] + w[j] <= 0
            # x[j] >= x[i] + (1-r[i])*w[i] + r[i]*h[i]   ->   -x[j] + x[i] - r[i]*w[i] + r[i]*h[i] + w[i] <= 0
            # y[i] >= y[j] + (1-r[j])*h[j] + r[j]*w[j]   ->   -y[i] + y[j] - r[j]*h[j] + r[j]*w[j] + h[j] <= 0
            # y[j] >= y[i] + (1-r[i])*h[i] + r[i]*w[i]   ->   -y[j] + y[i] - r[i]*h[i] + r[i]*w[i] + h[i] <= 0

            # M[0] = w[j] + max(-1*0, -1*width) + max(1*0, 1*width)              ->   M[0] = w[j] + width
            # M[1] = w[i] + max(-1*0, -1*width) + max(1*0, 1*width)              ->   M[1] = w[i] + width
            # M[2] = h[j] + max(-1*0, -1*max_height) + max(1*0, 1*max_height)    ->   M[2] = h[j] + max_height
            # M[3] = h[i] + max(-1*0, -1*max_height) + max(1*0, 1*max_height)    ->   M[3] = h[i] + max_height
            reify_or(
                [
                    -x[i] + x[j] - r[j]*circuits[j][0] + r[j]*circuits[j][1] + circuits[j][0],
                    -x[j] + x[i] - r[i]*circuits[i][0] + r[i]*circuits[i][1] + circuits[i][0],
                    -y[i] + y[j] - r[j]*circuits[j][1] + r[j]*circuits[j][0] + circuits[j][1],
                    -y[j] + y[i] - r[i]*circuits[i][1] + r[i]*circuits[i][0] + circuits[i][1]
                ],
                [
                    circuits[j][0] + width,
                    circuits[i][0] + width,
                    circuits[j][1] + max_height,
                    circuits[i][1] + max_height
                ], m, "diffn")



    # Symmetry breaking
    # Horizontal
    lex_less(x, [width - x[i] - (1-r[i])*circuits[i][0] - r[i]*circuits[i][1] for i in range(0,n)], [(0, width) for _ in range(0,n)], [(0, width) for _ in range(0,n)], m, "horizontal_symmetry")

    # Vertical
    lex_less(y, [height - y[i] - (1-r[i])*circuits[i][1] - r[i]*circuits[i][0] for i in range(0,n)], [(0, max_height) for _ in range(0,n)], [(0, max_height) for _ in range(0,n)], m, "vertical_symmetry")
    
    # Equal circuits
    for i in range(n):
        for j in range(i+1,n):
            if circuits[i][0] == circuits[j][0] and circuits[i][1] == circuits[j][1] or circuits[i][0] == circuits[j][1] and circuits[i][1] == circuits[j][0]:
                lex_less([x[i], y[i]], [x[j], y[j]], [(0,width), (0,max_height)], [(0,width), (0,max_height)], m, f"equal_{i}_{j}")
    
    # Square circuits
    for i in range(n):
        if circuits[i][0] == circuits[i][1]:
            m.addConstr(r[i] <= 0, name=f"square_{i}")


    m.setObjective(height, GRB.MINIMIZE)
    m.optimize()
    result = json.loads(m.getJSONSolution())

    rect = []
    for i in range(n):
        if int(r[i].X) == 0:
            rect.append((circuits[i][0], circuits[i][1], int(x[i].X), int(y[i].X)))
        else:
            rect.append((circuits[i][1], circuits[i][0], int(x[i].X), int(y[i].X)))
        
    return {"result": {"width": width, "height": int(height.X), "rect": rect},
            "statistics": result['SolutionInfo'],
            "status": result['SolutionInfo']["Status"]}