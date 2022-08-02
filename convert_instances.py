"""Convert a directory of instances into json format.

Python >= 3.8.
"""
import os
import os.path as pt
import sys
import glob
import json


def main(dirname: str):
    # Build new directory
    newdirname = f'{dirname}_json'
    os.makedirs(newdirname, exist_ok=True)

    # Build new instance files
    for instance in glob.glob(pt.join(dirname, '*')):
        # Build corresponding dictionary
        with open(instance) as fin:
            instance_lines = fin.read().splitlines()

        width = int(instance_lines[0])
        n = int(instance_lines[1])
        instance_lines = instance_lines[2:]
        circuits = list(map(lambda x: [int(s) for s in x.strip().split(' ')],
                            instance_lines))
        instance_dict = {
            'width': width,
            'n': n,
            'circuits': circuits
        }

        # Write new file
        newinstancename = f'{pt.basename(pt.splitext(instance)[0])}.json'
        with open(pt.join(newdirname, newinstancename), 'w') as fout:
            json.dump(instance_dict, fout)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Please provide a directory', file=sys.stderr)
        sys.exit()

    filename = sys.argv[1]
    main(filename)
