"""Launch the sat model on all given instances.

Python >= 3.8.
"""
import re
import sys
import glob
import json
import datetime
import os
import os.path as pt
import argparse


from SAT_model import *


# Path to json input instances, converted using convert_instances.py
DEFAULT_INSTANCES_DIR = pt.join(pt.dirname(__file__), '..', 'instances_json')
DEFAULT_OUTPUT_DIR = pt.join(pt.dirname(__file__), 'out')

SAT_INSTANCE_DECODER_RE = re.compile(r'x_([0-9]+)_([0-9]+)_([0-9]+)')

def dump_result(instance_data, height, fp=sys.stdout):
    """Format result and dump it."""
    fp.write(f'{instance_data["width"]} {height}\n{instance_data["n"]}\n')
    fp.writelines(' '.join(map(str, circuit)) + '\n'
                  for circuit in instance_data['circuits'])


def main(rotation: bool = False):
    # Solve SAT problem for each instance
    for instance_file in glob.glob(pt.join(DEFAULT_INSTANCES_DIR, '*')):
        with open(instance_file) as fin:
            instance_data = json.load(fin)

        print(f'solving instance: {pt.basename(instance_file)}')
        model_results = sat_vlsi(instance_data['width'], instance_data['n'],
                                 instance_data['circuits'])

        # If unsolvable (it should never happen with our instances)
        if model_results is None:
            print('Unsatisfiable instance')
            continue

        # Unpack and decode
        height, variables = model_results

        for var in map(str, variables):
            match = SAT_INSTANCE_DECODER_RE.match(var)
            x, y, k = map(int, match.groups())

            # Update instance data with results
            instance_data['circuits'][k] = (instance_data['circuits'][k]
                                            + [x, y])

        # Dump results and statistics on file
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        output_basename = (f'out-{pt.splitext(pt.basename(instance_file))[0]}'
                           '.txt')
        stats_basename = (f'stats-{pt.splitext(pt.basename(instance_file))[0]}'
                          '.txt')
        with open(pt.join(DEFAULT_OUTPUT_DIR, output_basename), 'w') as fout:
            dump_result(instance_data, height, fout)

        # with open(pt.join(DEFAULT_OUTPUT_DIR, stats_basename), 'w') as fout:
        #     dump_statistics(result.statistics, result.status, fout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convenience script for model execution. Execute the SAT '
                    'model on all given instances.')
    parser.add_argument('-r', '--rotation', dest='rotation',
                        action='store_true', default=False,
                        help='if specified, the rotation aware model will be '
                             'used')
    args = parser.parse_args()
    # Imposing rotations currently have no effect, but can be used
    # later on to determine which model to use
    main(args.rotation)
