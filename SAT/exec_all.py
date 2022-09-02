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


from SAT_model import linear_optimization as sat_vlsi
from SAT_model_rotations import sat_vlsi as sat_vlsi_rot
from SAT_model_order import binary_optimization as sat_vlsi_ord


# Path to json input instances, converted using convert_instances.py
DEFAULT_INSTANCES_DIR = pt.join(pt.dirname(__file__), '..', 'instances_json')
DEFAULT_OUTPUT_DIR = pt.join(pt.dirname(__file__), 'out')

SAT_INSTANCE_DECODER_RE = re.compile(r'x_([0-9]+)_([0-9]+)_([0-9]+)')

def dump_result(instance_data, height, fp=sys.stdout):
    """Format result and dump it."""
    fp.write(f'{instance_data["width"]} {height}\n{instance_data["n"]}\n')
    fp.writelines(' '.join(map(str, circuit)) + '\n'
                  for circuit in instance_data['circuits'])


def dump_statistics(statistics, build_time, fp=sys.stdout):
    """Format statistics and dump it (json)."""
    statistics_dict = {}

    for key in statistics.keys():
        statistics_dict[key] = statistics.get_key_value(key)

    statistics_dict['build_time'] = build_time

    json.dump(statistics_dict, fp, indent=4)
    

def main(solve_func):
    # Solve SAT problem for each instance
    for instance_file in sorted(
            glob.glob(pt.join(DEFAULT_INSTANCES_DIR, '*'))):
        with open(instance_file) as fin:
            instance_data = json.load(fin)

        print(f'solving instance: {pt.basename(instance_file)}')
        model_results = solve_func(instance_data['width'], instance_data['n'],
                                   instance_data['circuits'],
                                   instance_data['max_height'])

        # If unsolvable (it should never happen with our instances)
        if model_results is None:
            print('Unsatisfiable instance')
            continue

        # Unpack and decode
        height, variables, statistics, build_time = model_results

        for var in map(str, variables):
            match = SAT_INSTANCE_DECODER_RE.match(var)
            x, y, k = map(int, match.groups())

            # Normalize k (from index k to 2k - 1 it's the kth
            # rectangle, rotated)
            if k >= instance_data['n']:
                k -= instance_data['n']

            w, h = instance_data['circuits'][k]
            if k >= instance_data['n']:
                w, h = h, w

            # Update instance data with results
            instance_data['circuits'][k] = (w, h, x, y)

        # Output results and statistics
        dump_result(instance_data, height)
        print(statistics)

        # Dump results and statistics on file
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        output_basename = (f'out-{pt.splitext(pt.basename(instance_file))[0]}'
                           '.txt')
        stats_basename = (f'stats-{pt.splitext(pt.basename(instance_file))[0]}'
                          '.json')
        with open(pt.join(DEFAULT_OUTPUT_DIR, output_basename), 'w') as fout:
            dump_result(instance_data, height, fout)

        with open(pt.join(DEFAULT_OUTPUT_DIR, stats_basename), 'w') as fout:
            dump_statistics(statistics, build_time, fout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convenience script for model execution. Execute the SAT '
                    'model on all given instances.')
    parser.add_argument('-r', '--rotation', dest='rotation',
                        action='store_true', default=False,
                        help='if specified, the rotation aware model will be '
                             'used')
    parser.add_argument('-o', '--order', dest='order', action='store_true',
                        default=False,
                        help='if specified, use the order encodings model '
                             '(huge performance boost)')
    args = parser.parse_args()

    solve_func = sat_vlsi
    if args.rotation and args.order:
        raise NotImplementedError('rotation order model not implemented')
    elif args.order:
        solve_func = sat_vlsi_ord
    elif args.rotation:
        solve_func = sat_vlsi_rot
    main(solve_func)
