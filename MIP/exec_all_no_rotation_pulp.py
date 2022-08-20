import sys
import glob
import json
import os
import os.path as pt

from MIP_no_rotation_pulp import solve

DEFAULT_INSTANCES_DIR = pt.join(pt.dirname(__file__), '..', 'instances_json')
DEFAULT_OUTPUT_DIR = pt.join(pt.dirname(__file__), 'out_no_rotation_pulp')

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
    for instance_file in glob.glob(pt.join(DEFAULT_INSTANCES_DIR, '*01*')):
        with open(instance_file) as fin:
            instance_data = json.load(fin)

        print(f'solving instance: {pt.basename(instance_file)}')
        result = solve(**instance_data, export_file="no_rotation_pulp.mps")

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
    main()