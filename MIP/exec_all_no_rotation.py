import sys
import glob
import json
import os
import os.path as pt

from MIP_no_rotation import solve, supported_solver

DEFAULT_INSTANCES_DIR = pt.join(pt.dirname(__file__), '..', 'instances_json')
DEFAULT_OUTPUT_DIR = pt.join(pt.dirname(__file__), 'out_no_rotation')
solvers = supported_solver()

def dump_statistics(statistics, status, fp=sys.stdout):
    """Dump pretty printed statistics from minizinc results.statistics."""
    statistics = {**statistics, 'status': str(status)}
    json.dump(statistics, fp, indent=4)

def format_result(result):
    ret = f"{result['width']} {result['height']}\n{len(result['rect'])}\n"
    for r in result["rect"]:
        ret += " ".join([str(s) for s in r]) + "\n"
    return ret

def main(solver=solvers[0]):

    # Define a new instance for each input file
    for instance_file in glob.glob(pt.join(DEFAULT_INSTANCES_DIR, '*')):
        with open(instance_file) as fin:
            instance_data = json.load(fin)

        print(f'solving instance: {pt.basename(instance_file)}')
        result = solve(**instance_data, solver=solver)

        dump_statistics(result["statistics"], result["status"])

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
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] in solvers):
        print("usage: prog.py [solver_name].")
        print("Supported solver: ", solvers)
    elif len(sys.argv) == 2 and sys.argv[1] in solvers:
        main(sys.argv[1])
    else:
        main()


