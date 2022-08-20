from pulp import LpVariable, LpProblem, LpMinimize, LpStatus, GUROBI, CPLEX_PY, PULP_CBC_CMD, LpContinuous, LpInteger 
import pulp as pl
import json
from math import ceil

from util import linear_max, lex_less, linear_or

DEFAULT_TIME_LIMIT = 5*60
VARIABLE_TYPE = LpInteger

def supported_solver():
    return pl.listSolvers(onlyAvailable=True)

def solve(width, n, circuits, name="no_rotation", solver="PULP_CBC_CMD", sort_column_row = False, export_file=None, time_limit=DEFAULT_TIME_LIMIT):
    f'''
    Solve VLSI problem using a MILP formulation and MILP solver. Is not possible to rotate the chips.
    width : width of the plate
    n : number of circuits.
    circuits : list of tuple in the form [(x1,y1), ..., (xn, yn)].
    name : name of the model. Useful when exporting the model. Default "no_rotation".
    solver : set the solver to use. Use supported_solver() to list the supported solvers. Default "PULP_CBC_CMD".
    sort_column_row : additional symmetry breaking. This symmetry breaking increase by lot the complexity. Default False.
    export_file : export the model into lp format. Default None
    time_limit : time limit in which the calculation stops. Default {DEFAULT_TIME_LIMIT}.

    return : dict containing: 
        - status : string with a commend on the solution(eg. Optimal)
        - statistics : statistics of the solving process. Contains at least "solutionTime" and "solutionCpuTime".
        - result : dict containing:
            - width : width of the plate.
            - height : height of the highest chip.
            - rect : list of tuple in the form [(w[1], h[1], x[1], y[i]), ..., (w[n], h[n], x[n], y[n])]
    '''

    model = LpProblem(name, LpMinimize)

    # Min height is the lowest possible height of a rectangle that can contain the circuits or the highest chip.
    min_height = max(ceil(sum([circuits[i][0]*circuits[i][1] for i in range(n)]) / width), max([circuits[i][1] for i in range(n)]))

    # Max height is obtained by stacking all chips in one column
    max_height = sum([circuits[i][0] for i in range(n)])

    print(f"Best height: {min_height}")

    # Objective variable
    height = LpVariable("height", 0, max_height, VARIABLE_TYPE)

    # Objective function. Must be the first contraint.
    model += height

    x = []
    y = []
    for i in range(n):
        x.append(LpVariable(f"x_{i}", 0, width - circuits[i][0], VARIABLE_TYPE))
        y.append(LpVariable(f"y_{i}", 0, max_height - circuits[i][1], VARIABLE_TYPE))
        model += (x[i] <= width - circuits[i][0], f"width_{i}")

    # Set height as the max y[i] + h[i]
    linear_max(
        [y[i] + circuits[i][1] for i in range(n)],
        [(0, max_height) for _ in range(n)],
        height, model, "height")
    
    # Lower bound of the solution
    model += (height >= min_height, "optimal_solution")
    
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
            linear_or(
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
                ], model, f"diffn_{i}_{j}")



    # Symmetry breaking
    # Horizontal
    lex_less(x, [width - x[i] - circuits[i][0] for i in range(0,n)], [(0, width) for _ in range(0,n)], [(0, width) for _ in range(0,n)], model, "horizontal_symmetry")

    # Vertical
    lex_less(y, [height - y[i] - circuits[i][1] for i in range(0,n)], [(0, max_height) for _ in range(0,n)], [(0, max_height) for _ in range(0,n)], model, "vertical_symmetry")
    
    # Equal circuits
    for i in range(n):
        for j in range(i+1,n):
            if circuits[i][0] == circuits[j][0] and circuits[i][1] == circuits[j][1]:
                lex_less([x[i], y[i]], [x[j], y[j]], [(0,width), (0,max_height)], [(0,width), (0,max_height)], model, f"equal_{i}_{j}")


    
    if sort_column_row:
        # Same width and same column sort by size in descending order 
        # w[i] = w[j] /\ h[i] < h[j] |= (x[i] = x[j] /\ h[i] = y[j] - y[i]) -> y[j] < y[i]
        for i in range(n):
            for j in range(i+1, n):
                if circuits[i][0] == circuits[j][0]:
                    (h,k) = (i,j) if circuits[i][1] < circuits[j][1] else (j,i) # if h[i] > h[j] swap i with j

                    linear_or(
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
                        ], model, f"same_column_{h}_{k}"
                    )


        # Same height and same row in ascending order 
        # h[i] = h[j] /\ w[i] < w[j] |= (y[i] = y[j] /\ w[i] = x[j] - x[i]) -> x[j] < x[i]
        for i in range(n):
            for j in range(i+1, n):
                if circuits[i][1] == circuits[j][1]:
                    (h,k) = (i,j) if circuits[i][0] < circuits[j][0] else (j,i) # if h[i] > h[j] swap i with j

                    linear_or(
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
                        ], model, f"same_column_{h}_{k}"
                    )

    
    model.solverModel = {}
    model.solve(pl.getSolver(solver, timeLimit=time_limit))
        

    if export_file is not None:
        model.writeLP(export_file+".lp")
        print(f"Model exported in {export_file}")

    
    rect = [(circuits[i][0], circuits[i][1], round(x[i].varValue), round(y[i].varValue)) for i in range(n)]
    return {"result": {"width": width, "height": round(height.varValue), "rect": rect},
            "statistics": _get_solver_statistics(solver, model),
            "status": LpStatus[model.status]}


def _get_solver_statistics(solver, model):
    '''
    Get statistics from the solution. If the solver is GUROBI or CPLEX_PY it gives additional infos.

    solver : name of the solver
    model : model that already have solved the problem

    return : dict containing infos.
    '''

    if solver == "GUROBI":
        ret = json.loads(model.solverModel.getJSONSolution())['SolutionInfo']
    elif solver == "CPLEX_PY":
        ret = model.solverModel.get_stats().__dict__
    else:
        ret = {}

    ret["solutionTime"] = model.solutionTime
    ret["solutionCpuTime"] = model.solutionCpuTime

    return ret
