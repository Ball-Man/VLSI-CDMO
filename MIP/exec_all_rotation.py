
import sys
import glob
import json
import os
import os.path as pt

from MIP_rotation import solve, supported_solver

DEFAULT_INSTANCES_DIR = pt.join(pt.dirname(__file__), '..', 'instances_json')
DEFAULT_OUTPUT_DIR = pt.join(pt.dirname(__file__), 'out_rotation')
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
    out_dir = f"{DEFAULT_OUTPUT_DIR}_{solver}"

    # Define a new instance for each input file
    for instance_file in glob.glob(pt.join(DEFAULT_INSTANCES_DIR, '*')):
        with open(instance_file) as fin:
            instance_data = json.load(fin)

        print(f'solving instance: {pt.basename(instance_file)}')
        result = solve(**instance_data, solver=solver)

        dump_statistics(result["statistics"], result["status"])
        print()

        # Dump results and statistics on file
        os.makedirs(out_dir, exist_ok=True)
        
        stats_basename = (f'stats-{pt.splitext(pt.basename(instance_file))[0]}'
                        '.txt')
        if result["status"] == "Optimal":
            output_basename = (f'out-{pt.splitext(pt.basename(instance_file))[0]}'
                        '.txt')
            with open(pt.join(out_dir, output_basename), 'w') as fout:
                fout.write(format_result(result["result"]))

        with open(pt.join(out_dir, stats_basename), 'w') as fout:
            dump_statistics(result["statistics"], result["status"], fout)


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] not in solvers):
        print("usage: prog.py [solver_name].")
        print("Supported solver: ", solvers)
    elif len(sys.argv) == 2 and sys.argv[1] in solvers:
        main(sys.argv[1])
    else:
        main()