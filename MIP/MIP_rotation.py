from pulp import LpVariable, LpProblem, LpMinimize, LpInteger, LpStatus, GUROBI, CPLEX_PY, PULP_CBC_CMD
import json


from util import linear_max, reify_or, lex_less

def solve(width, n, circuits, solver=None, export_file=None):
    model = LpProblem("rotation", LpMinimize)
    min_height = sum([circuits[i][0]*circuits[i][1] for i in range(n)]) // width
    max_height = max(max([max(circuits[i]) for i in range(n)]), sum([circuits[i][0] for i in range(n)]))
    print(f"Best height: {min_height}")

    height = LpVariable("height", 0, max_height, LpInteger)
    model += height
    x = []
    y = []
    r = []
    for i in range(n):
        x.append(LpVariable(f"x_{i}", 0, width - circuits[i][0], LpInteger))
        y.append(LpVariable(f"y_{i}", 0, max_height - circuits[i][1], LpInteger))
        r.append(LpVariable(f"r_{i}", 0, 1))
        model += (x[i] <= width - (1-r[i])*circuits[i][0] - r[i]*circuits[i][1], f"width_{i}")
    
    linear_max(
        [y[i] + (1-r[i])*circuits[i][1] + r[i]*circuits[i][0] for i in range(n)],
        [(0, max_height) for _ in range(n)],
        height, model, "height")

    model += (height >= min_height, "optimal_solution")
    
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
                ], model, f"diffn_{i}_{j}")



    # Symmetry breaking
    # Horizontal
    lex_less(x, [width - x[i] - (1-r[i])*circuits[i][0] - r[i]*circuits[i][1] for i in range(0,n)], [(0, width) for _ in range(0,n)], [(0, width) for _ in range(0,n)], model, "horizontal_symmetry")

    # Vertical
    lex_less(y, [height - y[i] - (1-r[i])*circuits[i][1] - r[i]*circuits[i][0] for i in range(0,n)], [(0, max_height) for _ in range(0,n)], [(0, max_height) for _ in range(0,n)], model, "vertical_symmetry")
    
    # Equal circuits
    for i in range(n):
        for j in range(i+1,n):
            if circuits[i][0] == circuits[j][0] and circuits[i][1] == circuits[j][1] or circuits[i][0] == circuits[j][1] and circuits[i][1] == circuits[j][0]:
                lex_less([x[i], y[i]], [x[j], y[j]], [(0,width), (0,max_height)], [(0,width), (0,max_height)], model, f"equal_{i}_{j}")
    
    # Square circuits
    for i in range(n):
        if circuits[i][0] == circuits[i][1]:
            model += (r[i] <= 0, f"square_{i}")


    if solver is None:
        model.solverModel = {}
        model.solve(GUROBI())
    else:
        model.solve(solver)

    if export_file is not None:
        model.writeLP(export_file+".lp")
        print(f"Model exported in {export_file}")

    rect = []
    for i in range(n):
        if round(r[i].varValue) == 0:
            rect.append((circuits[i][0], circuits[i][1], round(x[i].varValue), round(y[i].varValue)))
        else:
            rect.append((circuits[i][1], circuits[i][0], round(x[i].varValue), round(y[i].varValue)))
        
    return {"result": {"width": width, "height": round(height.varValue), "rect": rect},
            "statistics": get_solver_statistics(model.solver, model.solverModel),
            "status": LpStatus[model.status]}


def get_solver_statistics(solver, solverModel):
    if solver.__class__.__name__ == "GUROBI":
        return json.loads(solverModel.getJSONSolution())['SolutionInfo']
    if solver.__class__.__name__ == "CPLEX_PY":
        return solverModel.get_stats().__dict__
    return {}