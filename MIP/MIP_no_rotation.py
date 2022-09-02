from pulp import LpVariable, LpProblem, LpMinimize, LpStatus, LpContinuous, LpInteger
import pulp as pl
import json
from math import ceil, sqrt

from util import linear_max, lex_less, linear_or

DEFAULT_TIME_LIMIT = 5*60
VARIABLE_TYPE = LpContinuous

def supported_solver():
    '''Get a list with the supported pulp solver.'''

    return pl.listSolvers(onlyAvailable=True)

def solve(width, n, circuits, max_height=-1, name="no_rotation", solver="PULP_CBC_CMD", export_file=None, time_limit=DEFAULT_TIME_LIMIT):
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
    max_height = (max_height if max_height > 0 else sum([circuits[i][0] for i in range(n)])) + 1 # + 1 because bounds exclude max_height
    print(f"Best height: {min_height}")

    # Objective variable
    height = LpVariable("height", min_height, max_height, VARIABLE_TYPE)
    height_half = LpVariable("height_tmp", min_height/2, max_height/2, VARIABLE_TYPE)

    # Objective function. Must be the first contraint.
    model += height
    model += height_half == 0.5*height

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

            # M[0] = w[j] + max(-1*0, -1*(width-w[i])) + max(1*0, 1*(width-w[j]))              -> M[0] = width
            # M[1] = w[i] + max(-1*0, -1*(width-w[j])) + max(1*0, 1*(width-w[i]))              -> M[1] = width
            # M[2] = h[j] + max(-1*0, -1*(max_height-h[i])) + max(1*0, 1*(max_height-h[j]))    -> M[2] = max_height
            # M[3] = h[i] + max(-1*0, -1*(max_height-h[j])) + max(1*0, 1*(max_height-h[i]))    -> M[3] = max_height
            linear_or(
                [
                    -x[i] + x[j] + circuits[j][0],
                    -x[j] + x[i] + circuits[i][0],
                    -y[i] + y[j] + circuits[j][1],
                    -y[j] + y[i] + circuits[i][1]
                ],
                [
                    width,
                    width,
                    max_height,
                    max_height
                ], model, f"diffn_{i}_{j}")

    # Symmetry breaking
    # Horizontal
    lex_less(x,
            [(width - circuits[i][0])/2 for i in range(n)], # NB. independent from any variable
            [(0, width - circuits[i][0]) for i in range(n)], # Domain of x
            [(0, width - circuits[i][0]) for i in range(n)], # Domain of mirrored x
            model, "horizontal_symmetry")

    # Vertical
    lex_less(y,
            [(height - circuits[i][1])/2 for i in range(n)],
            [(0, max_height - circuits[i][1]) for i in range(n)], # Domain of y
            [(0, max_height - circuits[i][1]) for i in range(n)], # Domain of mirrored y
            model, "vertical_symmetry")

    # Equal circuits
    for i in range(n):
        for j in range(i+1,n):
            if circuits[i][0] == circuits[j][0] and circuits[i][1] == circuits[j][1]:
                lex_less([x[i], y[i]], [x[j], y[j]],
                [(0,width - circuits[i][0]), (0,max_height - circuits[i][1])],
                [(0,width - circuits[j][0]), (0,max_height - circuits[j][1])],
                model, f"equal_{i}_{j}")

    model.solverModel = {}
    model.solve(pl.getSolver(solver, timeLimit=time_limit))

    if export_file is not None:
        model.writeLP(export_file+".lp")
        print(f"Model exported in {export_file}")

    rect = _format_solution(circuits, n, x, y)
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

def _format_solution(circuits, n, x, y):
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
        if x[i].varValue is None or y[i].varValue is None:
            return None
        rect.append((circuits[i][0], circuits[i][1], round(x[i].varValue), round(y[i].varValue)))
    return rect