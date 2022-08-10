
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


def problem_no_rotation(width, n, circuits):
    m = gp.Model("mip1")
    m.setParam('TimeLimit', 5*60)
    min_height = sum([circuits[i][0]*circuits[i][1] for i in range(n)]) // width
    max_height = max(max([circuits[i][0] for i in range(n)]), sum([circuits[i][0] for i in range(n)]))

    x = []
    y = []
    top_edges = []
    for i in range(n):
        x.append(m.addVar(vtype=GRB.INTEGER, name=f"x_{i}"))
        y.append(m.addVar(vtype=GRB.INTEGER, name=f"y_{i}"))
        top_edges.append(m.addVar(vtype=GRB.INTEGER, name=f"hs_{i}"))

        m.addConstr(x[i] <= width - circuits[i][0], f"width_{i}")
        m.addConstr(top_edges[i] == circuits[i][1] + y[i], f"top_edge_{i}")
    print(f"Best height: {min_height}")
    
    # Non overlap
    for i in range(n):
        for j in range(i+1,n):
            
            b = [m.addVar(vtype=GRB.BINARY, name=f"b_{k}_{i}_{j}") for k in range(4)]
            m.addConstr(sum(b) >= 1, f"diffn_b_{i}_{j}")
            
            m.addConstr(x[i] - x[j] <= -circuits[i][0] + (circuits[i][0] + width)*(1-b[0]))
            m.addConstr(x[j] - x[i] <= -circuits[j][0] + (circuits[j][0] + width)*(1-b[1]))
            m.addConstr(y[i] - y[j] <= -circuits[i][1] + (circuits[i][1] + max_height)*(1-b[2]))
            m.addConstr(y[j] - y[i] <= -circuits[j][1] + (circuits[j][1] + max_height)*(1-b[3]))
    
    # Height aka objective function
    height = m.addVar(vtype=GRB.INTEGER, name="height")
    b = [m.addVar(vtype=GRB.BINARY, name=f"b_height_{i}") for i in range(n)]
    m.addConstr(sum(b) == 1, f"height_sum_b")
    for i in range(n):
        m.addConstr(height >= top_edges[i], f"height_less_Y_{i}")
        m.addConstr(height <= top_edges[i] + (max_height-min([circuits[i][1] for i in range(n)]))*(1-b[i]), f"height_less_Y_{i}")
    m.addConstr(height >= min_height, "best_height")
    m.setObjective(height, GRB.MINIMIZE)
    m.optimize()
    result = json.loads(m.getJSONSolution())

    rect = [(int(x[i].X), int(y[i].X), circuits[i][0], circuits[i][1]) for i in range(n)]
    return {"result": {"width": width, "height": int(height.X), "rect": rect},
            "statistics": result['SolutionInfo'],
            "status": result['SolutionInfo']["Status"]}




def problem_rotation(width, n, circuits):
    m = gp.Model("mip2")
    m.setParam('TimeLimit', 5*60)
    min_height = sum([circuits[i][0]*circuits[i][1] for i in range(n)]) // width
    max_height = max(max([max(circuits[i]) for i in range(n)]), sum([max(circuits[i]) for i in range(n)]))

    x = []
    y = []
    r = []
    top_edges = []
    for i in range(n):
        x.append(m.addVar(vtype=GRB.INTEGER, name=f"x_{i}"))
        y.append(m.addVar(vtype=GRB.INTEGER, name=f"y_{i}"))
        r.append(m.addVar(vtype=GRB.BINARY, name=f"r_{i}"))
        top_edges.append(m.addVar(vtype=GRB.INTEGER, name=f"hs_{i}"))

        m.addConstr(x[i] + (1-r[i])*circuits[i][0] + r[i]*circuits[i][1] <= width, f"width_{i}")
        m.addConstr(top_edges[i] - y[i] + (circuits[i][1]-circuits[i][0])*r[i] == circuits[i][1], f"top_edge_{i}")
    print(f"Best height: {min_height}")
    
    # Non overlap
    for i in range(n):
        for j in range(i+1,n):
            
            b = [m.addVar(vtype=GRB.BINARY, name=f"b_{k}_{i}_{j}") for k in range(4)]
            m.addConstr(sum(b) >= 1, f"diffn_b_{i}_{j}")
            
            m.addConstr((x[i] - x[j]) <= width - b[0]*circuits[i][0] + b[0]*r[i]*circuits[i][0] - b[0]*r[i]*circuits[i][1] - b[0]*width )
            m.addConstr((x[j] - x[i]) <= width - b[1]*circuits[j][0] + b[1]*r[j]*circuits[j][0] - b[1]*r[j]*circuits[j][1] - b[1]*width )
            m.addConstr((y[i] - y[j]) <= max_height - b[2]*circuits[i][1] + b[2]*r[i]*circuits[i][1] - b[2]*r[i]*circuits[i][0] - b[2]*max_height )
            m.addConstr((y[j] - y[i]) <= max_height - b[3]*circuits[j][1] + b[3]*r[j]*circuits[j][1] - b[3]*r[j]*circuits[j][0] - b[3]*max_height )
            
    
    # Height aka objective function
    height = m.addVar(vtype=GRB.INTEGER, name="height")
    b = []
    
    for i in range(n):
        b.append(m.addVar(vtype=GRB.BINARY, name=f"b_height_{i}"))
        m.addConstr(height >= top_edges[i], f"height_less_Y_{i}")
        m.addConstr(height <= top_edges[i] + (max_height-min([circuits[i][1] for i in range(n)]))*(1-b[i]), f"height_less_Y_{i}")
    m.addConstr(sum(b) == 1, "height_sum_b")
    # Implied constraint
    m.addConstr(height >= min_height, "best_height")
    m.setObjective(height, GRB.MINIMIZE)
    print("Compiled")
    m.optimize()

    rect = []
    for i in range(n):
        if int(r[i].X) == 0:
            rect.append((int(x[i].X), int(y[i].X), circuits[i][0], circuits[i][1]))
        else:
            rect.append((int(x[i].X), int(y[i].X), circuits[i][1], circuits[i][0]))
    result = json.loads(m.getJSONSolution())
    return {"result": {"width": width, "height": int(height.X), "rect": rect},
            "statistics": result['SolutionInfo'],
            "status": result['SolutionInfo']["Status"]}


def dump_statistics(statistics, status, fp=sys.stdout):
    """Dump pretty printed statistics from minizinc results.statistics."""
    statistics = {**statistics, 'status': str(status)}
    json.dump(statistics, fp, indent=4)

def format_result(result):
    ret = f"{result['width']} {result['height']}\n{len(result['rect'])}\n"
    for r in result["rect"]:
        ret += " ".join([str(s) for s in r]) + "\n"
    return ret


def main():

    # Define a new instance for each input file
    for instance_file in glob.glob(pt.join(DEFAULT_INSTANCES_DIR, '*')):
        with open(instance_file) as fin:
            instance_data = json.load(fin)

        print(f'solving instance: {pt.basename(instance_file)}')
        print(instance_data)
        result = problem_no_rotation(**instance_data)

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


if __name__ == '__main__':
    main()


if __name__ == '__main__':
    main()