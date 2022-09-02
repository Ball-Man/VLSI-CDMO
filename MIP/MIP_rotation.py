from pulp import LpVariable, LpProblem, LpMinimize, LpStatus, LpContinuous, LpInteger, LpBinary 
import pulp as pl
import json
from math import ceil, sqrt

from util import linear_max, linear_or, lex_less

DEFAULT_TIME_LIMIT = 5*60
VARIABLE_TYPE = LpContinuous

def supported_solver():
    '''Get a list with the supported pulp solver.'''

    return pl.listSolvers(onlyAvailable=True)

def solve(width, n, circuits, name="rotation", solver="PULP_CBC_CMD", export_file=None, time_limit=DEFAULT_TIME_LIMIT):
    f'''
    Solve VLSI problem using a MILP formulation and MILP solver. Is possible to rotate the chips.
    width : width of the plate
    n : number of circuits.
    circuits : list of tuple in the form [(x1,y1), ..., (xn, yn)].
    name : name of the model. Useful when exporting the model. Default "no_rotation".
    solver : set the solver to use. Use supported_solver() to list the supported solvers. Default "PULP_CBC_CMD".
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

    # Min height is the lowest possible height of a rectangle that can contain the circuits or the highest chip
    min_height = max(ceil(sum([circuits[i][0]*circuits[i][1] for i in range(n)]) / width),
                    max([min(circuits[i]) if max(circuits[i]) <= width else max(circuits[i]) for i in range(n)]))

    # Max height is obtained by stacking all chips in one column
    max_height = sum([max(circuits[i]) for i in range(n)])
    print(f"Best height: {min_height}")

    # Objective variable
    height = LpVariable("height", min_height, max_height, VARIABLE_TYPE)

    # Objective function
    model += height

    x = []
    y = []
    r = []
    for i in range(n):
        x.append(LpVariable(f"x_{i}", 0, width - circuits[i][0], VARIABLE_TYPE))
        y.append(LpVariable(f"y_{i}", 0, max_height - circuits[i][1], VARIABLE_TYPE))
        r.append(LpVariable(f"r_{i}", cat=LpBinary))
        model += (x[i] - r[i]*circuits[i][0] + r[i]*circuits[i][1] <= width - circuits[i][0], f"width_{i}")
    
    # Set height as the max y[i] + (h[i] if not rotated else w[i])
    linear_max(
        [y[i] - r[i]*circuits[i][1] + r[i]*circuits[i][0] + circuits[i][1] for i in range(n)],
        [(0, max_height) for _ in range(n)],
        height, model, "height")

    # Lower bound of the solution
    model += (height >= min_height, "optimal_solution")
    
    # Non overlap
    for i in range(n):
        for j in range(i+1,n):
            # x[i] >= x[j] + (1-r[j])*w[j] + r[j]*h[j]   ->   -x[i] + x[j] - r[j]*w[j] + r[j]*h[j] + w[j] <= 0
            # x[j] >= x[i] + (1-r[i])*w[i] + r[i]*h[i]   ->   -x[j] + x[i] - r[i]*w[i] + r[i]*h[i] + w[i] <= 0
            # y[i] >= y[j] + (1-r[j])*h[j] + r[j]*w[j]   ->   -y[i] + y[j] - r[j]*h[j] + r[j]*w[j] + h[j] <= 0
            # y[j] >= y[i] + (1-r[i])*h[i] + r[i]*w[i]   ->   -y[j] + y[i] - r[i]*h[i] + r[i]*w[i] + h[i] <= 0

            # M[0] = w[j] + max(-1*0, -1*(width-min(w[i], h[i]))) + max(1*0, 1*(width-min(w[j], h[j]))) + max(-w[j]*0, -w[j]*1) + max(h[j]*0, h[j]*1)               ->   M[0] = w[j] + width - min(w[j],h[j]) + h[j]
            # M[1] = w[i] + max(-1*0, -1*(width-min(w[j], h[j]))) + max(1*0, 1*(width-min(w[i], h[i]))) + max(-w[i]*0, -w[i]*1) + max(h[i]*0, h[i]*1)               ->   M[1] = w[i] + width - min(w[i],h[i]) + h[i]
            # M[2] = h[j] + max(-1*0, -1*(max_height-min(w[i], h[i]))) + max(1*0, 1*(max_height-min(w[j], h[j]))) + max(-h[j]*0, -h[j]*1) + max(w[j]*0, w[j]*1)     ->   M[2] = h[j] + max_height - min(w[j],h[j]) + w[j]
            # M[3] = h[i] + max(-1*0, -1*(max_height-min(w[j], h[j]))) + max(1*0, 1*(max_height-min(w[i], h[i]))) + max(-h[i]*0, -h[i]*1) + max(w[i]*0, w[i]*1)     ->   M[3] = h[i] + max_height - min(w[i],h[i]) + w[i]

            linear_or(
                [
                    -x[i] + x[j] - r[j]*circuits[j][0] + r[j]*circuits[j][1] + circuits[j][0],
                    -x[j] + x[i] - r[i]*circuits[i][0] + r[i]*circuits[i][1] + circuits[i][0],
                    -y[i] + y[j] - r[j]*circuits[j][1] + r[j]*circuits[j][0] + circuits[j][1],
                    -y[j] + y[i] - r[i]*circuits[i][1] + r[i]*circuits[i][0] + circuits[i][1]
                ],
                [
                    circuits[j][0] + width - min(circuits[j]) + circuits[j][1],
                    circuits[i][0] + width - min(circuits[i]) + circuits[i][1],
                    circuits[j][1] + max_height - min(circuits[j]) + circuits[j][0],
                    circuits[i][1] + max_height - min(circuits[i]) + circuits[i][0]
                ], model, f"diffn_{i}_{j}")



    # Symmetry breaking
    # Horizontal
    # x[i] <= W - x[i] - (1-r[i])*w[i] - r[i]*h[i]   ->  2x[i] <= r[i]*(w[i] - h[i]) + W - w[i]

    # D(2*x[i]) = (0, W - min(w[i],h[i])) * 2   -> (0, (W - min(w[i],h[i]))*2)
    # D(r[i]*(w[i] - h[i]) + W - w[i]) = (min(0,w[i]-h[i]) + W - w[i], max(0,w[i]-h[i]) + W - w[i]) ->
    #   ->  (W - max(w[i], h[i]), W - min(w[i], h[i]))
    lex_less([2*x[i] for i in range(n)],
        [r[i]*(circuits[i][0] - circuits[i][1]) + width - circuits[i][0] for i in range(n)],
        [(0, (width - min(circuits[i]))*2) for i in range(n)],
        [(width - max(circuits[i]), width - min(circuits[i])) for i in range(n)],
        model, "horizontal_symmetry", simplify=ceil(sqrt(n)))

    # Vertical
    # y[i] <= H - y[i] - (1-r[i])*h[i] - r[i]*w[i]   ->  2y[i] <= r[i]*(h[i] - w[i]) + H - h[i]

    # D(2*y[i]) = (0, H_max - min(w[i],h[i])) * 2   -> (0, (H_max - min(w[i],h[i]))*2)
    # D(r[i]*(h[i] - w[i]) + H - h[i]) = (min(0,h[i]-w[i]) + H_min - h[i], max(0,h[i]-w[i]) + H_max - h[i]) ->
    #   ->  (H_min - max(w[i], h[i]), H_max - min(w[i], h[i]))
    lex_less([2*y[i] for i in range(n)],
        [r[i]*(circuits[i][1] - circuits[i][0]) + height - circuits[i][1] for i in range(n)],
        [(0, (max_height - min(circuits[i])*2)) for i in range(n)],
        [(min_height - max(circuits[i]), max_height - min(circuits[i])) for i in range(n)],
        model, "vertical_symmetry", simplify=ceil(sqrt(n)))
    
    # Equal circuits
    for i in range(n):
        for j in range(i+1,n):
            if circuits[i][0] == circuits[j][0] and circuits[i][1] == circuits[j][1] or circuits[i][0] == circuits[j][1] and circuits[i][1] == circuits[j][0]:
                lex_less([x[i], y[i]],
                    [x[j], y[j]],
                    [(0,width - min(circuits[i])), (0,max_height - min(circuits[i]))], # Domain of x[i] and y[i]
                    [(0,width - min(circuits[j])), (0,max_height - min(circuits[j]))], # Domain of x[j] and y[j]
                    model, f"equal_{i}_{j}")
    
    # Square circuits
    for i in range(n):
        if circuits[i][0] == circuits[i][1]:
            model += (r[i] <= 0, f"square_{i}")

    model.solve(pl.getSolver(solver, timeLimit=time_limit))

    if export_file is not None:
        model.writeLP(export_file+".lp")
        print(f"Model exported in {export_file}")
    
    rect = _format_solution(circuits, n, x, y, r)
    final_height = round(height.varValue) if height.varValue is not None else None
    return {"result": {"width": width, "height": final_height, "rect": rect},
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

def _format_solution(circuits, n, x, y, r):
    '''
    Format the rectangle acording to the desired output.
    circuits : list of tuple in the form [(x1,y1), ..., (xn, yn)].
    n : number of circuits.
    x : LpVariable for the x axis.
    y : LpVariable for the y axis.
    r : LpVariable boolean value that indicate if the chip is rotated.
    '''
    rect = []
    for i in range(n):
        if r[i].varValue is None or r[i].varValue is None or r[i].varValue is None:
            return None
        if round(r[i].varValue) == 0:
            rect.append((circuits[i][0], circuits[i][1], round(x[i].varValue), round(y[i].varValue)))
        else:
            rect.append((circuits[i][1], circuits[i][0], round(x[i].varValue), round(y[i].varValue)))
    return rect