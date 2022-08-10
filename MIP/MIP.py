
import gurobipy as gp
from gurobipy import GRB

import sys
import glob
import json
import datetime
import os
import os.path as pt


DEFAULT_INSTANCES_DIR = pt.join(pt.dirname(__file__), '..', 'instances_json')
DEFAULT_OUTPUT_DIR = pt.join(pt.dirname(__file__), 'out')



def reify_or(arr, big_m, model, key):
    '''Linearize the or.
    It require to pass the constraint in the form "a_ij*x_j - B_i <= 0"
    big_m is calculated as such: M_i = -B_i + SUM_j max(a_ij*l_j , a_ij*u_j)
    where l_j and u_j are the upper bound for a_ij.'''

    b = []
    for i in range(len(arr)):
        b.append(model.addVar(vtype=GRB.BINARY, name=f"{key}_b_{i}"))
        model.addConstr(arr[i] <= big_m[i]*(1-b[i]), name=f"{key}_{i}")
    model.addConstr(sum(b) >= 1, name=f"{key}_b_sum")

def lex_less(arr1, arr2, dom1, dom2, model, key):
    ''' Lexicographic ordering constraint.

    lex_less([x1, x2, ..., xk], [y1, y2, ..., yk],
        [(l_x1,u_x1), (l_x2,u_x2), ..., (l_xk,u_xk)],
        [(l_y1,u_y1), (l_y2,u_y2), ..., (l_yk,u_yk)],
        model, key)

    x1 <= y1
    /\ (x1 = y1 -> x2 <= y2)
    /\ ((x1 = y1 /\ x1 = y2) -> x2 <= y2) /\ ...
    /\ ((x1 = y1 /\ x2 = y2 /\ ... /\ xk-1 = yk-1) -> xk <= yk)
    '''

    # x1 <= y1 /\
    #     (x1 != y1 \/ x2 <= y2) /\             -> x1 - y1 + 1 <= 0 \/ y1 - x1 + 1 <= 0 \/ x2 - y2 <= 0
    #     (x1 != y1 \/ x2 != y2 \/ x3 <= y3)    -> x1 - y1 + 1 <= 0 \/ y1 - x1 + 1 <= 0 \/ x2 - y2 + 1 <= 0 \/ y2 - x2 + 1 <= 0 \/ x3 - y3 <= 0
    #     ...


    # x1 != y1   ->   x1 < y1 \/ x1 > y1   ->   x1 <= y1 - 1 \/ x1 >= y1 + 1   ->   x1 - y1 + 1 <= 0 \/ -x1 + y1 +1 <= 0
    for i in range(len(arr1)):
        reify_or(
            [ arr1[k] - arr2[k] + 1 for k in range(0,i)] +   # x_k < y_k \/
            [-arr1[k] + arr2[k] + 1 for k in range(0,i)] +   # x_k > y_k \/
            [arr1[i] - arr2[i]],                            # x_i <= y_i
            [1 + dom1[k][1] - dom2[k][0] for k in range(0,i)] + #  B = -1, Mk = 1 + max(dom1[k]) + max(-1*dom2[k][0], -1*dom2[k][1])   ->   1 + dom1[k][1] - dom2[k][0]
            [1 - dom1[k][0] + dom2[k][1] for k in range(0,i)] + #  B = -1, Mk = 1 + max(-1*dom1[k][0], -1*dom1[k][1]) + max(dom2[k])   ->   1 - dom1[k][0] + dom2[k][1]
            [dom1[i][1]], model, f"{key}_{i}")
    
def linear_max(arr, dom, model, key, vtype=GRB.INTEGER):
    ''' Max constraint.
        
        linear_max([x1, x2, ..., xk], [(l_1,u_1), (l_2,u_2), ..., (l_k,u_k)], model, key)
    '''

    # y = max(x1, x2, ..., xk): 
    #   y >= xi for i in 1..k
    #   y <= xi + (umax - l_i)*(1-b_i) where umax = max(u_1, u_2, ..., u_k) and b_i = 1 -> xi = max(x1, x2, ..., xk)

    max_var = model.addVar(vtype=vtype, name=f"{key}")
    b = []
    u_max = max(dom[i][1] for i in range(len(arr)))
    for i in range(len(arr)):
        b.append(model.addVar(vtype=GRB.BINARY, name=f"{key}_b_{i}"))
        model.addConstr(max_var >= arr[i], name=f"{key}_max1_{i}")
        model.addConstr(max_var <= arr[i] + (u_max - dom[i][0])*(1-b[i]), name=f"{key}_max2_{i}")

    model.addConstr(sum(b) == 1, f"{key}_sum_b")
    return max_var



def problem_no_rotation(width, n, circuits):
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

    height = linear_max([y[i] + circuits[i][1] for i in range(n)], [(0, max_height) for _ in range(n)], m, "height")
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
    
    m.setObjective(height, GRB.MINIMIZE)
    m.optimize()
    result = json.loads(m.getJSONSolution())

    rect = [(circuits[i][0], circuits[i][1], int(x[i].X), int(y[i].X)) for i in range(n)]
    return {"result": {"width": width, "height": int(height.X), "rect": rect},
            "statistics": result['SolutionInfo'],
            "status": result['SolutionInfo']["Status"]}


def problem_rotation(width, n, circuits):
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

    height = linear_max([y[i] + (1-r[i])*circuits[i][1] + r[i]*circuits[i][0] for i in range(n)], [(0, max_height) for _ in range(n)], m, "height")
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


def dump_statistics(statistics, status, fp=sys.stdout):
    """Dump pretty printed statistics from minizinc results.statistics."""
    statistics = {**statistics, 'status': str(status)}
    json.dump(statistics, fp, indent=4)

def format_result(result):
    print(result['rect'])
    ret = f"{result['width']} {result['height']}\n{len(result['rect'])}\n"
    for r in result["rect"]:
        ret += " ".join([str(s) for s in r]) + "\n"
    return ret


def main():

    # Define a new instance for each input file
    for instance_file in glob.glob(pt.join(DEFAULT_INSTANCES_DIR, '*15*')):
        with open(instance_file) as fin:
            instance_data = json.load(fin)

        print(f'solving instance: {pt.basename(instance_file)}')
        print(instance_data)
        result = problem_rotation(**instance_data)

        dump_statistics(result["statistics"], result["status"])
        print()

        # Dump results and statistics on file
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        output_basename = (f'out-{pt.splitext(pt.basename(instance_file))[0]}'
                           '.txt')
        stats_basename = (f'stats-{pt.splitext(pt.basename(instance_file))[0]}'
                          '.txt')
        with open(pt.join(DEFAULT_OUTPUT_DIR, output_basename), 'w') as fout:
            fout.write(format_result(result["result"]))

        with open(pt.join(DEFAULT_OUTPUT_DIR, stats_basename), 'w') as fout:
            dump_statistics(result["statistics"], result["status"], fout)
        return


if __name__ == '__main__':
    main()