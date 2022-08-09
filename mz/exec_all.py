"""Launch the final model on all given instances.

Python >= 3.8.
"""
import sys
import glob
import json
import datetime
import os
import os.path as pt

from minizinc import Instance, Model, Solver

DEFAULT_MODEL_FILE = pt.join(pt.dirname(__file__), 'final.mzn')
# Path to json input instances, converted using convert_instances.py
DEFAULT_INSTANCES_DIR = pt.join(pt.dirname(__file__), '..', 'instances_json')
DEFAULT_OUTPUT_DIR = pt.join(pt.dirname(__file__), 'out')


def dump_statistics(statistics, status, fp=sys.stdout):
    """Dump pretty printed statistics from minizinc results.statistics."""
    statistics = {**statistics, 'status': str(status)}

    # Make time serializable
    time_keys = 'flatTime', 'time', 'solveTime', 'initTime', 'optTime'
    for key in time_keys:
        statistics[key] = str(statistics[key])

    json.dump(statistics, fp, indent=4)


def main():
    solver = Solver.lookup('chuffed')
    model = Model([DEFAULT_MODEL_FILE])

    # Define a new instance for each input file
    for instance_file in glob.glob(pt.join(DEFAULT_INSTANCES_DIR, '*')):
        instance = Instance(solver, model)
        with open(instance_file) as fin:
            instance_data = json.load(fin)

        # Populate instance parameters
        for key, value in instance_data.items():
            instance[key] = value

        print(f'solving instance: {pt.basename(instance_file)}')

        result = instance.solve(timeout=datetime.timedelta(minutes=5),
                                optimisation_level=5, free_search=True)

        dump_statistics(result.statistics, result.status)
        print()

        # Dump results and statistics on file
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        output_basename = (f'out-{pt.splitext(pt.basename(instance_file))[0]}'
                           '.txt')
        stats_basename = (f'stats-{pt.splitext(pt.basename(instance_file))[0]}'
                          '.txt')
        with open(pt.join(DEFAULT_OUTPUT_DIR, output_basename), 'w') as fout:
            fout.write(str(result))

        with open(pt.join(DEFAULT_OUTPUT_DIR, stats_basename), 'w') as fout:
            dump_statistics(result.statistics, result.status, fout)


if __name__ == '__main__':
    main()
