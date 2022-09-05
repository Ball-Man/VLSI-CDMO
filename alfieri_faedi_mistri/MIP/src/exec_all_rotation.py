import sys
import glob
import json
import os
import os.path as pt
import argparse

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

def main(solver, time_limit, save_model):
    out_dir = f"{DEFAULT_OUTPUT_DIR}_{solver}"

    # Define a new instance for each input file
    for instance_file in glob.glob(pt.join(DEFAULT_INSTANCES_DIR, '*')):
        with open(instance_file) as fin:
            instance_data = json.load(fin)
        basename = pt.splitext(pt.basename(instance_file))[0]

        print(f'solving instance: {pt.basename(instance_file)}')
        print(instance_data)

        if save_model:
            result = solve(**instance_data, solver=solver, time_limit=time_limit, export_file=pt.join(out_dir, basename+".mps"))
        else:
            result = solve(**instance_data, solver=solver, time_limit=time_limit)

        dump_statistics(result["statistics"], result["status"])

        # Dump results and statistics on file
        os.makedirs(out_dir, exist_ok=True)

        
        
        if result["status"] == "Optimal":
            with open(pt.join(out_dir, f'out-{basename}.txt'), 'w') as fout:
                fout.write(format_result(result["result"]))
        
        with open(pt.join(out_dir, f'stats-{basename}.txt'), 'w') as fout:
            dump_statistics(result["statistics"], result["status"], fout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Solve all instances of VLSI')
    parser.add_argument("-s", dest="solver", nargs=1, default=[supported_solver()[0]], choices=supported_solver(),
                        help=f"Choose the solver to use, Default={supported_solver()[0]}")
    parser.add_argument("-t", dest="time_limit", default=300, type=int, 
                        help="Set the time limit to solver an instance. Once passed the instance is considered not solved")
    parser.add_argument("-sm", dest="save_model", default=False, action="store_true",
                        help="Save the models in mps format")
    args = parser.parse_args()

    main(args.solver[0], args.time_limit, args.save_model)


